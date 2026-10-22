"""แปลงไฟล์ที่ผู้ใช้อัปโหลดเป็นไฟล์ DuckDB (ใช้โดย routers/datasets.py)

ทุกนามสกุลจะถูกอ่านเป็น DataFrame ก่อน แล้วผ่านโค้ดทำความสะอาดชื่อตาราง/คอลัมน์และเขียนลง DuckDB
ชุดเดียวกัน — agent ไม่เคยแตะไฟล์ต้นฉบับ อ่านเฉพาะไฟล์ .duckdb ที่ได้จากที่นี่

รองรับ: .csv .tsv .xlsx .xls .ods .json .jsonl .parquet
1 ไฟล์ = 1 ตาราง ยกเว้นไฟล์ spreadsheet (.xlsx .xls .ods) ที่ 1 sheet = 1 ตาราง

หมายเหตุ: ไฟล์นี้เรียก read_json / read_parquet ของ DuckDB ได้ เพราะเป็นโค้ดของเราเอง
ส่วน SQL ที่ LLM เขียนยังถูก sql_guard บล็อกฟังก์ชันพวกนี้เหมือนเดิม
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

MAX_BYTES = 10 * 1024 * 1024
MAX_TABLES = 20
MAX_COLUMNS = 200

SPREADSHEET_SUFFIXES = {".xlsx", ".xls", ".ods"}
SUPPORTED_SUFFIXES = {".csv", ".tsv", ".json", ".jsonl", ".parquet"} | SPREADSHEET_SUFFIXES

# ลำดับการเดา encoding ของไฟล์ข้อความภาษาไทย (cp874 = Excel ภาษาไทยรุ่นเก่า)
_TEXT_ENCODINGS = ("utf-8-sig", "cp874", "tis-620")

_ENGINES = {".xlsx": "openpyxl", ".xls": "xlrd", ".ods": "odf"}


class IngestError(ValueError):
    """ไฟล์ใช้ไม่ได้ ข้อความแสดงให้ผู้ใช้เห็นได้"""


@dataclass(frozen=True)
class TableInfo:
    name: str
    rows: int
    columns: list[str]


# ---------- ชื่อตาราง/คอลัมน์ ----------

_UNSAFE = re.compile(r"[^\w฀-๿]+", flags=re.UNICODE)


def clean_name(raw: object, fallback: str) -> str:
    """เก็บตัวอักษรไทย อังกฤษ ตัวเลข และ _ ที่เหลือเปลี่ยนเป็น _"""
    text = "" if raw is None or (isinstance(raw, float) and pd.isna(raw)) else str(raw)
    text = _UNSAFE.sub("_", text.strip()).strip("_")
    if not text or text.lower().startswith("unnamed"):
        text = fallback
    if text[0].isdigit():
        text = f"_{text}"
    return text[:63]


def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for n in names:
        key = n.lower()
        if key in seen:
            seen[key] += 1
            n = f"{n}_{seen[key]}"
        else:
            seen[key] = 1
        out.append(n)
    return out


def _clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.shape[1] == 0:
        raise IngestError("ไม่พบคอลัมน์ในไฟล์")
    if df.shape[1] > MAX_COLUMNS:
        raise IngestError(f"คอลัมน์เกิน {MAX_COLUMNS}")
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = _dedupe([clean_name(c, f"column_{i + 1}") for i, c in enumerate(df.columns)])
    return df


# ---------- ตัวอ่านแต่ละนามสกุล ----------

def _read_text_table(path: Path, sep: str) -> pd.DataFrame:
    last: Exception | None = None
    for enc in _TEXT_ENCODINGS:
        try:
            return pd.read_csv(path, sep=sep, encoding=enc)
        except UnicodeDecodeError as e:
            last = e
        except pd.errors.ParserError as e:
            raise IngestError(f"อ่านไฟล์ไม่ได้: {e}") from e
    raise IngestError("อ่านภาษาของไฟล์ไม่ได้ ลองบันทึกเป็น CSV UTF-8") from last


def _read_spreadsheet(path: Path) -> dict[str, pd.DataFrame]:
    try:
        sheets = pd.read_excel(path, sheet_name=None, engine=_ENGINES[path.suffix.lower()])
    except Exception as e:  # ไฟล์เสีย หรือนามสกุลไม่ตรงเนื้อไฟล์
        raise IngestError(f"เปิดไฟล์ spreadsheet ไม่ได้: {e}") from e
    return {name: df for name, df in sheets.items() if not df.dropna(how="all").empty}


def _read_with_duckdb(path: Path, reader: str) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        return con.execute(f"SELECT * FROM {reader}(?)", [str(path)]).df()
    except duckdb.Error as e:
        raise IngestError(f"อ่านไฟล์ไม่ได้: {e}") from e
    finally:
        con.close()


def _flatten_nested(df: pd.DataFrame) -> pd.DataFrame:
    """JSON ซ้อน 1 ชั้น ({"a": {"b": 1}}) → คอลัมน์ a_b · ซ้อนลึกกว่านั้นเก็บเป็นข้อความ"""
    for col in list(df.columns):
        if df[col].map(lambda v: isinstance(v, dict)).any():
            expanded = pd.json_normalize(df[col].map(lambda v: v if isinstance(v, dict) else {}).tolist())
            expanded.columns = [f"{col}_{c}" for c in expanded.columns]
            df = pd.concat([df.drop(columns=[col]), expanded], axis=1)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].map(lambda v: str(v) if isinstance(v, (list, dict)) else v)
    return df


def read_tables(path: Path) -> dict[str, pd.DataFrame]:
    """อ่านไฟล์ คืน {ชื่อตารางดิบ: DataFrame}"""
    suffix = path.suffix.lower()
    stem = path.stem
    if suffix == ".csv":
        return {stem: _read_text_table(path, ",")}
    if suffix == ".tsv":
        return {stem: _read_text_table(path, "\t")}
    if suffix in SPREADSHEET_SUFFIXES:
        return _read_spreadsheet(path)
    if suffix == ".parquet":
        return {stem: _read_with_duckdb(path, "read_parquet")}
    if suffix in {".json", ".jsonl"}:
        try:
            df = pd.read_json(path, lines=(suffix == ".jsonl"), dtype=False)
        except ValueError as e:
            raise IngestError("JSON ต้องเป็นรายการของ object เช่น [{\"a\": 1}, {\"a\": 2}]") from e
        return {stem: _flatten_nested(df)}
    raise IngestError(f"ยังไม่รองรับไฟล์ {suffix} (รองรับ: {', '.join(sorted(SUPPORTED_SUFFIXES))})")


# ---------- จุดเข้าใช้งาน ----------

def ingest(src: Path, dest: Path) -> list[TableInfo]:
    """แปลง src เป็นไฟล์ DuckDB ที่ dest (เขียนทับถ้ามี) คืนรายการตารางที่สร้าง"""
    if src.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise IngestError(f"ยังไม่รองรับไฟล์ {src.suffix} (รองรับ: {', '.join(sorted(SUPPORTED_SUFFIXES))})")
    size = src.stat().st_size
    if size == 0:
        raise IngestError("ไฟล์ว่างเปล่า")
    if size > MAX_BYTES:
        raise IngestError(f"ไฟล์ใหญ่เกิน {MAX_BYTES // (1024 * 1024)} MB")

    raw_tables = read_tables(src)
    if not raw_tables:
        raise IngestError("ไม่พบข้อมูลในไฟล์")
    if len(raw_tables) > MAX_TABLES:
        raise IngestError(f"มีตารางเกิน {MAX_TABLES} ตาราง")

    names = _dedupe([clean_name(n, f"table_{i + 1}") for i, n in enumerate(raw_tables)])

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.duckdb")
    tmp.unlink(missing_ok=True)
    con = duckdb.connect(str(tmp))
    infos: list[TableInfo] = []
    try:
        for name, df in zip(names, raw_tables.values()):
            df = _clean_frame(df)
            con.register("_src", df)
            con.execute(f'CREATE TABLE "{name}" AS SELECT * FROM _src')
            con.unregister("_src")
            infos.append(TableInfo(name=name, rows=len(df), columns=list(df.columns)))
    except IngestError:
        con.close()
        tmp.unlink(missing_ok=True)
        raise
    con.close()
    tmp.replace(dest)  # เขียนเสร็จทั้งไฟล์แล้วค่อยย้าย agent จะไม่เห็นไฟล์ครึ่ง ๆ กลาง ๆ
    return infos

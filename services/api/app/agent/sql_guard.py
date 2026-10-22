"""ตัวตรวจ SQL ก่อนรันจริง

หลักการ: โค้ดเป็นคนตัดสินว่า SQL ปลอดภัยหรือไม่ ไม่ใช่ LLM
- อนุญาตเฉพาะคำสั่งอ่านข้อมูล (SELECT / WITH ... SELECT / UNION)
- คำสั่งเดียวต่อครั้ง
- ห้ามฟังก์ชันที่อ่านไฟล์หรือเครือข่าย (read_csv, read_parquet, glob, ...)
- เติม LIMIT ให้ถ้าไม่มี
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DIALECT = "duckdb"
DEFAULT_LIMIT = 200

# ชนิด node ที่ห้ามปรากฏที่ใดก็ตามใน SQL
_FORBIDDEN_NODES: tuple[type[exp.Expression], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,  # ATTACH, COPY, INSTALL, LOAD, PRAGMA, SET ... มักแปลงเป็น Command
    exp.Copy,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Use,
    exp.Pragma,
    exp.Set,
    exp.Into,  # SELECT ... INTO
)

# ฟังก์ชันที่อ่านไฟล์ ระบบ หรือเครือข่าย (เทียบแบบตัวพิมพ์เล็ก)
_FORBIDDEN_FUNCTIONS = {
    "read_csv",
    "read_csv_auto",
    "read_parquet",
    "parquet_scan",
    "read_json",
    "read_json_auto",
    "read_json_objects",
    "read_ndjson",
    "read_text",
    "read_blob",
    "read_xlsx",
    "st_read",
    "glob",
    "sniff_csv",
    "iceberg_scan",
    "delta_scan",
    "sqlite_scan",
    "postgres_scan",
    "mysql_scan",
    "httpfs",
    "getenv",
    "current_setting",
    "duckdb_settings",
    "duckdb_secrets",
    "duckdb_extensions",
    "query",
    "query_table",
}


class SqlRejected(ValueError):
    """SQL ไม่ผ่านการตรวจ ข้อความใช้ส่งกลับให้ agent แก้ได้"""


@dataclass(frozen=True)
class CheckedSql:
    sql: str
    limit_added: bool


def _function_name(node: exp.Expression) -> str | None:
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    if isinstance(node, exp.Func):
        return node.sql_name().lower()
    return None


_PATH_CHARS = ("/", "\\", ":", "*", "?")
_FILE_SUFFIXES = (".csv", ".tsv", ".parquet", ".json", ".ndjson", ".xlsx", ".txt", ".db", ".duckdb", ".sqlite", ".gz")


def _looks_like_path(name: str) -> bool:
    lowered = name.lower()
    return any(c in name for c in _PATH_CHARS) or lowered.endswith(_FILE_SUFFIXES)


def check_sql(
    sql: str,
    *,
    max_rows: int = DEFAULT_LIMIT,
    allowed_tables: set[str] | None = None,
) -> CheckedSql:
    """ตรวจและปรับ SQL ให้ปลอดภัย ผ่านแล้วคืน SQL ที่พร้อมรัน ไม่ผ่านจะ raise SqlRejected

    allowed_tables: ถ้าส่งมา ทุกตารางที่อ้างถึง (ยกเว้นชื่อ CTE) ต้องอยู่ในชุดนี้
    ควรส่งเสมอตอนรันจริง — sqlglot แยก FROM 'file.csv' ออกจาก FROM "table" ไม่ได้
    """
    if not sql or not sql.strip():
        raise SqlRejected("SQL ว่างเปล่า")

    try:
        statements = [s for s in sqlglot.parse(sql, read=DIALECT) if s is not None]
    except ParseError as e:
        raise SqlRejected(f"อ่าน SQL ไม่ได้: {e}") from e

    if len(statements) != 1:
        raise SqlRejected("อนุญาตให้รันได้ครั้งละ 1 คำสั่งเท่านั้น")

    tree = statements[0]

    if not isinstance(tree, exp.Query):
        raise SqlRejected("อนุญาตเฉพาะคำสั่งอ่านข้อมูล (SELECT)")

    cte_names = {cte.alias_or_name for cte in tree.find_all(exp.CTE)}

    for node in tree.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            raise SqlRejected(f"ไม่อนุญาตคำสั่ง {node.key.upper()}")
        name = _function_name(node)
        if name and name in _FORBIDDEN_FUNCTIONS:
            raise SqlRejected(f"ไม่อนุญาตฟังก์ชัน {name}")
        if isinstance(node, exp.Table) and node.name:
            # FROM 'file.csv' — DuckDB อ่านไฟล์จากชื่อที่เป็นข้อความได้
            if _looks_like_path(node.name) or node.args.get("db") or node.args.get("catalog"):
                raise SqlRejected(f"ไม่อนุญาตให้อ่านไฟล์หรือฐานข้อมูลอื่น: {node.name}")
            if allowed_tables is not None and node.name not in allowed_tables and node.name not in cte_names:
                raise SqlRejected(f"ไม่มีตาราง {node.name} (มี: {', '.join(sorted(allowed_tables))})")

    limit_added = False
    if tree.args.get("limit") is None:
        tree = tree.limit(max_rows)
        limit_added = True

    return CheckedSql(sql=tree.sql(dialect=DIALECT), limit_added=limit_added)

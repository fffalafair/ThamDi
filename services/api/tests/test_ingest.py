import json

import duckdb
import pandas as pd
import pytest

from app.ingest import IngestError, clean_name, ingest

ROWS = pd.DataFrame(
    {
        "จังหวัด": ["กรุงเทพมหานคร", "เชียงใหม่", "ภูเก็ต"],
        "ยอดขาย": [100, 200, 300],
        "order date": ["2024-10-01", "2024-11-01", "2024-12-01"],
    }
)


def tables_of(db):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return {t: con.execute(f'SELECT * FROM "{t}"').fetchall() for (t,) in con.execute("SHOW TABLES").fetchall()}
    finally:
        con.close()


def test_csv_utf8(tmp_path):
    src = tmp_path / "sales.csv"
    ROWS.to_csv(src, index=False, encoding="utf-8-sig")
    info = ingest(src, tmp_path / "out.duckdb")
    assert info[0].name == "sales"
    assert info[0].columns == ["จังหวัด", "ยอดขาย", "order_date"]
    assert len(tables_of(tmp_path / "out.duckdb")["sales"]) == 3


def test_csv_thai_legacy_encoding(tmp_path):
    src = tmp_path / "legacy.csv"
    ROWS.to_csv(src, index=False, encoding="cp874")
    info = ingest(src, tmp_path / "out.duckdb")
    rows = tables_of(tmp_path / "out.duckdb")[info[0].name]
    assert rows[0][0] == "กรุงเทพมหานคร"


def test_tsv(tmp_path):
    src = tmp_path / "t.tsv"
    ROWS.to_csv(src, index=False, sep="\t")
    assert ingest(src, tmp_path / "out.duckdb")[0].rows == 3


def test_xlsx_multiple_sheets(tmp_path):
    src = tmp_path / "book.xlsx"
    with pd.ExcelWriter(src, engine="openpyxl") as w:
        ROWS.to_excel(w, sheet_name="ยอดขาย", index=False)
        ROWS.head(1).to_excel(w, sheet_name="Sheet 2", index=False)
    names = {t.name for t in ingest(src, tmp_path / "out.duckdb")}
    assert names == {"ยอดขาย", "Sheet_2"}


def test_ods(tmp_path):
    src = tmp_path / "book.ods"
    ROWS.to_excel(src, engine="odf", index=False)
    assert ingest(src, tmp_path / "out.duckdb")[0].rows == 3


def test_json_array_with_nested_object(tmp_path):
    src = tmp_path / "data.json"
    src.write_text(
        json.dumps([{"id": 1, "addr": {"province": "ภูเก็ต"}}, {"id": 2, "addr": {"province": "สงขลา"}}], ensure_ascii=False),
        encoding="utf-8",
    )
    info = ingest(src, tmp_path / "out.duckdb")
    assert "addr_province" in info[0].columns


def test_jsonl(tmp_path):
    src = tmp_path / "data.jsonl"
    src.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in ROWS.to_dict("records")), encoding="utf-8")
    assert ingest(src, tmp_path / "out.duckdb")[0].rows == 3


def test_parquet(tmp_path):
    src = tmp_path / "data.parquet"
    con = duckdb.connect()
    con.register("df", ROWS)
    con.execute(f"COPY df TO '{src}' (FORMAT parquet)")
    con.close()
    assert ingest(src, tmp_path / "out.duckdb")[0].rows == 3


def test_duplicate_and_blank_headers(tmp_path):
    src = tmp_path / "messy.csv"
    src.write_text("ชื่อ,ชื่อ,,1st\nก,ข,ค,ง\n", encoding="utf-8")
    cols = ingest(src, tmp_path / "out.duckdb")[0].columns
    assert cols == ["ชื่อ", "ชื่อ_1", "column_3", "_1st"]


@pytest.mark.parametrize("name", ["virus.exe", "doc.pdf", "notes.docx", "db.sqlite"])
def test_rejects_unsupported(tmp_path, name):
    src = tmp_path / name
    src.write_bytes(b"x")
    with pytest.raises(IngestError):
        ingest(src, tmp_path / "out.duckdb")


def test_rejects_empty_file(tmp_path):
    src = tmp_path / "empty.csv"
    src.write_bytes(b"")
    with pytest.raises(IngestError):
        ingest(src, tmp_path / "out.duckdb")


def test_rejects_fake_xlsx(tmp_path):
    src = tmp_path / "fake.xlsx"
    src.write_text("not really excel")
    with pytest.raises(IngestError):
        ingest(src, tmp_path / "out.duckdb")


def test_failed_ingest_leaves_no_file(tmp_path):
    src = tmp_path / "fake.xlsx"
    src.write_text("not really excel")
    dest = tmp_path / "out.duckdb"
    with pytest.raises(IngestError):
        ingest(src, dest)
    assert not dest.exists()


@pytest.mark.parametrize("raw,expected", [("ยอด ขาย", "ยอด_ขาย"), ("a-b/c", "a_b_c"), ("", "fb"), ("Unnamed: 0", "fb"), ("2024", "_2024")])
def test_clean_name(raw, expected):
    assert clean_name(raw, "fb") == expected

"""เครื่องมือที่ agent เรียกได้ (คนที่ 1)

TODO วันที่ 25–27 ต.ค.: ทำให้ครบทุกตัว
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from app.agent.sql_guard import check_sql
from app.config import settings


def dataset_path(dataset_id: str) -> Path:
    # ตามสัญญาใน docs/CONTRACT.md
    return Path(settings.data_dir) / "datasets" / f"{dataset_id}.duckdb"


def connect(dataset_id: str) -> duckdb.DuckDBPyConnection:
    """เปิดแบบ read-only และปิดการเข้าถึงไฟล์ภายนอก"""
    con = duckdb.connect(str(dataset_path(dataset_id)), read_only=True)
    con.execute("SET enable_external_access = false")
    return con


def list_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall()]


def describe_table(con: duckdb.DuckDBPyConnection, name: str, sample: int = 3) -> dict:
    if name not in list_tables(con):
        raise ValueError(f"ไม่มีตาราง {name}")
    cols = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position",
        [name],
    ).fetchall()
    rows = con.execute(f'SELECT * FROM "{name}" LIMIT {int(sample)}').fetchall()
    return {"table": name, "columns": [{"name": c, "type": t} for c, t in cols], "sample": rows}


def find_values(con: duckdb.DuckDBPyConnection, table: str, column: str, keyword: str, k: int = 5) -> list[str]:
    """TODO: หาค่าที่ใกล้เคียง เช่น 'กทม' → 'กรุงเทพมหานคร'
    เริ่มจาก ILIKE แล้วค่อยเพิ่ม jaro_winkler_similarity / ตารางคำพ้อง
    """
    raise NotImplementedError


def run_sql(con: duckdb.DuckDBPyConnection, sql: str) -> dict:
    checked = check_sql(sql, allowed_tables=set(list_tables(con)))
    cur = con.execute(checked.sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return {"sql": checked.sql, "columns": columns, "rows": rows, "limit_added": checked.limit_added}

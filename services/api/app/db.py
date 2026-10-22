"""เชื่อมต่อ Postgres (P2) — ใช้ psycopg ตรง ๆ ไม่มี ORM

ทุก query ต้องใช้ parameter (%s) ห้ามต่อ string
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.config import settings

MODELS_SQL = Path(__file__).with_name("models.sql")


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """เปิด connection ที่คืนแถวเป็น dict · commit เมื่อจบ block, rollback เมื่อ error"""
    with psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def init_db() -> None:
    """สร้างตารางทั้งหมดถ้ายังไม่มี (รันซ้ำได้)"""
    with connect() as conn:
        conn.execute(MODELS_SQL.read_text(encoding="utf-8"))

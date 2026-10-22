"""ตาราง Postgres (P2-02) — ข้ามถ้าต่อ Postgres ไม่ได้ (เช่นรัน pytest บนเครื่องที่ไม่ได้เปิด docker)"""

import psycopg
import pytest

from app.config import settings
from app.db import connect, init_db

try:
    psycopg.connect(settings.database_url, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("ต่อ Postgres ไม่ได้", allow_module_level=True)


def _tables() -> set[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ).fetchall()
    return {r["table_name"] for r in rows}


def test_init_db_creates_tables():
    init_db()
    assert {"users", "datasets", "chat_history"} <= _tables()


def test_init_db_is_idempotent():
    init_db()
    init_db()
    assert {"users", "datasets", "chat_history"} <= _tables()


def test_deleting_user_cascades():
    init_db()
    with connect() as conn:
        uid = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
            ("cascade-test@example.com", "x"),
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO datasets (id, user_id, name) VALUES (%s, %s, %s)",
            ("ds_cascadetest", uid, "a.csv"),
        )
        conn.execute(
            "INSERT INTO chat_history (user_id, dataset_id, question, response) VALUES (%s, %s, %s, %s)",
            (uid, "ds_cascadetest", "q", "{}"),
        )
        expires = conn.execute(
            "SELECT expires_at - created_at AS ttl FROM datasets WHERE id = %s", ("ds_cascadetest",)
        ).fetchone()["ttl"]
        conn.execute("DELETE FROM users WHERE id = %s", (uid,))
        left = conn.execute("SELECT count(*) AS n FROM chat_history WHERE dataset_id = %s", ("ds_cascadetest",))
        assert left.fetchone()["n"] == 0
        assert conn.execute("SELECT 1 FROM datasets WHERE id = %s", ("ds_cascadetest",)).fetchone() is None
    assert expires.days == 7

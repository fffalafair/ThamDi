import pytest

from app.agent.sql_guard import SqlRejected, check_sql

ALLOWED = [
    "SELECT 1",
    "SELECT * FROM orders",
    "SELECT province, SUM(total) FROM orders o JOIN branches b ON b.id = o.branch_id GROUP BY 1",
    "WITH t AS (SELECT * FROM orders) SELECT COUNT(*) FROM t",
    "SELECT name FROM products UNION SELECT name FROM customers",
    'SELECT "ยอดขาย" FROM "ยอดขายรายเดือน" WHERE "จังหวัด" = \'กรุงเทพมหานคร\'',
    "SELECT * FROM orders WHERE order_date BETWEEN '2024-10-01' AND '2025-09-30'",
]

REJECTED = [
    "",
    "   ",
    "DROP TABLE orders",
    "DELETE FROM orders",
    "UPDATE orders SET total = 0",
    "INSERT INTO orders VALUES (1)",
    "CREATE TABLE x AS SELECT 1",
    "ALTER TABLE orders ADD COLUMN x INT",
    "SELECT 1; DROP TABLE orders",
    "SELECT 1; SELECT 2",
    "ATTACH 'other.duckdb' AS other",
    "COPY orders TO 'out.csv'",
    "INSTALL httpfs",
    "LOAD httpfs",
    "PRAGMA database_list",
    "SET enable_external_access = true",
    "SELECT * FROM read_csv('/etc/passwd')",
    "SELECT * FROM read_csv_auto('secret.csv')",
    "SELECT * FROM read_parquet('s3://bucket/x.parquet')",
    "SELECT * FROM glob('/data/*')",
    "SELECT * FROM '/etc/passwd'",
    "SELECT getenv('GROQ_API_KEY')",
    "SELECT * FROM (SELECT * FROM read_json('x.json'))",
    "WITH t AS (SELECT * FROM read_text('/etc/hosts')) SELECT * FROM t",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allows_read_only(sql):
    assert check_sql(sql).sql


@pytest.mark.parametrize("sql", REJECTED)
def test_rejects_dangerous(sql):
    with pytest.raises(SqlRejected):
        check_sql(sql)


TABLES = {"orders", "branches", "products", "customers"}


def test_allowlist_accepts_known_tables_and_ctes():
    check_sql("WITH t AS (SELECT * FROM orders) SELECT * FROM t JOIN branches b ON true", allowed_tables=TABLES)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM secrets",
        'SELECT * FROM "x"',
        "SELECT * FROM other.orders",
        "SELECT * FROM 'data'",  # ไฟล์ไม่มีนามสกุล — จับได้ด้วย allowlist เท่านั้น
    ],
)
def test_allowlist_rejects_unknown_tables(sql):
    with pytest.raises(SqlRejected):
        check_sql(sql, allowed_tables=TABLES)


def test_adds_limit_when_missing():
    out = check_sql("SELECT * FROM orders", max_rows=50)
    assert out.limit_added
    assert "LIMIT 50" in out.sql


def test_keeps_existing_limit():
    out = check_sql("SELECT * FROM orders LIMIT 5")
    assert not out.limit_added
    assert "LIMIT 5" in out.sql

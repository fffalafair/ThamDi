"""สมัคร / login / current_user (P2-03) — ข้ามถ้าต่อ Postgres ไม่ได้"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import psycopg
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import init_db
from app.main import app
from app.routers import auth

try:
    psycopg.connect(settings.database_url, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("ต่อ Postgres ไม่ได้", allow_module_level=True)

client = TestClient(app)
PASSWORD = "correct-horse-1"


@pytest.fixture(autouse=True)
def _setup():
    init_db()
    auth._attempts.clear()


def _email() -> str:
    return f"user-{uuid4().hex[:10]}@example.com"


def _register(email: str, password: str = PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def _me(token: str):
    return client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})


def test_register_returns_working_token():
    email = _email()
    r = _register(email)
    assert r.status_code == 201
    me = _me(r.json()["access_token"])
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_register_duplicate_email_409_case_insensitive():
    email = _email()
    assert _register(email).status_code == 201
    r = _register(email.upper())
    assert r.status_code == 409


@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "password": PASSWORD},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "ก" * 30},  # 90 byte เกินที่ bcrypt รับ
    ],
)
def test_register_rejects_invalid_input(body):
    assert client.post("/api/auth/register", json=body).status_code == 422


def test_password_is_not_stored_plain():
    from app.db import connect

    email = _email()
    _register(email)
    with connect() as conn:
        h = conn.execute("SELECT password_hash FROM users WHERE email = %s", (email,)).fetchone()["password_hash"]
    assert PASSWORD not in h
    assert h.startswith("$2b$10$")


def test_login_success():
    email = _email()
    _register(email)
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200
    assert _me(r.json()["access_token"]).status_code == 200


def test_login_wrong_password_and_unknown_email_look_the_same():
    email = _email()
    _register(email)
    wrong = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    unknown = client.post("/api/auth/login", json={"email": _email(), "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_rate_limited_per_email():
    email = _email()
    _register(email)
    for _ in range(auth.LOGIN_LIMIT):
        assert client.post("/api/auth/login", json={"email": email, "password": "wrong"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 429
    # อีเมลอื่นยังเข้าได้ (นับต่ออีเมล ไม่ใช่ต่อ IP)
    other = _email()
    _register(other)
    assert client.post("/api/auth/login", json={"email": other, "password": PASSWORD}).status_code == 200


def test_successful_logins_do_not_count_and_reset_failures():
    email = _email()
    _register(email)
    for _ in range(auth.LOGIN_LIMIT - 1):
        client.post("/api/auth/login", json={"email": email, "password": "wrong"})
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    # สำเร็จแล้วล้างตัวนับ: login ถูกซ้ำ ๆ เกิน limit ก็ไม่โดน 429
    for _ in range(auth.LOGIN_LIMIT + 2):
        assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200


def test_login_rejects_password_over_72_bytes():
    r = client.post("/api/auth/login", json={"email": _email(), "password": "ก" * 30})
    assert r.status_code == 422


@pytest.mark.parametrize("secret,origins,should_fail", [
    ("change-me", "http://localhost:3000", False),
    ("change-me", "https://thamdi.example.com", True),
    ("short", "https://thamdi.example.com", True),
    ("x" * 48, "https://thamdi.example.com", False),
])
def test_check_jwt_secret(monkeypatch, secret, origins, should_fail):
    from app.security import check_jwt_secret

    monkeypatch.setattr(settings, "jwt_secret", secret)
    monkeypatch.setattr(settings, "cors_origins", origins)
    if should_fail:
        with pytest.raises(RuntimeError):
            check_jwt_secret()
    else:
        check_jwt_secret()


def test_demo_user_can_login():
    auth.ensure_demo_user()
    auth.ensure_demo_user()  # รันซ้ำได้
    r = client.post("/api/auth/login", json={"email": settings.demo_email, "password": settings.demo_password})
    assert r.status_code == 200


def test_me_without_token_401():
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("make_token", [
    lambda uid: "not-a-jwt",
    lambda uid: jwt.encode({"sub": uid, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "wrong-secret"),
    lambda uid: jwt.encode({"sub": uid, "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, settings.jwt_secret),
    lambda uid: jwt.encode({"sub": uid}, settings.jwt_secret),  # ไม่มี exp
    lambda uid: jwt.encode({"sub": uid, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, None,
                           algorithm="none"),
    lambda uid: jwt.encode({"sub": str(uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                           settings.jwt_secret),  # user ไม่มีจริง
    lambda uid: jwt.encode({"sub": "not-a-uuid", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                           settings.jwt_secret),
], ids=["garbage", "wrong-secret", "expired", "no-exp", "alg-none", "unknown-user", "bad-sub"])
def test_me_rejects_bad_tokens(make_token):
    email = _email()
    token = _register(email).json()["access_token"]
    uid = _me(token).json()["id"]
    assert _me(make_token(uid)).status_code == 401

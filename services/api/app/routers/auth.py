"""การสมัครและ login (P2)

- bcrypt (cost 10) สำหรับรหัสผ่าน
- JWT ใน Authorization: Bearer <token> อายุ 24 ชม.
- rate limit login ผิด 10 ครั้ง/นาที ต่ออีเมล (ไม่ใช่ต่อ IP เพราะทั้งห้องใช้ wifi เดียวกันตอนเดโม)
  นับเฉพาะครั้งที่ผิด login สำเร็จแล้วล้าง จึงไม่ล็อกอาจารย์ที่ login บัญชีเดโมหลายแท็บ
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import settings
from app.db import connect
from app.security import DUMMY_HASH, create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOGIN_LIMIT = 10
LOGIN_WINDOW_S = 60.0
MAX_TRACKED_EMAILS = 10_000  # กัน dict โตไม่หยุดเมื่อมีคนยิงด้วยอีเมลสุ่ม
_attempts: dict[str, deque[float]] = {}
_attempts_lock = Lock()


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def _bcrypt_limit(cls, v: str) -> str:
        # bcrypt ใช้ได้แค่ 72 byte (ภาษาไทย 1 ตัว = 3 byte)
        if len(v.encode()) > 72:
            raise ValueError("รหัสผ่านยาวเกินไป")
        return v


class RegisterBody(Credentials):
    password: str = Field(min_length=8, max_length=72)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    id: UUID
    email: str


def _prune(q: deque[float], now: float) -> None:
    while q and now - q[0] > LOGIN_WINDOW_S:
        q.popleft()


def _check_rate_limit(email: str) -> None:
    now = time.monotonic()
    with _attempts_lock:
        q = _attempts.get(email)
        if q is None:
            return
        _prune(q, now)
        if not q:
            del _attempts[email]
        elif len(q) >= LOGIN_LIMIT:
            raise HTTPException(status_code=429, detail="ลองเข้าสู่ระบบบ่อยเกินไป รอ 1 นาทีแล้วลองใหม่")


def _record_failure(email: str) -> None:
    now = time.monotonic()
    with _attempts_lock:
        if len(_attempts) >= MAX_TRACKED_EMAILS:
            for key in list(_attempts):
                _prune(_attempts[key], now)
                if not _attempts[key]:
                    del _attempts[key]
        _attempts.setdefault(email, deque()).append(now)


def ensure_demo_user() -> None:
    """สร้างบัญชีเดโมให้อาจารย์ลองใช้ ถ้ายังไม่มี"""
    with connect() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING",
            (settings.demo_email.lower(), hash_password(settings.demo_password)),
        )


@router.post("/register", response_model=Token, status_code=201)
def register(body: RegisterBody) -> Token:
    try:
        with connect() as conn:
            row = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (body.email, hash_password(body.password)),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="อีเมลนี้มีบัญชีอยู่แล้ว") from None
    return Token(access_token=create_token(row["id"]))


@router.post("/login", response_model=Token)
def login(body: Credentials) -> Token:
    _check_rate_limit(body.email)
    with connect() as conn:
        user = conn.execute("SELECT id, password_hash FROM users WHERE email = %s", (body.email,)).fetchone()
    # เทียบ hash เสมอแม้ไม่มีอีเมลนี้ ไม่ให้เดาได้จากเวลาตอบว่าอีเมลไหนมีบัญชี
    ok = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)
    if not (user and ok):
        _record_failure(body.email)
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    with _attempts_lock:
        _attempts.pop(body.email, None)
    return Token(access_token=create_token(user["id"]))


@router.get("/me", response_model=User)
def me(user: dict = Depends(current_user)) -> User:
    return User(**user)

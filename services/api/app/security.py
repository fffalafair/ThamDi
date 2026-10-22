"""รหัสผ่าน, JWT และ dependency current_user() (P2)

router อื่นใช้แบบนี้:
    @router.get("/x")
    def x(user: dict = Depends(current_user)): ...   # user = {"id": UUID, "email": str}
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.db import connect

BCRYPT_ROUNDS = 10
JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=24)

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = HTTPException(
    status_code=401, detail="กรุณาเข้าสู่ระบบใหม่", headers={"WWW-Authenticate": "Bearer"}
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# hash ของรหัสสุ่ม ใช้เทียบเมื่อไม่พบอีเมล ให้ login ผิดทั้งสองแบบใช้เวลาเท่ากัน
DUMMY_HASH = hash_password("not-a-real-password")


def check_jwt_secret() -> None:
    """ไม่ยอมเริ่มระบบที่เปิดให้คนนอกใช้ ถ้า JWT_SECRET ยังเป็นค่าตัวอย่าง (repo เป็น public ใครก็ปลอม token ได้)

    ถือว่า "เปิดให้คนนอกใช้" เมื่อ CORS_ORIGINS มีโดเมนที่ไม่ใช่ localhost · บนเครื่องพัฒนาแค่เตือน
    """
    secret = settings.jwt_secret
    if secret not in ("", "change-me") and len(secret.encode()) >= 32:
        return
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    local = ("http://localhost", "http://127.0.0.1")
    if any(not o.startswith(local) for o in origins):
        raise RuntimeError(
            "JWT_SECRET ไม่ปลอดภัย: ตั้งค่าใหม่ใน .env ยาวอย่างน้อย 32 ตัว เช่น "
            'python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    logging.getLogger(__name__).warning("JWT_SECRET ยังเป็นค่าตัวอย่าง ใช้ได้บนเครื่องพัฒนาเท่านั้น")


def create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        raise _UNAUTHORIZED
    try:
        payload = jwt.decode(
            creds.credentials, settings.jwt_secret, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "sub"]}
        )
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise _UNAUTHORIZED from None
    with connect() as conn:
        user = conn.execute("SELECT id, email FROM users WHERE id = %s", (user_id,)).fetchone()
    if user is None:
        raise _UNAUTHORIZED
    return user

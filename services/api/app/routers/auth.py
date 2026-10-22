"""การสมัครและ login (P2) — TODO 23–24 ต.ค.

- bcrypt (cost 10) สำหรับรหัสผ่าน
- JWT ใน Authorization: Bearer <token>
- rate limit login ต่อบัญชี
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=Token, status_code=201)
def register(body: Credentials) -> Token:
    raise HTTPException(status_code=501, detail="TODO: P2")


@router.post("/login", response_model=Token)
def login(body: Credentials) -> Token:
    raise HTTPException(status_code=501, detail="TODO: P2")

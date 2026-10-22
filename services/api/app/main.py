from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, chat, datasets

app = FastAPI(title="ThamDi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mock_agent": settings.use_mock_agent, "demo_mode": settings.demo_mode}

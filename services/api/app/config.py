from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ระบบ
    data_dir: str = "/data"
    database_url: str = "postgresql://app:app@postgres:5432/app"
    jwt_secret: str = "change-me"
    cors_origins: str = "http://localhost:3000"
    demo_email: str = "demo@example.com"
    demo_password: str = "demo1234"

    # agent
    use_mock_agent: bool = True
    demo_mode: bool = False
    llm_timeout_s: float = 30.0

    # LLM
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3-32b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"


settings = Settings()

"""เรียก LLM พร้อมสำรองหลายชั้น

ทุกเจ้าเรียกผ่านไลบรารี openai เปลี่ยนแค่ base_url
ลำดับ: Groq → Gemini → (ล่มหมด) ให้ผู้เรียกสลับไปโหมดพื้นฐาน
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from app.config import settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str


def providers() -> list[Provider]:
    out: list[Provider] = []
    if settings.groq_api_key:
        out.append(Provider("groq", "https://api.groq.com/openai/v1", settings.groq_api_key, settings.groq_model))
    if settings.gemini_api_key:
        out.append(
            Provider(
                "gemini",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
                settings.gemini_api_key,
                settings.gemini_model,
            )
        )
    return out


class AllProvidersFailed(RuntimeError):
    pass


def chat(messages: list[dict], tools: list[dict] | None = None, **kwargs):
    """ลองทีละเจ้าตามลำดับ คืน (response, provider) ของเจ้าแรกที่สำเร็จ"""
    errors: list[str] = []
    for p in providers():
        try:
            client = OpenAI(base_url=p.base_url, api_key=p.api_key, timeout=settings.llm_timeout_s)
            resp = client.chat.completions.create(model=p.model, messages=messages, tools=tools, **kwargs)
            return resp, p
        except OpenAIError as e:  # รวม rate limit, timeout, 5xx
            log.warning("LLM %s ล้มเหลว: %s", p.name, e)
            errors.append(f"{p.name}: {e}")
    raise AllProvidersFailed("; ".join(errors) or "ไม่ได้ตั้งค่า API key")

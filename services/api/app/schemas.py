"""รูปแบบข้อมูลกลาง — ต้องตรงกับ docs/CONTRACT.md

เปลี่ยนไฟล์นี้ = เปลี่ยนสัญญา ต้องแก้ CONTRACT.md และบอกอีกคนทันที
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    dataset_id: str
    question: str = Field(min_length=1, max_length=1000)


class Step(BaseModel):
    tool: str
    status: Literal["ok", "error"]
    args: dict[str, Any] | None = None
    sql: str | None = None
    summary: str | None = None
    detail: str | None = None
    rows: int | None = None
    ms: int | None = None


class Table(BaseModel):
    columns: list[str]
    rows: list[list[Any]]


class Chart(BaseModel):
    type: Literal["bar", "line", "pie"]
    x: str
    y: str


class Meta(BaseModel):
    model: str | None = None
    tokens: int | None = None
    ms: int | None = None
    retries: int = 0


class ChatResponse(BaseModel):
    status: Literal["answered", "clarify", "refused", "error"]
    answer: str
    steps: list[Step] = []
    table: Table | None = None
    chart: Chart | None = None
    meta: Meta = Meta()

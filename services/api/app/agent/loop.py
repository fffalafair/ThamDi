"""agent loop (P1)

TODO ตามแผน:
- 23–24 ต.ค.  ระบบ A: schema + คำถาม → SQL ครั้งเดียว
- 25–27 ต.ค.  tool calling
- 30–31 ต.ค.  ระบบ B (find_values), C (วนแก้ ≤ 3 รอบ), D (วันที่ไทย + ตัวตรวจคำตอบ)

ผลลัพธ์ต้องเป็นรูปแบบเดียวกับ app.schemas.ChatResponse เสมอ
"""

from __future__ import annotations

from app.schemas import ChatRequest, ChatResponse


def answer(req: ChatRequest, *, system: str = "D") -> ChatResponse:
    raise NotImplementedError("ยังใช้ mock อยู่: ตั้ง USE_MOCK_AGENT=true")

"""POST /api/chat (P1)

ตอนนี้ตอบด้วย mock ตามสัญญา เพื่อให้P2 ทำหน้าแชทได้ทันที
ตั้ง USE_MOCK_AGENT=false เมื่อ agent จริงพร้อม (เป้าหมาย 30–31 ต.ค.)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agent import loop
from app.config import settings
from app.schemas import Chart, ChatRequest, ChatResponse, Meta, Step, Table

router = APIRouter(prefix="/api", tags=["chat"])

MOCK_RESPONSE = ChatResponse(
    status="answered",
    answer=(
        "ในปีงบประมาณ 2568 (1 ต.ค. 2567 – 30 ก.ย. 2568) จังหวัดที่ยอดขายสูงสุดคือ "
        "กรุงเทพมหานคร 4,812,350 บาท ตามด้วยชลบุรีและเชียงใหม่"
    ),
    steps=[
        Step(tool="describe_table", status="ok", args={"name": "orders"},
             summary="พบคอลัมน์ order_date, total, branch_id"),
        Step(tool="thai_fiscal_year", status="ok", args={"year": 2568},
             summary="2024-10-01 ถึง 2025-09-30"),
        Step(tool="run_sql", status="error",
             sql="SELECT o.province, SUM(o.total) FROM orders o GROUP BY 1",
             detail='Binder Error: column "o.province" not found'),
        Step(tool="run_sql", status="ok", rows=5, ms=38,
             sql=(
                 "SELECT b.province AS จังหวัด, SUM(o.total) AS ยอดขาย\n"
                 "FROM orders o JOIN branches b ON b.id = o.branch_id\n"
                 "WHERE o.order_date BETWEEN '2024-10-01' AND '2025-09-30'\n"
                 "GROUP BY b.province ORDER BY ยอดขาย DESC LIMIT 5"
             )),
        Step(tool="check_answer", status="ok", summary="ตัวเลขในคำตอบ 3/3 ตรงกับผลลัพธ์ SQL"),
    ],
    table=Table(
        columns=["จังหวัด", "ยอดขาย"],
        rows=[
            ["กรุงเทพมหานคร", 4812350],
            ["ชลบุรี", 2105900],
            ["เชียงใหม่", 1876420],
            ["ขอนแก่น", 1240780],
            ["ภูเก็ต", 1198600],
        ],
    ),
    chart=Chart(type="bar", x="จังหวัด", y="ยอดขาย"),
    meta=Meta(model="mock", tokens=0, ms=2400, retries=1),
)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if settings.use_mock_agent:
        return MOCK_RESPONSE
    try:
        return loop.answer(req)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e

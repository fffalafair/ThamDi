"""ชุดข้อมูล (คนที่ 2) — TODO 25–27 ต.ค. (งาน P2-05)

อัปโหลด → app.ingest.ingest() แปลงเป็นไฟล์ DuckDB ที่ {DATA_DIR}/datasets/{dataset_id}.duckdb
(ตำแหน่งนี้คือสัญญากับ agent ห้ามเปลี่ยนโดยไม่แก้ docs/CONTRACT.md)

ส่วนแปลงไฟล์ทำเสร็จแล้วใน app/ingest.py (8 นามสกุล + เทสต์) เหลือ:
- รับไฟล์ลง temp, เรียก ingest(), จับ IngestError → 400
- สร้าง dataset_id แบบสุ่ม ห้ามใช้ชื่อไฟล์ผู้ใช้เป็น path
- บันทึก metadata ลง Postgres + ตรวจเจ้าของทุก endpoint
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

from app.ingest import SUPPORTED_SUFFIXES  # noqa: E402,F401  ใช้ตรวจนามสกุลก่อนรับไฟล์


@router.post("", status_code=201)
async def upload(file: UploadFile) -> dict:
    raise HTTPException(status_code=501, detail="TODO: คนที่ 2")


@router.get("")
def list_datasets() -> list[dict]:
    raise HTTPException(status_code=501, detail="TODO: คนที่ 2")


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str) -> dict:
    raise HTTPException(status_code=501, detail="TODO: คนที่ 2")

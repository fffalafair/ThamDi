"""ตัวแปลงวันที่แบบไทย

agent เรียกใช้ฟังก์ชันเหล่านี้ ไม่ให้ LLM คำนวณวันที่เอง
- พ.ศ. ↔ ค.ศ.
- ปีงบประมาณ (1 ต.ค. ปีก่อน – 30 ก.ย.)
- ไตรมาส (ตามปีปฏิทิน หรือตามปีงบประมาณ)
- ชื่อเดือนไทย เต็มและย่อ
"""

from __future__ import annotations

import calendar
from datetime import date

BE_OFFSET = 543

# ปีที่มากกว่าค่านี้ถือว่าเป็น พ.ศ. (ข้อมูลธุรกิจทั่วไปไม่มีปี ค.ศ. เกิน 2400)
_BE_THRESHOLD = 2400

THAI_MONTHS: dict[str, int] = {
    "มกราคม": 1, "ม.ค.": 1, "มค": 1,
    "กุมภาพันธ์": 2, "ก.พ.": 2, "กพ": 2,
    "มีนาคม": 3, "มี.ค.": 3, "มีค": 3,
    "เมษายน": 4, "เม.ย.": 4, "เมย": 4,
    "พฤษภาคม": 5, "พ.ค.": 5, "พค": 5,
    "มิถุนายน": 6, "มิ.ย.": 6, "มิย": 6,
    "กรกฎาคม": 7, "ก.ค.": 7, "กค": 7,
    "สิงหาคม": 8, "ส.ค.": 8, "สค": 8,
    "กันยายน": 9, "ก.ย.": 9, "กย": 9,
    "ตุลาคม": 10, "ต.ค.": 10, "ตค": 10,
    "พฤศจิกายน": 11, "พ.ย.": 11, "พย": 11,
    "ธันวาคม": 12, "ธ.ค.": 12, "ธค": 12,
}


def be_to_ce(year: int) -> int:
    """พ.ศ. → ค.ศ."""
    return year - BE_OFFSET


def ce_to_be(year: int) -> int:
    """ค.ศ. → พ.ศ."""
    return year + BE_OFFSET


def normalize_year(year: int) -> int:
    """รับได้ทั้ง พ.ศ. และ ค.ศ. คืนค่าเป็น ค.ศ. เสมอ"""
    return be_to_ce(year) if year > _BE_THRESHOLD else year


def thai_month(name: str) -> int:
    """ชื่อเดือนไทย (เต็มหรือย่อ มีหรือไม่มีจุด) → เลขเดือน 1–12"""
    key = name.strip()
    if key in THAI_MONTHS:
        return THAI_MONTHS[key]
    compact = key.replace(".", "").replace(" ", "")
    if compact in THAI_MONTHS:
        return THAI_MONTHS[compact]
    raise ValueError(f"ไม่รู้จักชื่อเดือน: {name}")


def month_range(year: int, month: int) -> tuple[date, date]:
    """ช่วงวันที่ของเดือนนั้น (วันแรก, วันสุดท้าย)"""
    y = normalize_year(year)
    last = calendar.monthrange(y, month)[1]
    return date(y, month, 1), date(y, month, last)


def year_range(year: int) -> tuple[date, date]:
    """ช่วงวันที่ของปีปฏิทิน"""
    y = normalize_year(year)
    return date(y, 1, 1), date(y, 12, 31)


def fiscal_year_range(year: int) -> tuple[date, date]:
    """ปีงบประมาณ เช่น ปีงบ 2568 = 1 ต.ค. 2567 ถึง 30 ก.ย. 2568"""
    y = normalize_year(year)
    return date(y - 1, 10, 1), date(y, 9, 30)


def quarter_range(year: int, quarter: int, *, fiscal: bool = False) -> tuple[date, date]:
    """ไตรมาส 1–4 ของปีปฏิทิน หรือของปีงบประมาณถ้า fiscal=True

    ปีงบ: ไตรมาส 1 = ต.ค.–ธ.ค. ของปีก่อนหน้า
    """
    if quarter not in (1, 2, 3, 4):
        raise ValueError("ไตรมาสต้องเป็น 1–4")
    y = normalize_year(year)
    if fiscal:
        start_month = (10 + 3 * (quarter - 1) - 1) % 12 + 1
        start_year = y - 1 if quarter == 1 else y
    else:
        start_month = 3 * (quarter - 1) + 1
        start_year = y
    end_month = start_month + 2
    end_day = calendar.monthrange(start_year, end_month)[1]
    return date(start_year, start_month, 1), date(start_year, end_month, end_day)

from datetime import date

import pytest

from app.agent import thai_dates as td


def test_be_ce_roundtrip():
    assert td.be_to_ce(2568) == 2025
    assert td.ce_to_be(2025) == 2568


@pytest.mark.parametrize("year,expected", [(2568, 2025), (2025, 2025), (2500, 1957)])
def test_normalize_year(year, expected):
    assert td.normalize_year(year) == expected


def test_fiscal_year_2568():
    assert td.fiscal_year_range(2568) == (date(2024, 10, 1), date(2025, 9, 30))


def test_fiscal_year_accepts_ce():
    assert td.fiscal_year_range(2025) == (date(2024, 10, 1), date(2025, 9, 30))


def test_calendar_quarters():
    assert td.quarter_range(2567, 1) == (date(2024, 1, 1), date(2024, 3, 31))
    assert td.quarter_range(2567, 2) == (date(2024, 4, 1), date(2024, 6, 30))
    assert td.quarter_range(2567, 4) == (date(2024, 10, 1), date(2024, 12, 31))


def test_fiscal_quarters():
    assert td.quarter_range(2568, 1, fiscal=True) == (date(2024, 10, 1), date(2024, 12, 31))
    assert td.quarter_range(2568, 2, fiscal=True) == (date(2025, 1, 1), date(2025, 3, 31))
    assert td.quarter_range(2568, 4, fiscal=True) == (date(2025, 7, 1), date(2025, 9, 30))


def test_invalid_quarter():
    with pytest.raises(ValueError):
        td.quarter_range(2568, 5)


@pytest.mark.parametrize("name,num", [("มกราคม", 1), ("ม.ค.", 1), ("มค", 1), ("เม.ย.", 4), ("ธันวาคม", 12)])
def test_thai_month(name, num):
    assert td.thai_month(name) == num


def test_unknown_month():
    with pytest.raises(ValueError):
        td.thai_month("สงกรานต์")


def test_month_range_leap_year():
    # 2567 = ค.ศ. 2024 ปีอธิกสุรทิน
    assert td.month_range(2567, 2) == (date(2024, 2, 1), date(2024, 2, 29))

"""eval runner (P1) — TODO 28–29 ต.ค.

ใช้: python eval/run.py --system A --db data/datasets/demo.duckdb

ขั้นตอน:
1. อ่าน eval/questions.jsonl
2. ข้อที่ expect = "answer": รัน gold_sql เทียบกับผลลัพธ์ของระบบ (เทียบผลลัพธ์ ไม่เทียบตัว SQL)
3. ข้อที่ expect = "clarify" / "refuse": ตรวจว่า status ตรง
4. บันทึก eval/results/<system>_<YYYYMMDD-HHMM>.json พร้อม token, latency, retries ต่อข้อ

ตอนนี้ทำได้แค่ตรวจว่า SQL เฉลยทุกข้อรันได้ (ใช้สลับกันตรวจคำถามของอีกคน)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).parent


def load_questions(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def results_equal(a: list[tuple], b: list[tuple]) -> bool:
    """เทียบผลลัพธ์แบบไม่สนลำดับแถว และปัดทศนิยมให้ตรงกัน"""

    def norm(rows):
        return sorted(tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows)

    return norm(a) == norm(b)


def check_gold(db: Path, questions: list[dict]) -> int:
    con = duckdb.connect(str(db), read_only=True)
    failed = 0
    for q in questions:
        if not q.get("gold_sql"):
            continue
        try:
            rows = con.execute(q["gold_sql"]).fetchall()
            print(f"✓ {q['id']}  {len(rows)} แถว")
        except duckdb.Error as e:
            failed += 1
            print(f"✗ {q['id']}  {e}")
    return failed


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/datasets/demo.duckdb"))
    ap.add_argument("--questions", type=Path, default=ROOT / "questions.jsonl")
    ap.add_argument("--system", choices=["A", "B", "C", "D"])
    ap.add_argument("--check-gold", action="store_true", help="ตรวจว่า SQL เฉลยทุกข้อรันได้")
    args = ap.parse_args()

    qs = load_questions(args.questions)
    if args.check_gold or not args.system:
        raise SystemExit(1 if check_gold(args.db, qs) else 0)

    raise NotImplementedError("TODO: เรียก agent ระบบที่เลือก แล้วให้คะแนน")

"""สร้างฐานข้อมูลยอดขายภาษาไทยสำหรับทดสอบ (คนที่ 1)

ใช้: python scripts/gen_sales_db.py --out data/datasets/demo.duckdb --seed 42

ตั้งใจใส่กรณียากไว้ในข้อมูล:
- ชื่อจังหวัดสะกดหลายแบบ ("กทม", "กรุงเทพฯ", "กรุงเทพมหานคร", "จ.เชียงใหม่")
- วันที่ครอบคลุมปีงบ 2566–2568 (ต.ค. 2565 – ก.ย. 2568)
- คอลัมน์ภาษาไทยปนอังกฤษ ("ช่องทาง")
seed เดิม = ข้อมูลเดิมทุกครั้ง เพื่อให้ SQL เฉลยใน eval ให้ผลคงที่
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

# (ชื่อจังหวัดมาตรฐาน, [ชื่อที่ใช้จริงในข้อมูล])
PROVINCES = [
    ("กรุงเทพมหานคร", ["กรุงเทพมหานคร", "กรุงเทพฯ", "กทม"]),
    ("ชลบุรี", ["ชลบุรี", "จ.ชลบุรี"]),
    ("เชียงใหม่", ["เชียงใหม่", "จ.เชียงใหม่"]),
    ("ขอนแก่น", ["ขอนแก่น"]),
    ("ภูเก็ต", ["ภูเก็ต"]),
    ("นครราชสีมา", ["นครราชสีมา", "โคราช"]),
    ("สงขลา", ["สงขลา"]),
    ("ปทุมธานี", ["ปทุมธานี"]),
]

CATEGORIES = {
    "เครื่องดื่ม": [("กาแฟเย็น", 65), ("ชาเขียว", 55), ("น้ำผลไม้", 45), ("โกโก้", 60)],
    "ขนม": [("ครัวซองต์", 75), ("เค้กช็อกโกแลต", 120), ("คุกกี้", 40)],
    "อาหาร": [("ข้าวผัด", 80), ("สปาเกตตี", 140), ("แซนด์วิช", 95)],
    "ของใช้": [("แก้วน้ำ", 250), ("ถุงผ้า", 150)],
}

FIRST_NAMES = ["สมชาย", "สมหญิง", "วิชัย", "มาลี", "ปิยะ", "อรุณ", "กมล", "ศิริ", "ธนา", "นภา"]
LAST_NAMES = ["ใจดี", "รักไทย", "สุขสันต์", "มั่นคง", "ศรีสุข", "ทองดี", "แสงทอง"]

START = date(2022, 10, 1)  # ต้นปีงบ 2566
END = date(2025, 9, 30)  # ปลายปีงบ 2568


def build(out: Path, seed: int, n_orders: int) -> None:
    rnd = random.Random(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    con = duckdb.connect(str(out))

    con.execute("CREATE TABLE branches (id INTEGER PRIMARY KEY, name TEXT, province TEXT)")
    branches = []
    bid = 1
    for _, spellings in PROVINCES:
        for i in range(rnd.randint(1, 3)):
            branches.append((bid, f"สาขา {spellings[0]} {i + 1}", rnd.choice(spellings)))
            bid += 1
    con.executemany("INSERT INTO branches VALUES (?, ?, ?)", branches)

    con.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price DECIMAL(10,2))")
    products = []
    pid = 1
    for cat, items in CATEGORIES.items():
        for name, price in items:
            products.append((pid, name, cat, price))
            pid += 1
    con.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    con.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, province TEXT, joined_at DATE)")
    customers = []
    for cid in range(1, 401):
        prov = rnd.choice(PROVINCES)[1]
        joined = START + timedelta(days=rnd.randint(0, (END - START).days))
        customers.append((cid, f"{rnd.choice(FIRST_NAMES)} {rnd.choice(LAST_NAMES)}", rnd.choice(prov), joined))
    con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

    con.execute(
        """CREATE TABLE orders (
            id INTEGER PRIMARY KEY, order_date DATE, branch_id INTEGER, customer_id INTEGER,
            product_id INTEGER, qty INTEGER, total DECIMAL(12,2), "ช่องทาง" TEXT)"""
    )
    orders = []
    span = (END - START).days
    for oid in range(1, n_orders + 1):
        d = START + timedelta(days=rnd.randint(0, span))
        b = rnd.choice(branches)
        c = rnd.choice(customers)
        p = rnd.choice(products)
        qty = rnd.randint(1, 5)
        orders.append((oid, d, b[0], c[0], p[0], qty, float(p[3]) * qty, rnd.choice(["หน้าร้าน", "ออนไลน์"])))
    con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", orders)

    con.close()
    print(f"สร้าง {out}: {len(branches)} สาขา, {len(products)} สินค้า, {len(customers)} ลูกค้า, {n_orders} คำสั่งซื้อ")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/datasets/demo.duckdb"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--orders", type=int, default=18000)
    args = ap.parse_args()
    build(args.out, args.seed, args.orders)

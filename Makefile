.PHONY: up down logs data test gold smoke

up:            ## รันทั้งระบบ
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

data:          ## สร้างฐานข้อมูลยอดขายตัวอย่าง
	python scripts/gen_sales_db.py --out data/datasets/demo.duckdb

test:          ## pytest ฝั่ง API
	cd services/api && python -m pytest -q

gold: data     ## ตรวจว่า SQL เฉลยใน eval รันได้ทุกข้อ
	python eval/run.py --check-gold

smoke:         ## ไล่เส้นหลักกับระบบที่รันอยู่
	bash scripts/smoke.sh

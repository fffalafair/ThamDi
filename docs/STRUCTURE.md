# ThamDi · โครงสร้างโปรเจกต์ (Repository Structure)

เอกสารนี้อธิบายว่าแต่ละโฟลเดอร์และไฟล์ใน repo ทำหน้าที่อะไร ใครรับผิดชอบ และทำไปถึงไหนแล้ว
ใช้คู่กับ [`CONTRACT.md`](CONTRACT.md) (สัญญากลาง), [`PLAN.md`](PLAN.md) (แผนรายวัน) และ [`TASKS.md`](TASKS.md) (แบ่งงาน)

**สัญลักษณ์สถานะ:** ✅ ใช้งานได้แล้ว · 🟡 mock / บางส่วน · ⏳ ยังไม่ทำ (มี TODO)
**ผู้รับผิดชอบ:** **P1** = @fffalafair (AI + Eval) · **P2** = @SoSick41 (Web + ระบบ)

---

## 1. ผังโฟลเดอร์

```
ThamDi/
├── README.md                     เอกสารหลักของโปรเจกต์ (9 หัวข้อ)
├── Makefile                      คำสั่งลัด: make up / data / test / gold / smoke
├── docker-compose.yml            รัน 3 container: postgres, api, web
├── .env.example                  ตัวอย่างค่าตั้ง (คัดลอกเป็น .env)
├── .gitignore
│
├── .github/
│   ├── workflows/ci.yml          CI: pytest + ruff, ตรวจ SQL เฉลย, build เว็บ
│   ├── pull_request_template.md  เช็กลิสต์ก่อนขอ review
│   └── CODEOWNERS                ใครดูแลไฟล์ไหน (GitHub ขอ review อัตโนมัติ)
│
├── docs/
│   ├── CONTRACT.md               สัญญา API ระหว่าง P1 กับ P2
│   ├── PLAN.md                   แผนการทำงานรายวัน
│   ├── PROJECT.md                ภาพรวม สถาปัตยกรรม การทดลอง
│   ├── ISSUES.md                 บันทึกปัญหาที่เจอและวิธีแก้
│   ├── TASKS.md                  แบ่งงานรายงาน P1 / P2
│   └── STRUCTURE.md              ไฟล์นี้
│
├── apps/web/                     หน้าเว็บ Next.js (P2)
│   ├── app/
│   │   ├── layout.tsx            header + เมนู + ฟอนต์
│   │   ├── page.tsx              หน้าแชท
│   │   ├── datasets/page.tsx     หน้าชุดข้อมูล
│   │   ├── eval/page.tsx         หน้าผลการทดสอบ
│   │   └── globals.css           Tailwind + สีหลัก
│   ├── lib/api.ts                ฟังก์ชันเรียก API + type ตามสัญญา
│   ├── public/mascot.svg         น้องเต่าคิว (โลโก้ + มาสคอต)
│   ├── package.json / package-lock.json
│   ├── next.config.mjs / postcss.config.mjs / tsconfig.json
│   └── Dockerfile
│
├── services/api/                 Backend FastAPI
│   ├── app/
│   │   ├── main.py               สร้างแอป, CORS, รวม router, /health
│   │   ├── config.py             อ่านค่าจาก .env
│   │   ├── schemas.py            รูปแบบข้อมูลกลาง (ต้องตรง CONTRACT.md)
│   │   ├── ingest.py             แปลงไฟล์อัปโหลด 8 นามสกุล → DuckDB (P2)
│   │   ├── routers/
│   │   │   ├── auth.py           สมัคร / login (P2)
│   │   │   ├── datasets.py       อัปโหลด / รายการ / รายละเอียด (P2)
│   │   │   └── chat.py           POST /api/chat (P1)
│   │   └── agent/                ส่วน AI ทั้งหมด (P1)
│   │       ├── sql_guard.py      ตัวตรวจ SQL
│   │       ├── thai_dates.py     ตัวแปลงวันที่ไทย
│   │       ├── tools.py          เครื่องมือที่ agent เรียกได้
│   │       ├── loop.py           agent loop (ระบบ A/B/C/D)
│   │       └── llm.py            เรียก LLM + สำรองหลายชั้น
│   ├── tests/
│   │   ├── test_sql_guard.py
│   │   ├── test_thai_dates.py
│   │   ├── test_ingest.py
│   │   └── test_api.py
│   ├── requirements.txt / requirements-dev.txt
│   ├── pyproject.toml            ตั้งค่า pytest + ruff
│   └── Dockerfile
│
├── eval/                         ชุดทดสอบและการวัดผล (P1)
│   ├── questions.jsonl           คำถาม + SQL เฉลย (ตอนนี้ 7 ข้อตัวอย่าง)
│   ├── run.py                    eval runner
│   └── results/                  ผล eval แต่ละรอบ (JSON)
│
├── scripts/
│   ├── gen_sales_db.py           สร้างฐานข้อมูลยอดขายภาษาไทย (P1)
│   └── smoke.sh                  smoke test ทั้งระบบ (P2)
│
└── data/                         ⚠️ ไม่อยู่ใน git — ไฟล์ DuckDB ที่สร้าง/อัปโหลด
    └── datasets/{dataset_id}.duckdb
```

---

## 2. รายละเอียดแต่ละส่วน

### 2.1 Backend: `services/api/app/`

| ไฟล์ | หน้าที่ | เจ้าของ | สถานะ | ทำต่อเมื่อ |
|---|---|---|---|---|
| `main.py` | สร้าง FastAPI, CORS, รวม router, `/health` | P2 | ✅ | — |
| `config.py` | อ่านค่า `.env` เช่น API key, `USE_MOCK_AGENT` | ทั้งคู่ | ✅ | เพิ่มค่าใหม่เมื่อจำเป็น |
| `schemas.py` | `ChatRequest`, `ChatResponse`, `Step`, `Table`, `Chart`, `Meta` | ทั้งคู่ | ✅ | **แก้ต้องแก้ CONTRACT.md ด้วย** |
| `routers/chat.py` | `POST /api/chat` ตอบ mock ตอนนี้ | P1 | 🟡 | 30–31 ต.ค. ปิด mock |
| `routers/auth.py` | register / login (bcrypt + JWT) | P2 | ⏳ | 23–24 ต.ค. |
| `ingest.py` | แปลง `.csv .tsv .xlsx .xls .ods .json .jsonl .parquet` → DuckDB, เดา encoding ไทย, ทำความสะอาดชื่อ, เขียนแบบ atomic | P2 | ✅ | เพิ่ม `.sqlite` ถ้าทัน (P2-15) |
| `routers/datasets.py` | รับไฟล์ → เรียก `ingest()` → บันทึก metadata | P2 | ⏳ | 25–27 ต.ค. |

### 2.2 Agent: `services/api/app/agent/`

| ไฟล์ | หน้าที่ | สถานะ | ทำต่อเมื่อ |
|---|---|---|---|
| `sql_guard.py` | อนุญาตเฉพาะ SELECT, คำสั่งเดียว, ห้ามฟังก์ชันอ่านไฟล์, allowlist ตาราง, เติม LIMIT | ✅ | เพิ่ม timeout ต่อ query |
| `thai_dates.py` | `be_to_ce`, `fiscal_year_range`, `quarter_range`, `thai_month`, `month_range` | ✅ | เพิ่มช่วงเทศกาลถ้าต้องการ |
| `tools.py` | `connect` (read-only), `list_tables`, `describe_table`, `run_sql` | 🟡 | 25–27 ต.ค. ทำ `find_values`, `make_chart` |
| `loop.py` | agent loop | ⏳ | 23–24 ต.ค. ระบบ A → 30–31 ต.ค. ระบบ B/C/D |
| `llm.py` | Groq → Gemini ผ่านไลบรารี `openai` เปลี่ยนแค่ `base_url` | ✅ | ต่อกับโหมดพื้นฐานเมื่อล่มหมด |

**การป้องกันใน `sql_guard.py` (เรียงจากชั้นนอกสุด)**
1. แยกวิเคราะห์ด้วย sqlglot ต้องเป็นคำสั่งเดียวและเป็น query อ่านข้อมูล
2. ห้าม node อันตราย: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, ATTACH, COPY, PRAGMA, SET ฯลฯ
3. ห้ามฟังก์ชันอ่านไฟล์หรือเครือข่าย: `read_csv`, `read_parquet`, `glob`, `getenv` ฯลฯ
4. ห้ามชื่อตารางที่หน้าตาเป็น path หรืออ้างฐานข้อมูลอื่น
5. allowlist: ใช้ได้เฉพาะตารางที่มีจริงในชุดข้อมูล (+ ชื่อ CTE)
6. ตอนเปิด DuckDB: `read_only=True` และ `SET enable_external_access = false`

### 2.3 Frontend: `apps/web/`

| ไฟล์ | หน้าที่ | สถานะ | ทำต่อเมื่อ |
|---|---|---|---|
| `app/layout.tsx` | header + ชื่อ "ถามดิ" + มาสคอต, เมนู, โหลดฟอนต์ IBM Plex Sans Thai | ✅ | เพิ่มปุ่มบัญชีผู้ใช้ |
| `app/page.tsx` | แชท: ช่องถาม, คำตอบ, ตาราง, ขั้นตอนของ agent | 🟡 | 25–27 ต.ค. กราฟ, เลือกชุดข้อมูล, ประวัติ |
| `app/datasets/page.tsx` | อัปโหลด + schema + แถวตัวอย่าง (มีค่า `ACCEPT` 8 นามสกุลแล้ว) | ⏳ | 25–27 ต.ค. |
| `public/mascot.svg` | น้องเต่าคิว ใช้เป็นโลโก้และใน README | ✅ | — |
| `app/eval/page.tsx` | ตารางผล 4 ระบบ × 7 หมวด | ⏳ | 1–2 พ.ย. |
| `lib/api.ts` | `ask()` + type `ChatResponse` | ✅ | เพิ่ม auth, datasets |

**เวอร์ชันที่ปักไว้:** next 15.5.27 · react 19.2.8 · tailwindcss 4.1.11 · postcss override 8.5.28
(`npm audit` = 0 vulnerabilities ณ 22 ต.ค. — อย่าอัปเกรดโดยไม่ build ทดสอบ)

### 2.4 Eval: `eval/`

| ไฟล์ | หน้าที่ | สถานะ |
|---|---|---|
| `questions.jsonl` | 1 บรรทัด = 1 คำถาม | 🟡 7/100 ข้อ |
| `run.py --check-gold` | ตรวจว่า SQL เฉลยทุกข้อรันได้ | ✅ |
| `run.py --system A` | รัน agent แล้วให้คะแนน | ⏳ 28–29 ต.ค. |
| `results/` | `<system>_<YYYYMMDD-HHMM>.json` | ⏳ |

**รูปแบบคำถาม**
```json
{"id":"Q051","category":"thai_date","question":"ยอดขายรวมปีงบประมาณ 2568","gold_sql":"SELECT SUM(total) FROM orders WHERE order_date BETWEEN '2024-10-01' AND '2025-09-30'","expect":"answer"}
```

| `category` | หมวด | จำนวนเป้าหมาย | คนเขียน |
|---|---|---|---|
| `basic` | รวม/นับพื้นฐาน | 20 | P1 |
| `filter` | กรองเงื่อนไข | 15 | P1 |
| `thai_date` | วันที่และปีแบบไทย | 15 | P1 |
| `join` | JOIN หลายตาราง | 15 | P2 |
| `spelling` | ค่าสะกดหลายแบบ | 15 | P2 |
| `clarify` | กำกวม → ถามกลับ (`gold_sql: null`) | 10 | P2 |
| `refuse` | ตอบไม่ได้ → ปฏิเสธ (`gold_sql: null`) | 10 | P2 |

### 2.5 ข้อมูลทดสอบ: `scripts/gen_sales_db.py`

| ตาราง | คอลัมน์ | จำนวน |
|---|---|---|
| `branches` | id, name, province | 15 สาขา |
| `products` | id, name, category, price | 12 สินค้า (4 หมวด) |
| `customers` | id, name, province, joined_at | 400 คน |
| `orders` | id, order_date, branch_id, customer_id, product_id, qty, total, ช่องทาง | 18,000 รายการ |

- วันที่ครอบคลุมปีงบ 2566–2568 (1 ต.ค. 2565 – 30 ก.ย. 2568)
- จังหวัดสะกดหลายแบบโดยตั้งใจ: กทม / กรุงเทพฯ / กรุงเทพมหานคร, จ.เชียงใหม่, โคราช
- `--seed 42` (ค่าเริ่มต้น) ให้ข้อมูลเหมือนเดิมทุกครั้ง **ห้ามเปลี่ยน seed หลังเขียน SQL เฉลยแล้ว**

### 2.6 การทดสอบและ CI

| ชุด | คำสั่ง | สถานะ |
|---|---|---|
| pytest ทั้งหมด | `make test` | ✅ 78 ข้อผ่าน |
| pytest ตัวตรวจ SQL | `make test` | ✅ |
| pytest แปลงไฟล์ 8 นามสกุล | `make test` | ✅ |
| pytest วันที่ไทย | `make test` | ✅ |
| pytest API (mock ตรงสัญญา) | `make test` | ✅ |
| lint | `ruff check .` | ✅ |
| SQL เฉลย | `make gold` | ✅ 5/5 |
| เว็บ build | `npm run build` | ✅ |
| smoke ทั้งระบบ | `make smoke` | 🟡 health + chat + web |

CI (`.github/workflows/ci.yml`) รัน 3 job ทุก PR และทุก push เข้า `main`/`dev`: **api**, **eval-gold**, **web**

---

## 3. ค่าตั้ง `.env`

| ตัวแปร | ค่าเริ่มต้น | ใช้ทำอะไร |
|---|---|---|
| `GROQ_API_KEY` | — | LLM หลัก |
| `GROQ_MODEL` | `qwen/qwen3-32b` | |
| `GEMINI_API_KEY` | — | LLM สำรอง |
| `GEMINI_MODEL` | `gemini-flash-latest` | ตรวจชื่อรุ่นในหน้า Google AI Studio อีกครั้ง |
| `USE_MOCK_AGENT` | `true` | `true` = `/api/chat` ตอบ mock |
| `DEMO_MODE` | `false` | `true` = ใช้คำตอบที่บันทึกไว้ |
| `JWT_SECRET` | `change-me` | **เปลี่ยนก่อน deploy** |
| `POSTGRES_USER` / `PASSWORD` / `DB` | `app` | **เปลี่ยนก่อน deploy** |
| `CORS_ORIGINS` | `http://localhost:3000` | ใส่โดเมนจริงตอน deploy |
| `PUBLIC_API_URL` | `http://localhost:8000` | URL ที่เบราว์เซอร์ใช้เรียก API |

---

## 4. เอาขึ้น GitHub

```bash
unzip ThamDi.zip && cd ThamDi
git init
git add .
git commit -m "chore: initial scaffold"
git branch -M main
git remote add origin https://github.com/<ชื่อ>/ThamDi.git
git push -u origin main
git checkout -b dev
git push -u origin dev
```

**ตั้งค่าใน GitHub (Settings)**
- [ ] **Branches → Add rule** ให้ `main` และ `dev`: Require a pull request · Require status checks (`api`, `eval-gold`, `web`)
- [ ] **Collaborators** เพิ่มเพื่อนในทีม
- [ ] **General → Default branch** = `dev` (ให้ PR เข้า `dev` โดยอัตโนมัติ)

---

## 5. เริ่มทำงานวันแรก

### ทั้งคู่
```bash
git clone https://github.com/<ชื่อ>/ThamDi.git && cd ThamDi
cp .env.example .env            # ใส่ API key
make data                       # สร้าง data/datasets/demo.duckdb
make test                       # ต้องผ่านทั้งหมด
```

### P1 (AI + Eval)
```bash
git checkout dev && git checkout -b p1/agent-system-a
cd services/api && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
# งานแรก: loop.py ระบบ A + สคริปต์ CLI ถามคำถาม
```

### P2 (Web + ระบบ)
```bash
git checkout dev && git checkout -b p2/auth
make up                         # รัน postgres + api (mock) + web
# เปิด http://localhost:3000 — หน้าแชทต่อกับ mock ได้แล้ว
# งานแรก: routers/auth.py + หน้า login
```

---

## 6. กฎที่ต้องจำ

1. **แก้ `schemas.py` = แก้สัญญา** ต้องแก้ `CONTRACT.md` และ `apps/web/lib/api.ts` ให้ตรงกัน แล้วบอกอีกคน
2. **อ่านไฟล์อัปโหลดผ่าน `ingest.py` เท่านั้น** ห้ามให้ agent อ่านไฟล์ต้นฉบับ
3. **ตำแหน่งไฟล์ DuckDB** `{DATA_DIR}/datasets/{dataset_id}.duckdb` ห้ามเปลี่ยนโดยไม่ตกลงกัน
4. **ห้าม commit** `.env`, `data/`, `*.duckdb`
5. **branch:** `p1/<เรื่อง>` หรือ `p2/<เรื่อง>` แตกจาก `dev` → PR เข้า `dev`
6. **commit:** `<type>(<ส่วน>): <ทำอะไร>` เช่น `feat(agent): add find_values tool`
7. **เจอปัญหา → จดลง `docs/ISSUES.md` ทันที** พร้อมตัวเลขก่อน/หลังถ้ามี

# สัญญากลาง (Contract)

ไฟล์นี้คือข้อตกลงระหว่าง P1 [@fffalafair](https://github.com/fffalafair) (agent) และ P2 [@SoSick41](https://github.com/SoSick41) (web + ระบบ)
**เปลี่ยนอะไรในนี้ ต้องบอกอีกคนทันที** และแก้ `services/api/app/schemas.py` กับ `apps/web/lib/api.ts` ให้ตรงกัน

## 1. Endpoint

| Method | Path | เจ้าของ | สถานะ |
|---|---|---|---|
| GET | `/health` | P2 | ✅ |
| POST | `/api/auth/register` | P2 | ✅ |
| POST | `/api/auth/login` | P2 | ✅ |
| GET | `/api/auth/me` | P2 | ✅ |
| POST | `/api/datasets` | P2 | ⏳ |
| GET | `/api/datasets` | P2 | ⏳ |
| GET | `/api/datasets/{id}` | P2 | ⏳ |
| POST | `/api/chat` | P1 | 🟡 mock |
| GET | `/api/eval/results` | P1 | ⏳ |

ทุก endpoint ยกเว้น `/health`, `/api/auth/register` และ `/api/auth/login` ต้องมี `Authorization: Bearer <JWT>`
ไม่มี token หรือ token หมดอายุ (24 ชม.) → `401` · หน้าเว็บพาไปหน้า login

### Auth

| Endpoint | Request | Response |
|---|---|---|
| `POST /api/auth/register` | `{ "email": "a@b.com", "password": "อย่างน้อย 8 ตัว" }` | `201` `{ "access_token": "...", "token_type": "bearer" }` · อีเมลซ้ำ `409` · ข้อมูลไม่ถูกรูปแบบ `422` |
| `POST /api/auth/login` | `{ "email": "a@b.com", "password": "..." }` | `200` แบบเดียวกับ register · ผิด `401` · เกิน 10 ครั้ง/นาทีต่ออีเมล `429` |
| `GET /api/auth/me` | — | `200` `{ "id": "uuid", "email": "a@b.com" }` |

error ทุกตัวอยู่ในรูป `{ "detail": "ข้อความภาษาไทย" }` (ยกเว้น `422` ที่เป็นรูปแบบของ FastAPI)

## 2. `POST /api/chat`

**Request**
```json
{ "dataset_id": "ds_123", "question": "ปีงบ 2568 จังหวัดไหนยอดขายสูงสุด" }
```

**Response**
```json
{
  "status": "answered",
  "answer": "ข้อความคำตอบ",
  "steps": [
    { "tool": "describe_table", "status": "ok", "args": {"name": "orders"}, "summary": "..." },
    { "tool": "run_sql", "status": "error", "sql": "SELECT ...", "detail": "error message" },
    { "tool": "run_sql", "status": "ok", "sql": "SELECT ...", "rows": 5, "ms": 38 }
  ],
  "table": { "columns": ["จังหวัด", "ยอดขาย"], "rows": [["กรุงเทพมหานคร", 4812350]] },
  "chart": { "type": "bar", "x": "จังหวัด", "y": "ยอดขาย" },
  "meta": { "model": "qwen/qwen3-32b", "tokens": 3120, "ms": 2400, "retries": 1 }
}
```

| ฟิลด์ | ค่า |
|---|---|
| `status` | `answered` · `clarify` (ถามกลับ) · `refused` (ตอบไม่ได้) · `error` |
| `table`, `chart` | เป็น `null` ได้ |
| `chart.type` | `bar` · `line` · `pie` |
| `steps[].status` | `ok` · `error` |

## 3. ไฟล์ข้อมูล

- ไฟล์ที่อัปโหลดแปลงเป็น DuckDB ที่ **`{DATA_DIR}/datasets/{dataset_id}.duckdb`**
- แปลงด้วย `services/api/app/ingest.py` เท่านั้น
- ไม่เกิน 10 MB, ไม่เกิน 20 ตาราง, ไม่เกิน 200 คอลัมน์ต่อตาราง

| นามสกุล | ได้กี่ตาราง | หมายเหตุ |
|---|---|---|
| `.csv` `.tsv` | 1 | เดา encoding: utf-8 → cp874 → tis-620 |
| `.xlsx` `.xls` `.ods` | 1 ต่อ sheet | ข้าม sheet ว่าง · หัวตารางต้องอยู่แถวแรก |
| `.json` | 1 | ต้องเป็นรายการ object · object ซ้อน 1 ชั้นแตกเป็น `a_b` |
| `.jsonl` | 1 | 1 บรรทัด = 1 object |
| `.parquet` | 1 | |

- ชื่อตาราง: ชื่อไฟล์ (หรือชื่อ sheet) ผ่าน `clean_name()` — เก็บไทย/อังกฤษ/ตัวเลข/`_` ที่เหลือเป็น `_`
- ชื่อคอลัมน์ซ้ำ: ต่อท้าย `_1`, `_2` · ว่าง: `column_N` · ขึ้นต้นด้วยตัวเลข: เติม `_` ข้างหน้า
- agent เปิดแบบ read-only เสมอ

## 4. Git flow

- แตก branch จาก `dev` ตั้งชื่อ `<ชื่อ>/<เรื่อง>` เช่น `p1/sql-guard`
- เปิด PR เข้า `dev` · CI ต้องผ่านก่อน merge · ห้าม push ตรงเข้า `dev` / `main`
- รวม `dev` → `main` เมื่อถึง milestone (`main` = เวอร์ชันที่ deploy)
- commit: `<type>(<ส่วน>): <ทำอะไร>` เช่น `feat(agent): add find_values tool`

## 5. ประวัติการเปลี่ยนสัญญา

| วันที่ | เปลี่ยนอะไร | โดย |
|---|---|---|
| 22 ต.ค. | ฉบับแรก | ทั้งคู่ |
| 22 ต.ค. | รองรับ 8 นามสกุล (หัวข้อ 3), เปลี่ยนชื่อโปรเจกต์เป็น ThamDi | ทั้งคู่ |
| 23 ต.ค. | เพิ่มรายละเอียด auth และ `GET /api/auth/me` (หัวข้อ 1) | P2 |

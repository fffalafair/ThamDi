-- ตารางของระบบ (P2) — รันทุกครั้งที่ API เริ่ม ต้องรันซ้ำได้โดยไม่พัง
-- ข้อมูลที่ผู้ใช้อัปโหลดไม่อยู่ที่นี่ แต่อยู่ใน {DATA_DIR}/datasets/{dataset_id}.duckdb

CREATE TABLE IF NOT EXISTS users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email         text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS datasets (
    id         text PRIMARY KEY,                -- ds_ + 12 ตัวสุ่ม
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       text NOT NULL,                   -- ชื่อไฟล์เดิมที่ผู้ใช้อัปโหลด
    tables     jsonb NOT NULL DEFAULT '[]',     -- TableInfo ทุกตาราง
    rows       integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL DEFAULT now() + interval '7 days'
);
CREATE INDEX IF NOT EXISTS datasets_user_id_idx ON datasets (user_id);
CREATE INDEX IF NOT EXISTS datasets_expires_at_idx ON datasets (expires_at);

CREATE TABLE IF NOT EXISTS chat_history (
    id         bigserial PRIMARY KEY,
    user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dataset_id text NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    question   text NOT NULL,
    response   jsonb NOT NULL,                  -- ChatResponse ทั้งก้อน
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chat_history_user_dataset_idx ON chat_history (user_id, dataset_id, created_at DESC);

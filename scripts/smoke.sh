#!/usr/bin/env bash
# smoke test: ไล่เส้นหลักกับระบบที่รันอยู่
# TODO (คนที่ 2): เพิ่ม register → login → upload → chat ด้วย token จริง
set -euo pipefail

API="${API:-http://localhost:8000}"
WEB="${WEB:-http://localhost:3000}"

echo "1) health"
curl -fsS "$API/health" | grep -q '"ok"'

echo "2) chat"
curl -fsS -X POST "$API/api/chat" \
  -H 'Content-Type: application/json' \
  -d '{"dataset_id":"demo","question":"มีลูกค้ากี่คน"}' | grep -q '"status"'

echo "3) web"
curl -fsS -o /dev/null "$WEB"

echo "✓ smoke ผ่านทุกข้อ"

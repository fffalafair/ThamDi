// หน้าชุดข้อมูล (P2) — TODO 25–27 ต.ค.
// อัปโหลด, รายการชุดข้อมูล, schema, แถวตัวอย่าง, แจ้งค่าที่สะกดหลายแบบ
// ช่องอัปโหลดใช้ accept={ACCEPT} ให้ตรงกับ SUPPORTED_SUFFIXES ใน services/api/app/ingest.py
const ACCEPT = ".csv,.tsv,.xlsx,.xls,.ods,.json,.jsonl,.parquet";

export default function DatasetsPage() {
  return (
    <section className="flex flex-col gap-2">
      <h1 className="text-2xl font-bold">ชุดข้อมูลของฉัน</h1>
      <p className="text-muted">รองรับ {ACCEPT.replaceAll(",", " ")} · ไม่เกิน 10 MB</p>
      <p className="text-muted">TODO: อัปโหลดไฟล์และดูโครงสร้างตาราง</p>
    </section>
  );
}

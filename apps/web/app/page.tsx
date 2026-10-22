"use client";

// หน้าแชท (P2) — ตอนนี้ต่อกับ mock endpoint
// TODO: เลือกชุดข้อมูล, ประวัติแชท, กราฟ (Recharts), ปุ่มดาวน์โหลด CSV / คัดลอก SQL

import { useState } from "react";
import { ask, type ChatResponse } from "@/lib/api";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await ask("demo", question));
    } catch (err) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาด");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      {result && (
        <article className="flex flex-col gap-5 rounded-2xl border border-line bg-white p-6">
          <p className="text-base leading-7">{result.answer}</p>

          {result.table && (
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="w-full text-sm tabular-nums">
                <thead className="bg-gray-50 text-left">
                  <tr>
                    {result.table.columns.map((c) => (
                      <th key={c} scope="col" className="px-4 py-2 font-semibold">{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.table.rows.map((row, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      {row.map((cell, j) => (
                        <td key={j} className="px-4 py-2">
                          {typeof cell === "number" ? cell.toLocaleString("th-TH") : cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <details open className="rounded-lg border border-line bg-gray-50">
            <summary className="cursor-pointer px-4 py-3 font-semibold">
              ขั้นตอนของ agent <span className="font-normal text-muted">· {result.steps.length} ขั้น · แก้ตัวเอง {result.meta.retries} รอบ</span>
            </summary>
            <ol className="flex flex-col gap-3 px-4 pb-4">
              {result.steps.map((s, i) => (
                <li key={i} className="flex flex-col gap-1">
                  <span className={`font-mono text-sm ${s.status === "error" ? "text-orange-800" : "text-brand"}`}>
                    {i + 1}. {s.tool} {s.status === "error" && "— error"}
                  </span>
                  {s.summary && <span className="text-sm text-muted">{s.summary}</span>}
                  {s.detail && <span className="font-mono text-sm text-orange-800">{s.detail}</span>}
                  {s.sql && s.status === "ok" && (
                    <pre className="overflow-x-auto rounded-md bg-gray-900 p-3 font-mono text-xs text-gray-100">{s.sql}</pre>
                  )}
                </li>
              ))}
            </ol>
          </details>
        </article>
      )}

      {error && <p role="alert" className="text-red-700">{error}</p>}

      <form onSubmit={onSubmit} className="flex items-center gap-2 rounded-2xl border border-gray-300 bg-white p-2 pl-4">
        <label htmlFor="q" className="sr-only">พิมพ์คำถาม</label>
        <input
          id="q"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="ถามอะไรก็ได้เกี่ยวกับข้อมูลนี้"
          className="min-h-10 grow bg-transparent outline-none"
        />
        <button type="submit" disabled={loading} className="min-h-11 rounded-xl bg-brand px-4 font-semibold text-white disabled:opacity-60">
          {loading ? "กำลังคิด…" : "ถาม"}
        </button>
      </form>
      <p className="-mt-3 text-xs text-muted">ระบบรันได้เฉพาะคำสั่งอ่านข้อมูล (SELECT) · ส่งเฉพาะโครงสร้างตารางและแถวตัวอย่างให้ AI</p>
    </div>
  );
}

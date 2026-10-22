// รูปแบบข้อมูลต้องตรงกับ docs/CONTRACT.md และ services/api/app/schemas.py

export type Step = {
  tool: string;
  status: "ok" | "error";
  args?: Record<string, unknown> | null;
  sql?: string | null;
  summary?: string | null;
  detail?: string | null;
  rows?: number | null;
  ms?: number | null;
};

export type ChatResponse = {
  status: "answered" | "clarify" | "refused" | "error";
  answer: string;
  steps: Step[];
  table: { columns: string[]; rows: (string | number | null)[][] } | null;
  chart: { type: "bar" | "line" | "pie"; x: string; y: string } | null;
  meta: { model?: string | null; tokens?: number | null; ms?: number | null; retries: number };
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function ask(datasetId: string, question: string): Promise<ChatResponse> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, question }),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// รูปแบบข้อมูลต้องตรงกับ docs/CONTRACT.md และ services/api/app/schemas.py

import { clearToken, getToken } from "./auth";

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

export type AuthToken = { access_token: string; token_type: "bearer" };

export type User = { id: string; email: string };

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** error จาก API พร้อมข้อความภาษาไทยจาก `detail` */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function detailMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (status === 422) return "ข้อมูลไม่ถูกต้อง ตรวจอีเมลและรหัสผ่านอีกครั้ง";
  return `เกิดข้อผิดพลาด (${status}) ลองใหม่อีกครั้ง`;
}

/** เรียก API ทุกเส้นผ่านตัวนี้: แนบ token ให้เอง ได้ 401 → ล้าง token แล้วพาไปหน้า login */
async function request<T>(path: string, init: RequestInit = {}, { redirectOn401 = true } = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "ติดต่อเซิร์ฟเวอร์ไม่ได้ ตรวจอินเทอร์เน็ตแล้วลองใหม่");
  }
  const body = await res.json().catch(() => null);
  if (res.status === 401 && redirectOn401) {
    clearToken();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") window.location.assign("/login");
  }
  if (!res.ok) throw new ApiError(res.status, detailMessage(res.status, body));
  return body as T;
}

export async function register(email: string, password: string): Promise<AuthToken> {
  return request("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }, { redirectOn401: false });
}

export async function login(email: string, password: string): Promise<AuthToken> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, { redirectOn401: false });
}

export async function me(): Promise<User> {
  return request("/api/auth/me");
}

export async function ask(datasetId: string, question: string): Promise<ChatResponse> {
  return request("/api/chat", { method: "POST", body: JSON.stringify({ dataset_id: datasetId, question }) });
}

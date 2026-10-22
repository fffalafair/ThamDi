"use client";

// หน้าเข้าสู่ระบบ / สมัคร (P2-04)

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, setToken } from "@/lib/auth";
import { login, register } from "@/lib/api";

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // login อยู่แล้ว → ไปหน้าแชทเลย
  useEffect(() => {
    if (getToken()) router.replace("/");
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await (mode === "login" ? login : register)(email.trim(), password);
      setToken(access_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "เกิดข้อผิดพลาด ลองใหม่อีกครั้ง");
      setLoading(false);
    }
  }

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
  }

  const isLogin = mode === "login";

  return (
    <div className="mx-auto flex min-h-[80vh] w-full max-w-sm flex-col justify-center gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/mascot.svg" alt="น้องเต่าคิว" width={96} height={96} />
        <h1 className="text-2xl font-bold">ถามดิ</h1>
        <p className="text-muted">ถามดิ เดี๋ยวคิวรีให้</p>
      </div>

      <div role="tablist" aria-label="เลือกวิธีเข้าใช้" className="grid grid-cols-2 rounded-xl bg-gray-100 p-1">
        {(["login", "register"] as const).map((m) => (
          <button
            key={m}
            type="button"
            role="tab"
            aria-selected={mode === m}
            onClick={() => switchMode(m)}
            className="min-h-11 rounded-lg font-semibold text-muted aria-selected:bg-white aria-selected:text-ink aria-selected:shadow-sm"
          >
            {m === "login" ? "เข้าสู่ระบบ" : "สมัครสมาชิก"}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-2xl border border-line bg-white p-6" noValidate={false}>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold">อีเมล</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="min-h-11 rounded-lg border border-gray-300 px-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-semibold">รหัสผ่าน</span>
          <input
            type="password"
            required
            minLength={isLogin ? undefined : 8}
            autoComplete={isLogin ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-describedby={isLogin ? undefined : "pw-hint"}
            className="min-h-11 rounded-lg border border-gray-300 px-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {!isLogin && <span id="pw-hint" className="text-xs text-muted">อย่างน้อย 8 ตัวอักษร</span>}
        </label>

        {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="min-h-11 rounded-xl bg-brand px-4 font-semibold text-white disabled:opacity-60"
        >
          {loading ? "กำลังดำเนินการ…" : isLogin ? "เข้าสู่ระบบ" : "สมัครและเข้าใช้งาน"}
        </button>
      </form>

      <p className="text-center text-xs text-muted">
        บัญชีทดลอง: demo@example.com / demo1234
      </p>
    </div>
  );
}

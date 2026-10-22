"use client";

// header + ตรวจว่า login แล้ว (P2-04)
// ทุกหน้ายกเว้น /login: ไม่มี token หรือ token ใช้ไม่ได้ → ไปหน้า login · ระหว่างเช็กไม่แสดงเนื้อหา

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearToken, getToken } from "@/lib/auth";
import { me } from "@/lib/api";

const nav = [
  { href: "/", label: "แชท" },
  { href: "/datasets", label: "ชุดข้อมูล" },
  { href: "/eval", label: "ผลการทดสอบ" },
];

const PUBLIC_PATHS = ["/login"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_PATHS.includes(pathname);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (isPublic) return;
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    me()
      .then((u) => !cancelled && setEmail(u.email))
      .catch(() => {}); // 401 → api.ts พาไปหน้า login เอง
    return () => {
      cancelled = true;
    };
  }, [isPublic, router]);

  function logout() {
    clearToken();
    setEmail(null);
    router.replace("/login");
  }

  if (isPublic) return <main className="mx-auto w-full max-w-6xl p-6">{children}</main>;

  return (
    <>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line bg-white px-6 py-3">
        <Link href="/" className="flex grow items-center gap-2 text-lg font-bold">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/mascot.svg" alt="" width={32} height={32} />
          ถามดิ
        </Link>
        <nav aria-label="เมนูหลัก" className="flex flex-wrap gap-1">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              aria-current={pathname === n.href ? "page" : undefined}
              className="rounded-lg px-3 py-2 text-gray-700 hover:bg-brand-soft hover:text-brand aria-[current=page]:bg-brand-soft aria-[current=page]:font-semibold aria-[current=page]:text-brand"
            >
              {n.label}
            </Link>
          ))}
        </nav>
        {email && (
          <div className="flex items-center gap-2 border-l border-line pl-4">
            <span className="max-w-48 truncate text-sm text-muted" title={email}>{email}</span>
            <button
              type="button"
              onClick={logout}
              className="min-h-11 rounded-lg px-3 text-sm font-semibold text-gray-700 hover:bg-gray-100"
            >
              ออกจากระบบ
            </button>
          </div>
        )}
      </header>
      <main className="mx-auto w-full max-w-6xl p-6">
        {email ? children : <p className="text-muted" role="status">กำลังตรวจสอบการเข้าสู่ระบบ…</p>}
      </main>
    </>
  );
}

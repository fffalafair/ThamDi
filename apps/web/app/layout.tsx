import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

// โหลดฟอนต์ตอนเปิดหน้า ไม่ใช้ next/font/google เพราะตัวนั้นดาวน์โหลดตอน build
// ทำให้ build พังเมื่อเครื่อง build เข้าเน็ตไม่ได้ (เจอจริงตอนตั้งโปรเจกต์)
// ถ้าต้องการฟอนต์แบบ self-host: ใช้ next/font/local แล้วเก็บไฟล์ .woff2 ไว้ใน repo
const FONTS_URL =
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap";

export const metadata: Metadata = {
  title: "ถามดิ (ThamDi)",
  description: "ถามดิ เดี๋ยวคิวรีให้ — ถามข้อมูลจากไฟล์ตารางด้วยภาษาไทย",
};

const nav = [
  { href: "/", label: "แชท" },
  { href: "/datasets", label: "ชุดข้อมูล" },
  { href: "/eval", label: "ผลการทดสอบ" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link rel="stylesheet" href={FONTS_URL} />
      </head>
      <body className="min-h-screen font-sans">
        <header className="flex flex-wrap items-center gap-4 border-b border-line bg-white px-6 py-3">
          <span className="flex grow items-center gap-2 text-lg font-bold">{/* eslint-disable-next-line @next/next/no-img-element */}<img src="/mascot.svg" alt="" width={32} height={32} />ถามดิ</span>
          <nav aria-label="เมนูหลัก" className="flex flex-wrap gap-1">
            {nav.map((n) => (
              <Link key={n.href} href={n.href} className="rounded-lg px-3 py-2 text-gray-700 hover:bg-brand-soft hover:text-brand">
                {n.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl p-6">{children}</main>
      </body>
    </html>
  );
}

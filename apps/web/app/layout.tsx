import type { Metadata } from "next";
import AppShell from "./components/AppShell";
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
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ระบบคลังความรู้การจดทะเบียนภาษีมูลค่าเพิ่ม (VAT Registration RAG) - กรมสรรพากร",
  description: "ระบบ RAG สำหรับเจ้าหน้าที่กรมสรรพากรในการสืบค้นข้อมูลระเบียบและประมวลรัษฎากรเกี่ยวกับการจดทะเบียนภาษีมูลค่าเพิ่ม (NIDA MADT IS Project)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}

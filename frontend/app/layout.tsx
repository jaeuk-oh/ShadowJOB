import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FIELD — AX PM",
  description: "가상 실무 프로젝트로 합격 무기를 만든다",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

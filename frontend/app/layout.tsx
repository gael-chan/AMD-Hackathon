import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Longhand — Auditable Expat Tax Assistant',
  description:
    'FTC vs FEIE for US citizens working in the UK. Python does the math; every number traces to the paragraph that produced it.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="min-h-screen bg-[#F2F5F3] text-[#1E3231] antialiased">{children}</body>
    </html>
  );
}

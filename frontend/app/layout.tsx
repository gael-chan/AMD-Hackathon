import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Provenance — Auditable Expat Tax Assistant',
  description:
    'FTC vs FEIE for US citizens working in the UK. Python does the math; every number traces to the paragraph that produced it.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}

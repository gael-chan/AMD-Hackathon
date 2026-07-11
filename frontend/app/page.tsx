import type { Metadata } from 'next';
import { Lexend } from 'next/font/google';
import Image from 'next/image';
import Link from 'next/link';

import EntrySplash from './EntrySplash';

/*
 * Forest theme landing (user-supplied palette).
 * Palette:
 *   Dust Grey  #F2F5F3  page background
 *   Dry Sage   #A7C4BA  borders, soft chips
 *   Fern       #2E7D6B  highlights, secondary accents
 *   Hunter     #114B4C  primary CTA, strong accents
 *   Pine Teal  #1E3231  primary text, dark surfaces
 */

const lexend = Lexend({ subsets: ['latin'], variable: '--font-forest' });

export const metadata: Metadata = {
  title: 'Longhand | One life. Two tax systems. Zero guesswork.',
  description:
    'Deterministic US and UK tax decisions for American expats. FEIE vs FTC, 14 filing flags, and the exact paragraph of law behind every number.',
};

const CTA = 'Get your estimate';

const btnPrimary =
  'rounded-xl bg-[#114B4C] px-5 py-3 text-sm font-semibold text-[#FAFCFA] transition-colors duration-200 hover:bg-[#1E3231] active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#114B4C]';

export default function ForestLanding() {
  return (
    <>
      <EntrySplash />
      <main className={`${lexend.variable} min-h-screen bg-[#F2F5F3] text-[#1E3231]`}>
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-[#A7C4BA]/50 bg-[#F2F5F3]/90 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center transition-opacity hover:opacity-80">
            <Image src="/longhand-logo-2.png" alt="Longhand" width={114} height={22} priority />
          </Link>
          <div className="hidden items-center gap-8 text-sm text-[#114B4C]/80 md:flex">
            <a href="#how-it-works" className="cursor-pointer transition-colors duration-200 hover:text-[#1E3231]">How it works</a>
            <a href="#pricing" className="cursor-pointer transition-colors duration-200 hover:text-[#1E3231]">Pricing</a>
            <a href="#faq" className="cursor-pointer transition-colors duration-200 hover:text-[#1E3231]">FAQ</a>
          </div>
          <Link href="/app" className={btnPrimary.replace('px-5 py-3', 'px-4 py-2')}>
            {CTA}
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-16 lg:grid-cols-[1.1fr_1fr] lg:pt-24">
        <div>
          <h1 className="text-5xl font-semibold leading-[1.02] tracking-tight [font-family:var(--font-forest)] md:text-6xl">
            One life.
            <br />
            Two tax systems.
            <br />
            <span className="text-[#2E7D6B]">Zero guesswork.</span>
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-[#114B4C]/85">
            Longhand decides FEIE vs FTC, flags all 14 US and UK filings, and shows the law
            behind every number.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="/app" className={btnPrimary}>
              {CTA}
            </Link>
            <a
              href="#how-it-works"
              className="cursor-pointer rounded-xl border border-[#A7C4BA] px-5 py-3 text-sm font-medium text-[#1E3231] transition-colors duration-200 hover:border-[#2E7D6B] active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#114B4C]"
            >
              See how it works
            </a>
          </div>
        </div>
        <div className="flex items-end justify-center">
          <Image
            src="/hero-consultation-2.png"
            alt="A tax adviser walking a client through her return"
            width={608}
            height={303}
            priority
          />
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="text-3xl font-semibold tracking-tight [font-family:var(--font-forest)] md:text-4xl">
          Trusted calculations. Transparent reasoning.
        </h2>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-[#A7C4BA]/60 bg-[#E2EBE6] p-6 shadow-[0_8px_32px_rgba(52,78,65,0.08)]">
            <h3 className="text-lg font-semibold [font-family:var(--font-forest)]">Deterministic engine</h3>
            <p className="mt-3 text-[#114B4C]/85">
              Every figure on your tax return is calculated by a rigorously audited deterministic
              engine. No language model ever touches a number.
            </p>
          </div>
          <div className="rounded-2xl border border-[#A7C4BA]/60 bg-[#E2EBE6] p-6 shadow-[0_8px_32px_rgba(52,78,65,0.08)]">
            <h3 className="text-lg font-semibold [font-family:var(--font-forest)]">Backed by official tax guidance</h3>
            <p className="mt-3 text-[#114B4C]/85">
              Each calculation is linked to the relevant IRS, HMRC, or tax treaty guidance, so you
              can see exactly why a deduction, credit, or liability applies.
            </p>
          </div>
          <div className="rounded-2xl border border-[#A7C4BA]/60 bg-[#E2EBE6] p-6 shadow-[0_8px_32px_rgba(52,78,65,0.08)]">
            <h3 className="text-lg font-semibold [font-family:var(--font-forest)]">Tax explanations in plain English</h3>
            <p className="mt-3 text-[#114B4C]/85">
              Complex tax rules become easy to understand. Highlights the reasoning behind each
              figure, and helps you confidently discuss your return with your accountant or tax
              adviser.
            </p>
          </div>
        </div>
      </section>

      {/* Proof */}
      <section className="border-t border-[#A7C4BA]/50 bg-[#D3E0DA]/50">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <div className="max-w-2xl">
            <h2 className="text-3xl font-semibold tracking-tight [font-family:var(--font-forest)] md:text-4xl">
              Every number defends itself.
            </h2>
            <p className="mt-4 text-lg text-[#114B4C]/85">
              Expand any form line and read the exact paragraph of law that produced it, from the
              wages on Form 1040 line 1h to the credit on Form 1116 line 35.
            </p>
          </div>
          <div className="mt-10 rounded-2xl bg-[#1E3231] p-2 shadow-[0_8px_32px_rgba(52,78,65,0.18)]">
            <Image
              src="/product-why-1040.png"
              alt="Form 1040 line preview with computed amounts and the expanded legal citation for line 1h"
              width={1606}
              height={698}
              className="rounded-xl"
            />
          </div>
        </div>
      </section>

      {/* ISA hook */}
      <section className="mx-auto max-w-3xl px-4 py-20 text-center">
        <h2 className="text-3xl font-semibold tracking-tight [font-family:var(--font-forest)] md:text-4xl">
          Your ISA is not invisible to the IRS.
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-[#114B4C]/85">
          UK platforms call it tax-free. US law calls the funds inside it PFICs and expects Form
          8621. Longhand checks the $25,000 threshold and tells you before a penalty letter does.
        </p>
      </section>

      {/* Problem */}
      <section className="border-t border-[#A7C4BA]/50 bg-[#D3E0DA]/50">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <div className="max-w-3xl">
            <h2 className="text-2xl font-semibold tracking-tight [font-family:var(--font-forest)]">
              Filing in both countries is a $1,500 problem.
            </h2>
            <ul className="mt-6 space-y-5 text-[#1E3231]">
              <li className="flex justify-between gap-6 border-b border-[#A7C4BA]/60 pb-5">
                <span>Consumer tax software refuses complex expat cases outright.</span>
                <span className="shrink-0 font-mono text-[#114B4C]/70">$115+/yr</span>
              </li>
              <li className="flex justify-between gap-6 border-b border-[#A7C4BA]/60 pb-5">
                <span>A specialist accountant works, but the answer is a black box.</span>
                <span className="shrink-0 font-mono text-[#114B4C]/70">$500 to $1,500/yr</span>
              </li>
              <li className="flex justify-between gap-6">
                <span>A generic chatbot is free, confident, and wrong where it counts.</span>
                <span className="shrink-0 font-mono text-[#114B4C]/70">$0</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-b border-t border-[#A7C4BA]/50">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <h2 className="text-3xl font-semibold tracking-tight [font-family:var(--font-forest)] md:text-4xl">
            Priced against the black box.
          </h2>
          <p className="mt-3 text-sm text-[#114B4C]/70">
            Illustrative pricing for the hackathon build. The engine is open source.
          </p>
          <div className="mt-10 grid gap-6 lg:grid-cols-3">
            <div className="rounded-2xl border border-[#A7C4BA]/60 bg-[#E2EBE6] p-6">
              <h3 className="text-lg font-semibold [font-family:var(--font-forest)]">Free</h3>
              <p className="mt-1 text-4xl font-semibold [font-family:var(--font-forest)]">$0</p>
              <p className="mt-1 text-sm text-[#114B4C]/70">The decision, in two minutes.</p>
              <ul className="mt-6 space-y-3 text-sm text-[#1E3231]">
                <li>FEIE vs FTC verdict with reasoning</li>
                <li>All 14 US and UK filing flags</li>
                <li>No signup, nothing stored</li>
              </ul>
              <div className="mt-8">
                <Link
                  href="/app/free"
                  className="block cursor-pointer rounded-xl border border-[#A7C4BA] px-5 py-3 text-center text-sm font-semibold text-[#1E3231] transition-colors duration-200 hover:border-[#2E7D6B] active:translate-y-px"
                >
                  Start free
                </Link>
              </div>
            </div>
            <div className="rounded-2xl border-2 border-[#114B4C] bg-[#E9E7DF] p-6 shadow-[0_8px_32px_rgba(52,78,65,0.14)]">
              <h3 className="text-lg font-semibold text-[#114B4C] [font-family:var(--font-forest)]">Filer</h3>
              <p className="mt-1 text-4xl font-semibold [font-family:var(--font-forest)]">
                $149<span className="text-base font-normal text-[#114B4C]/70">/yr</span>
              </p>
              <p className="mt-1 text-sm text-[#114B4C]/70">Both returns, defended line by line.</p>
              <ul className="mt-6 space-y-3 text-sm text-[#1E3231]">
                <li>Everything in Free</li>
                <li>Full calculation trace</li>
                <li>Line-by-line previews of 13 forms</li>
                <li>Filled PDFs and a filing packet</li>
                <li>Plain-English explanation of every figure</li>
              </ul>
              <div className="mt-8">
                <Link href="/app" className={`${btnPrimary} block text-center`}>
                  {CTA}
                </Link>
              </div>
            </div>
            <div className="rounded-2xl border border-[#A7C4BA]/60 bg-[#E2EBE6] p-6">
              <h3 className="text-lg font-semibold [font-family:var(--font-forest)]">Investor</h3>
              <p className="mt-1 text-4xl font-semibold [font-family:var(--font-forest)]">
                $349<span className="text-base font-normal text-[#114B4C]/70">/yr</span>
              </p>
              <p className="mt-1 text-sm text-[#114B4C]/70">On the roadmap.</p>
              <ul className="mt-6 space-y-3 text-sm text-[#1E3231]">
                <li>Everything in Filer</li>
                <li>PFIC excess-distribution computation</li>
                <li>Brokerage import</li>
                <li>Credit carryforward tracking</li>
              </ul>
              <div className="mt-8">
                <span
                  aria-disabled="true"
                  className="block cursor-not-allowed rounded-xl bg-[#C4C1B5] px-5 py-3 text-center text-sm font-semibold text-[#114B4C]/50"
                >
                  Coming soon
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-3xl px-4 py-20">
        <h2 className="text-3xl font-semibold tracking-tight [font-family:var(--font-forest)] md:text-4xl">Questions</h2>
        <div className="mt-8 divide-y divide-[#A7C4BA]/60 border-y border-[#A7C4BA]/60">
          <details name="faq" className="group py-5">
            <summary className="cursor-pointer list-none font-medium text-[#1E3231] transition-colors duration-200 hover:text-[#2E7D6B]">
              Is this tax advice?
            </summary>
            <p className="mt-3 text-[#114B4C]/85">
              No. Longhand produces deterministic estimates with citations so you can verify
              every step, then review with a professional. It does not file on your behalf.
            </p>
          </details>
          <details name="faq" className="group py-5">
            <summary className="cursor-pointer list-none font-medium text-[#1E3231] transition-colors duration-200 hover:text-[#2E7D6B]">
              Which forms does it cover?
            </summary>
            <p className="mt-3 text-[#114B4C]/85">
              14 filings across the IRS, FinCEN, and HMRC: Form 1040 and Schedules 1, 1-A, 2 and 3,
              Forms 2555, 1116, 8621, 8833 and 8938, the FBAR, and UK SA100, SA106 and SA109.
            </p>
          </details>
          <details name="faq" className="group py-5">
            <summary className="cursor-pointer list-none font-medium text-[#1E3231] transition-colors duration-200 hover:text-[#2E7D6B]">
              Does the AI compute my taxes?
            </summary>
            <p className="mt-3 text-[#114B4C]/85">
              Never. Pure Python computes every figure in exact decimal arithmetic. The language
              model receives finished numbers and citations, and returns only prose.
            </p>
          </details>
          <details name="faq" className="group py-5">
            <summary className="cursor-pointer list-none font-medium text-[#1E3231] transition-colors duration-200 hover:text-[#2E7D6B]">
              What is a PFIC?
            </summary>
            <p className="mt-3 text-[#114B4C]/85">
              A passive foreign investment company. Most UK funds and ETFs, including those inside
              a Stocks and Shares ISA, qualify, and the IRS taxes them punitively unless reported
              on Form 8621.
            </p>
          </details>
          <details name="faq" className="group py-5">
            <summary className="cursor-pointer list-none font-medium text-[#1E3231] transition-colors duration-200 hover:text-[#2E7D6B]">
              Where does my data go?
            </summary>
            <p className="mt-3 text-[#114B4C]/85">
              In the demo build, nowhere. Inputs are processed in memory against the analysis API
              and never stored.
            </p>
          </details>
        </div>
      </section>

      {/* Final CTA */}
      <section className="border-t border-[#A7C4BA]/50 bg-[#1E3231]">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-[#F2F5F3] [font-family:var(--font-forest)] md:text-4xl">
            Know your number in two minutes.
          </h2>
          <div className="mt-8 flex justify-center">
            <Link
              href="/app"
              className="rounded-xl bg-[#A7C4BA] px-5 py-3 text-sm font-semibold text-[#1F2E26] transition-colors duration-200 hover:bg-[#F2F5F3] active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A7C4BA]"
            >
              {CTA}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#A7C4BA]/50">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-10 text-sm text-[#114B4C]/70 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2.5">
            <span aria-hidden className="inline-block h-2 w-2 rotate-45 bg-[#2E7D6B]" />
            <span>Longhand. Built for the AMD Developer Hackathon, July 2026.</span>
          </div>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/gael-chan/AMD-Hackathon"
              target="_blank"
              rel="noreferrer"
              className="cursor-pointer transition-colors duration-200 hover:text-[#1E3231]"
            >
              GitHub
            </a>
            <span>Not tax advice. Estimates for planning only.</span>
          </div>
        </div>
      </footer>
      </main>
    </>
  );
}

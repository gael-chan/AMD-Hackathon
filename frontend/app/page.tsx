'use client';

import { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type TraceStep = {
  step: string;
  formula: string;
  inputs: Record<string, unknown>;
  result: string;
  citation_key: string | null;
};

type RouteResult = {
  route: string;
  eligible: boolean;
  us_tax_owed: number;
  detail: string;
  trace: TraceStep[];
};

type FilingFlag = {
  form: string;
  jurisdiction: string;
  required: boolean;
  reason: string;
  citation_key: string | null;
};

type Citation = {
  key: string;
  source: string;
  reference: string;
  text: string;
  url: string | null;
};

type AnalyzeResponse = {
  feie: RouteResult;
  ftc: RouteResult;
  recommended_route: string;
  recommendation_reason: string;
  us_tax_impact: number;
  filing_flags: FilingFlag[];
  citations: Citation[];
  explanation: string;
  explanation_provider: string;
};

const usd = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

function TraceViewer({ trace, citations }: { trace: TraceStep[]; citations: Citation[] }) {
  return (
    <ol className="mt-3 space-y-2">
      {trace.map((t, i) => {
        const cite = citations.find((c) => c.key === t.citation_key);
        return (
          <li key={i} className="rounded border border-slate-700 bg-slate-900 p-3 text-sm">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-slate-200">
                {i + 1}. {t.step}
              </span>
              <span className="font-mono text-emerald-400">{t.result}</span>
            </div>
            <div className="mt-1 font-mono text-xs text-slate-400">{t.formula}</div>
            <div className="mt-1 font-mono text-xs text-slate-500">
              {Object.entries(t.inputs)
                .map(([k, v]) => `${k}=${v}`)
                .join('  ·  ')}
            </div>
            {cite && (
              <div className="mt-2 border-l-2 border-amber-500 pl-2 text-xs text-amber-200/80">
                {cite.source} — {cite.reference}
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function RouteCard({
  result,
  recommended,
  citations,
}: {
  result: RouteResult;
  recommended: boolean;
  citations: Citation[];
}) {
  const [showTrace, setShowTrace] = useState(false);
  return (
    <div
      className={`rounded-xl border p-5 ${
        recommended ? 'border-emerald-500 bg-emerald-950/30' : 'border-slate-700 bg-slate-900/50'
      }`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {result.route === 'FEIE' ? 'Foreign Earned Income Exclusion' : 'Foreign Tax Credit'}
        </h3>
        {recommended && (
          <span className="rounded-full bg-emerald-500 px-3 py-0.5 text-xs font-bold text-emerald-950">
            RECOMMENDED
          </span>
        )}
      </div>
      {result.eligible ? (
        <p className="mt-2 text-3xl font-bold">{usd(result.us_tax_owed)}</p>
      ) : (
        <p className="mt-2 text-3xl font-bold text-slate-500">Not eligible</p>
      )}
      <p className="mt-2 text-sm text-slate-300">{result.detail}</p>
      <button
        onClick={() => setShowTrace(!showTrace)}
        className="mt-3 text-xs font-medium text-sky-400 hover:text-sky-300"
      >
        {showTrace ? '▾ Hide' : '▸ Show'} calculation trace ({result.trace.length} steps)
      </button>
      {showTrace && <TraceViewer trace={result.trace} citations={citations} />}
    </div>
  );
}

export default function Home() {
  const [form, setForm] = useState({
    uk_salary: '85000',
    uk_tax_paid: '24000',
    filing_status: 'single',
    days_abroad: '340',
    dependents: '0',
    foreign_account_balance: '',
    pfic_holdings_value: '',
    foreign_source_income_or_gains_gbp: '',
    uk_tax_residence: 'full_year_resident',
  });
  const [checks, setChecks] = useState({
    pfic_distribution_or_disposal: false,
    uk_workplace_pension: false,
    uk_non_domiciled: false,
    claims_uk_remittance_basis: false,
  });
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const body: Record<string, unknown> = {
        uk_salary: Number(form.uk_salary),
        uk_tax_paid: Number(form.uk_tax_paid),
        filing_status: form.filing_status,
        days_abroad: Number(form.days_abroad),
        dependents: Number(form.dependents),
        uk_tax_residence: form.uk_tax_residence,
        ...checks,
      };
      if (form.foreign_account_balance !== '') {
        body.foreign_account_balance = Number(form.foreign_account_balance);
      }
      if (form.pfic_holdings_value !== '') {
        body.pfic_holdings_value = Number(form.pfic_holdings_value);
      }
      if (form.foreign_source_income_or_gains_gbp !== '') {
        body.foreign_source_income_or_gains_gbp = Number(form.foreign_source_income_or_gains_gbp);
      }
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  const field =
    'mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none';
  const label = 'block text-xs font-medium uppercase tracking-wide text-slate-400';

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">🧾 Provenance</h1>
        <p className="mt-1 text-slate-400">
          FTC vs FEIE for US citizens working in the UK. Python does the math — every number
          traces back to the paragraph that produced it.
        </p>
      </header>

      <form onSubmit={analyze} className="grid grid-cols-2 gap-4 rounded-xl border border-slate-800 bg-slate-900/50 p-5 md:grid-cols-3">
        <div>
          <label className={label}>UK salary (£)</label>
          <input className={field} type="number" min="0" required value={form.uk_salary} onChange={set('uk_salary')} />
        </div>
        <div>
          <label className={label}>UK tax paid (£)</label>
          <input className={field} type="number" min="0" required value={form.uk_tax_paid} onChange={set('uk_tax_paid')} />
        </div>
        <div>
          <label className={label}>Filing status</label>
          <select className={field} value={form.filing_status} onChange={set('filing_status')}>
            <option value="single">Single</option>
            <option value="married_filing_jointly">Married filing jointly</option>
            <option value="married_filing_separately">Married filing separately</option>
            <option value="head_of_household">Head of household</option>
          </select>
        </div>
        <div>
          <label className={label}>Days abroad</label>
          <input className={field} type="number" min="0" max="366" required value={form.days_abroad} onChange={set('days_abroad')} />
        </div>
        <div>
          <label className={label}>Dependents</label>
          <input className={field} type="number" min="0" value={form.dependents} onChange={set('dependents')} />
        </div>
        <div>
          <label className={label}>Foreign accounts ($, optional)</label>
          <input className={field} type="number" min="0" placeholder="peak balance" value={form.foreign_account_balance} onChange={set('foreign_account_balance')} />
        </div>
        <div>
          <label className={label}>PFIC holdings ($, optional)</label>
          <input className={field} type="number" min="0" placeholder="e.g. funds in a Stocks & Shares ISA" value={form.pfic_holdings_value} onChange={set('pfic_holdings_value')} />
        </div>
        <div>
          <label className={label}>Non-UK income/gains (£, optional)</label>
          <input className={field} type="number" min="0" placeholder="e.g. US brokerage income" value={form.foreign_source_income_or_gains_gbp} onChange={set('foreign_source_income_or_gains_gbp')} />
        </div>
        <div>
          <label className={label}>UK tax residence</label>
          <select className={field} value={form.uk_tax_residence} onChange={set('uk_tax_residence')}>
            <option value="full_year_resident">Full-year UK resident</option>
            <option value="split_year">Split year</option>
            <option value="non_resident">Non-resident</option>
          </select>
        </div>
        <div className="col-span-2 flex flex-wrap gap-x-6 gap-y-2 md:col-span-3">
          {(
            [
              ['uk_workplace_pension', 'UK workplace pension'],
              ['pfic_distribution_or_disposal', 'Sold/received distribution from PFIC'],
              ['uk_non_domiciled', 'Non-UK domiciled'],
              ['claims_uk_remittance_basis', 'Claiming remittance basis'],
            ] as const
          ).map(([key, text]) => (
            <label key={key} className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-600 bg-slate-900 accent-sky-500"
                checked={checks[key]}
                onChange={(e) => setChecks({ ...checks, [key]: e.target.checked })}
              />
              {text}
            </label>
          ))}
        </div>
        <div className="col-span-2 md:col-span-3">
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-sky-600 px-4 py-2.5 font-semibold hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? 'Computing…' : 'Analyze'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 rounded-md border border-red-700 bg-red-950/50 p-4 text-sm text-red-300">
          {error} — is the API running at {API_URL}?
        </div>
      )}

      {result && (
        <section className="mt-8 space-y-6">
          <div className="rounded-xl border border-emerald-600 bg-emerald-950/40 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
              Recommendation
            </p>
            <p className="mt-1 text-2xl font-bold">
              Elect the {result.recommended_route} — estimated US tax {usd(result.us_tax_impact)}
            </p>
            <p className="mt-2 text-sm text-slate-300">{result.recommendation_reason}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <RouteCard result={result.feie} recommended={result.recommended_route === 'FEIE'} citations={result.citations} />
            <RouteCard result={result.ftc} recommended={result.recommended_route === 'FTC'} citations={result.citations} />
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
            <h3 className="text-lg font-semibold">Filing flags</h3>
            {(['US', 'UK'] as const).map((juris) => (
              <div key={juris} className="mt-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {juris === 'US' ? '🇺🇸 US — IRS / FinCEN' : '🇬🇧 UK — HMRC Self Assessment'}
                </p>
                <ul className="mt-2 space-y-2">
                  {result.filing_flags
                    .filter((f) => f.jurisdiction === juris)
                    .map((f) => (
                      <li key={f.form} className="flex items-start gap-3 text-sm">
                        <span
                          className={`mt-0.5 shrink-0 rounded px-2 py-0.5 text-xs font-bold ${
                            f.required ? 'bg-amber-500 text-amber-950' : 'bg-slate-700 text-slate-300'
                          }`}
                        >
                          {f.required ? 'FILE' : 'N/A'}
                        </span>
                        <span>
                          <span className="font-medium">{f.form}</span>
                          <span className="text-slate-400"> — {f.reason}</span>
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Plain-English explanation</h3>
              <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
                {result.explanation_provider}
              </span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
              {result.explanation}
            </p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-5">
            <h3 className="text-lg font-semibold">Citations</h3>
            <ul className="mt-3 space-y-3">
              {result.citations.map((c) => (
                <li key={c.key} className="border-l-2 border-amber-500 pl-3 text-sm">
                  <p className="font-medium text-amber-200">
                    {c.source} — {c.reference}
                  </p>
                  <p className="mt-1 text-slate-400">{c.text}</p>
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-sky-400 hover:underline">
                      {c.url}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <footer className="mt-10 border-t border-slate-800 pt-4 text-xs text-slate-500">
        Demo scope: PAYE-only UK salary, tax year 2024, fixed GBP/USD 1.27. Not tax advice.
      </footer>
    </main>
  );
}

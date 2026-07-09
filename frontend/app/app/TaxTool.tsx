'use client';

import { Fragment, useEffect, useRef, useState } from 'react';

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

type FormLine = {
  line: string;
  label: string;
  value: number | null;
  text_value: string | null;
  citation_key: string | null;
  note: string | null;
};

type FormPreview = {
  form: string;
  tax_year: number;
  lines: FormLine[];
  flows_to: string | null;
  note: string | null;
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
  form_previews: FormPreview[];
  citations: Citation[];
  explanation: string;
  explanation_provider: string;
};

const usd = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

// Forms with a vendored template + field mapping on the backend (see backend/pdf_fill.py)
const SUPPORTED_PDFS = new Set([
  'Form 1040',
  'Form 1116',
  'Form 2555',
  'Schedule 1 (Form 1040)',
  'Schedule 3 (Form 1040)',
]);

const pdfFilename = (form: string) =>
  form.toLowerCase().replace(' (form 1040)', '-1040').replace(/ /g, '-') + '.pdf';

function TraceViewer({ trace, citations }: { trace: TraceStep[]; citations: Citation[] }) {
  return (
    <ol className="mt-3 space-y-2">
      {trace.map((t, i) => {
        const cite = citations.find((c) => c.key === t.citation_key);
        return (
          <li key={i} className="rounded border border-[#A3B18A] bg-[#EFEEE7] p-3 text-sm">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-[#344E41]">
                {i + 1}. {t.step}
              </span>
              <span className="font-mono text-[#3A5A40]">{t.result}</span>
            </div>
            <div className="mt-1 font-mono text-xs text-[#3A5A40]/80">{t.formula}</div>
            <div className="mt-1 font-mono text-xs text-[#3A5A40]/60">
              {Object.entries(t.inputs)
                .map(([k, v]) => `${k}=${v}`)
                .join('  ·  ')}
            </div>
            {cite && (
              <div className="mt-2 border-l-2 border-[#588157] pl-2 text-xs text-[#3A5A40]/80">
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
  traceEnabled,
}: {
  result: RouteResult;
  recommended: boolean;
  citations: Citation[];
  traceEnabled: boolean;
}) {
  const [showTrace, setShowTrace] = useState(false);
  return (
    <div
      className={`rounded-xl border p-5 ${
        recommended ? 'border-[#3A5A40] bg-[#588157]/10' : 'border-[#A3B18A] bg-[#E4E2D8]'
      }`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {result.route === 'FEIE' ? 'Foreign Earned Income Exclusion' : 'Foreign Tax Credit'}
        </h3>
        {recommended && (
          <span className="rounded-full bg-[#3A5A40] px-3 py-0.5 text-xs font-bold text-[#EFEEE7]">
            RECOMMENDED
          </span>
        )}
      </div>
      {result.eligible ? (
        <p className="mt-2 text-3xl font-bold">{usd(result.us_tax_owed)}</p>
      ) : (
        <p className="mt-2 text-3xl font-bold text-[#3A5A40]/60">Not eligible</p>
      )}
      <p className="mt-2 text-sm text-[#344E41]/90">{result.detail}</p>
      {traceEnabled && (
        <>
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="mt-3 text-xs font-medium text-[#588157] hover:text-[#344E41]"
          >
            {showTrace ? '▾ Hide' : '▸ Show'} calculation trace ({result.trace.length} steps)
          </button>
          {showTrace && <TraceViewer trace={result.trace} citations={citations} />}
        </>
      )}
    </div>
  );
}

function FormPreviewTable({
  fp,
  citations,
  onDownload,
}: {
  fp: FormPreview;
  citations?: Citation[];
  onDownload?: () => void;
}) {
  const [openLine, setOpenLine] = useState<string | null>(null);
  const anyCited = !!citations && fp.lines.some((ln) => ln.citation_key);
  return (
    <div className="mt-2 rounded-lg border border-[#A3B18A] bg-[#EFEEE7] p-4">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-xs text-[#3A5A40]/60">
          Deterministic line entries — not a filed return.
          {anyCited && ' Click a cited line to see the law behind it.'}
        </p>
        <span className="flex shrink-0 items-baseline gap-3">
          {onDownload && (
            <button
              onClick={onDownload}
              className="rounded bg-[#3A5A40] px-2.5 py-1 text-xs font-semibold text-[#EFEEE7] hover:bg-[#344E41]"
            >
              Download PDF
            </button>
          )}
          <span className="font-mono text-xs text-[#3A5A40]/60">TY{fp.tax_year}</span>
        </span>
      </div>
      <table className="mt-3 w-full text-sm">
        <tbody>
          {fp.lines.map((ln) => {
            const cite = ln.citation_key && citations
              ? citations.find((c) => c.key === ln.citation_key)
              : undefined;
            const isOpen = openLine === ln.line;
            return (
              <Fragment key={ln.line}>
                <tr
                  className={`border-t border-[#A3B18A]/50 ${
                    cite ? 'cursor-pointer hover:bg-[#DAD7CD]/50' : ''
                  }`}
                  onClick={() => cite && setOpenLine(isOpen ? null : ln.line)}
                >
                  <td className="w-12 py-2 pr-3 align-top font-mono text-[#3A5A40]/80">{ln.line}</td>
                  <td className="py-2 pr-3 align-top text-[#344E41]/90">
                    {ln.label}
                    {cite && <span className="ml-2 text-xs text-[#588157]">{isOpen ? '▾ why' : '▸ why'}</span>}
                    {ln.note && <span className="mt-0.5 block text-xs text-[#3A5A40]/60">{ln.note}</span>}
                  </td>
                  {ln.text_value !== null ? (
                    <td className="max-w-[16rem] py-2 text-right align-top text-xs italic text-[#588157]">
                      {ln.text_value}
                    </td>
                  ) : (
                    <td
                      className={`py-2 text-right align-top font-mono ${
                        ln.value === null ? 'text-[#3A5A40]/60' : 'text-[#3A5A40]'
                      }`}
                    >
                      {ln.value === null
                        ? '—'
                        : ln.value < 0
                          ? `(${Math.abs(ln.value).toLocaleString('en-US', { minimumFractionDigits: 2 })})`
                          : ln.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                  )}
                </tr>
                {isOpen && cite && (
                  <tr className="bg-[#DAD7CD]/40">
                    <td colSpan={3} className="px-3 py-3">
                      <p className="text-xs font-semibold text-[#344E41]">Why this number (line {ln.line})</p>
                      <p className="mt-1 text-xs font-medium text-[#3A5A40]/90">
                        {cite.source} — {cite.reference}
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-[#3A5A40]/80">{cite.text}</p>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      {fp.flows_to && <p className="mt-2 text-xs font-medium text-[#588157]">→ flows to {fp.flows_to}</p>}
      {fp.note && <p className="mt-1 text-xs text-[#3A5A40]/60">{fp.note}</p>}
    </div>
  );
}

function FilingsMasterDetail({
  flags,
  previews,
  citations,
  onDownloadForm,
  onDownloadPacket,
  fetchPdfUrl,
}: {
  flags: FilingFlag[];
  previews: FormPreview[];
  citations: Citation[];
  onDownloadForm: (form: string) => void;
  onDownloadPacket: () => void;
  fetchPdfUrl: (form: string) => Promise<string | null>;
}) {
  const required = flags.filter((f) => f.required);
  const groups = (['US', 'UK'] as const)
    .map((juris) => ({ juris, items: required.filter((f) => f.jurisdiction === juris) }))
    .filter((g) => g.items.length > 0);
  const firstPreviewable =
    required.find((f) => previews.some((p) => p.form === f.form))?.form ?? required[0]?.form ?? null;
  const [selected, setSelected] = useState<string | null>(firstPreviewable);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  const selFlag = required.find((f) => f.form === selected);
  const selPreview = previews.find((p) => p.form === selected);
  const pdfSupported = !!selected && SUPPORTED_PDFS.has(selected);

  useEffect(() => {
    let alive = true;
    setPdfUrl(null);
    if (!selected || !SUPPORTED_PDFS.has(selected)) return;
    setPdfLoading(true);
    fetchPdfUrl(selected).then((url) => {
      if (alive) {
        setPdfUrl(url);
        setPdfLoading(false);
      }
    });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  return (
    <div className="rounded-xl border border-[#A3B18A] bg-[#E4E2D8] p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Required Filings</h3>
        <button
          onClick={onDownloadPacket}
          className="rounded-md bg-[#3A5A40] px-3 py-1.5 text-xs font-semibold text-[#EFEEE7] hover:bg-[#344E41]"
        >
          Download filing packet (ZIP)
        </button>
      </div>
      <div className="mt-4 grid gap-5 lg:grid-cols-[280px_1fr]">
        <div>
          {groups.map(({ juris, items }) => (
            <div key={juris} className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#3A5A40]/70">
                {juris === 'US' ? '🇺🇸 US — IRS / FinCEN' : '🇬🇧 UK — HMRC Self Assessment'}
              </p>
              <ul className="mt-2 space-y-1.5">
                {items.map((f) => {
                  const active = f.form === selected;
                  const hasPreview = previews.some((p) => p.form === f.form);
                  return (
                    <li key={f.form}>
                      <button
                        onClick={() => setSelected(f.form)}
                        className={`w-full cursor-pointer rounded-lg border px-3 py-2 text-left text-sm transition-colors duration-150 ${
                          active
                            ? 'border-[#3A5A40] bg-[#588157]/15 font-semibold'
                            : 'border-[#A3B18A]/60 bg-[#EFEEE7] hover:border-[#588157]'
                        }`}
                      >
                        <span className="flex items-center justify-between gap-2">
                          <span>{f.form}</span>
                          {!hasPreview && <span className="shrink-0 text-[10px] text-[#3A5A40]/60">no preview</span>}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
        <div className="min-w-0">
          {selFlag ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h4 className="text-base font-semibold">{selFlag.form}</h4>
                {pdfSupported && (
                  <button
                    onClick={() => onDownloadForm(selFlag.form)}
                    className="rounded bg-[#3A5A40] px-2.5 py-1 text-xs font-semibold text-[#EFEEE7] hover:bg-[#344E41]"
                  >
                    Download PDF
                  </button>
                )}
              </div>
              <p className="mt-1 text-sm text-[#3A5A40]/80">{selFlag.reason}</p>
              {selPreview ? (
                <FormPreviewTable fp={selPreview} citations={citations} />
              ) : (
                <p className="mt-4 text-sm text-[#3A5A40]/70">
                  No line preview for this filing — see the reason above for what it requires.
                </p>
              )}
              {pdfSupported && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#3A5A40]/70">PDF preview</p>
                  {pdfLoading && <p className="mt-2 text-sm text-[#3A5A40]/70">Generating PDF…</p>}
                  {pdfUrl && (
                    <iframe
                      title={`${selFlag.form} filled PDF preview`}
                      src={`${pdfUrl}#view=FitH`}
                      className="mt-2 h-[560px] w-full rounded-lg border border-[#A3B18A] bg-white"
                    />
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-[#3A5A40]/70">Select a filing to see its detail.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function RequiredFilings({
  flags,
  previews,
  previewsEnabled,
  onDownloadForm,
  onDownloadPacket,
}: {
  flags: FilingFlag[];
  previews: FormPreview[];
  previewsEnabled: boolean;
  onDownloadForm?: (form: string) => void;
  onDownloadPacket?: () => void;
}) {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const required = flags.filter((f) => f.required);
  const groups = (['US', 'UK'] as const)
    .map((juris) => ({ juris, items: required.filter((f) => f.jurisdiction === juris) }))
    .filter((g) => g.items.length > 0);
  return (
    <div className="rounded-xl border border-[#A3B18A] bg-[#E4E2D8] p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Required Filings</h3>
        {previewsEnabled && onDownloadPacket && (
          <button
            onClick={onDownloadPacket}
            className="rounded-md bg-[#3A5A40] px-3 py-1.5 text-xs font-semibold text-[#EFEEE7] hover:bg-[#344E41]"
          >
            Download filing packet (ZIP)
          </button>
        )}
      </div>
      {previewsEnabled && (
        <p className="mt-1 text-xs text-[#3A5A40]/60">Click a form to see its computed line preview.</p>
      )}
      {groups.map(({ juris, items }) => (
        <div key={juris} className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-[#3A5A40]/60">
            {juris === 'US' ? '🇺🇸 US — IRS / FinCEN' : '🇬🇧 UK — HMRC Self Assessment'}
          </p>
          <ul className="mt-2 space-y-2">
            {items.map((f) => {
              const fp = previewsEnabled ? previews.find((p) => p.form === f.form) : undefined;
              const isOpen = !!open[f.form];
              const row = (
                <span className="flex w-full items-start gap-3">
                  <span className="mt-0.5 shrink-0 rounded bg-[#3A5A40] px-2 py-0.5 text-xs font-bold text-[#EFEEE7]">
                    FILE
                  </span>
                  <span>
                    <span className="font-medium">{f.form}</span>
                    {fp && (
                      <span className="ml-2 text-xs font-medium text-[#588157]">
                        {isOpen ? '▾ Hide preview' : '▸ Preview'}
                      </span>
                    )}
                    <span className="block text-[#3A5A40]/80">{f.reason}</span>
                  </span>
                </span>
              );
              return (
                <li key={f.form} className="text-sm">
                  {fp ? (
                    <button
                      type="button"
                      onClick={() => setOpen({ ...open, [f.form]: !isOpen })}
                      className="w-full rounded-md text-left hover:bg-[#DAD7CD]/60"
                    >
                      {row}
                    </button>
                  ) : (
                    row
                  )}
                  {isOpen && fp && (
                    <FormPreviewTable
                      fp={fp}
                      onDownload={
                        onDownloadForm && SUPPORTED_PDFS.has(fp.form)
                          ? () => onDownloadForm(fp.form)
                          : undefined
                      }
                    />
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}

export default function TaxTool({ tier = 'filer' }: { tier?: 'free' | 'filer' }) {
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
  // Profile as submitted for the current result: downloads and PDF previews
  // must reflect the analyzed inputs, not later edits to the form.
  const [analyzedBody, setAnalyzedBody] = useState<Record<string, unknown> | null>(null);
  const [analysisId, setAnalysisId] = useState(0);
  const pdfCache = useRef<Record<string, string>>({});

  async function fetchPdfUrl(formName: string): Promise<string | null> {
    if (pdfCache.current[formName]) return pdfCache.current[formName];
    if (!analyzedBody) return null;
    try {
      const res = await fetch(`${API_URL}/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: analyzedBody, form: formName }),
      });
      if (!res.ok) return null;
      const url = URL.createObjectURL(await res.blob());
      pdfCache.current[formName] = url;
      return url;
    } catch {
      return null;
    }
  }

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  function buildBody(): Record<string, unknown> {
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
    return body;
  }

  async function downloadBlob(path: string, payload: unknown, filename: string) {
    try {
      const res = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Download failed (${res.status})`);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  }

  async function analyze(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const body = buildBody();
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      setResult(await res.json());
      setAnalyzedBody(body);
      Object.values(pdfCache.current).forEach((u) => URL.revokeObjectURL(u));
      pdfCache.current = {};
      setAnalysisId((i) => i + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  const field =
    'mt-1 w-full rounded-md border border-[#A3B18A] bg-[#EFEEE7] px-3 py-2 text-sm focus:border-[#588157] focus:outline-none';
  const label = 'block text-xs font-medium uppercase tracking-wide text-[#3A5A40]/80';

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <header className="mb-8">
        <h1 className="flex items-center gap-3 text-3xl font-bold">
          🧾 Provenance
          {tier === 'free' && (
            <span className="rounded-full border border-[#A3B18A] px-3 py-1 text-xs font-medium text-[#3A5A40]/80">
              Free estimate
            </span>
          )}
        </h1>
        <p className="mt-1 text-[#3A5A40]/80">
          FTC vs FEIE for US citizens working in the UK. Python does the math — every number
          traces back to the paragraph that produced it.
        </p>
      </header>

      <form onSubmit={analyze} className="grid grid-cols-2 gap-4 rounded-xl border border-[#A3B18A]/50 bg-[#E4E2D8] p-5 md:grid-cols-3">
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
            <label key={key} className="flex cursor-pointer items-center gap-2 text-sm text-[#344E41]/90">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-[#A3B18A] bg-[#EFEEE7] accent-[#3A5A40]"
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
            className="w-full rounded-md bg-[#3A5A40] px-4 py-2.5 font-semibold text-[#EFEEE7] hover:bg-[#344E41] disabled:opacity-50"
          >
            {loading ? 'Computing…' : 'Analyze'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 rounded-md border border-red-300 bg-red-100 p-4 text-sm text-red-800">
          {error} — is the API running at {API_URL}?
        </div>
      )}

      {result && (
        <section className="mt-8 space-y-6">
          <div className="rounded-xl border border-[#3A5A40] bg-[#588157]/15 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#3A5A40]">
              Recommendation
            </p>
            <p className="mt-1 text-2xl font-bold">
              Elect the {result.recommended_route} — estimated US tax {usd(result.us_tax_impact)}
            </p>
            <p className="mt-2 text-sm text-[#344E41]/90">{result.recommendation_reason}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <RouteCard result={result.feie} recommended={result.recommended_route === 'FEIE'} citations={result.citations} traceEnabled={tier !== 'free'} />
            <RouteCard result={result.ftc} recommended={result.recommended_route === 'FTC'} citations={result.citations} traceEnabled={tier !== 'free'} />
          </div>

          {tier === 'free' ? (
            <RequiredFilings
              flags={result.filing_flags}
              previews={result.form_previews}
              previewsEnabled={false}
            />
          ) : (
            <FilingsMasterDetail
              key={analysisId}
              flags={result.filing_flags}
              previews={result.form_previews}
              citations={result.citations}
              onDownloadForm={(f) =>
                downloadBlob('/pdf', { profile: analyzedBody ?? buildBody(), form: f }, pdfFilename(f))
              }
              onDownloadPacket={() =>
                downloadBlob('/packet', analyzedBody ?? buildBody(), 'provenance-filing-packet.zip')
              }
              fetchPdfUrl={fetchPdfUrl}
            />
          )}

          {tier === 'free' && (
            <div className="rounded-xl border border-[#3A5A40]/50 bg-[#588157]/10 p-5">
              <h3 className="text-lg font-semibold">This is the free estimate.</h3>
              <p className="mt-2 text-sm text-[#344E41]/90">
                Filer adds the step-by-step calculation trace, line-by-line previews of every
                required form, legal citations for each number, and a plain-English explanation.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <a
                  href="/app"
                  className="rounded-md bg-[#3A5A40] px-4 py-2 text-sm font-semibold text-[#EFEEE7] hover:bg-[#344E41]"
                >
                  Try the full version
                </a>
                <a
                  href="/#pricing"
                  className="rounded-md border border-[#A3B18A] px-4 py-2 text-sm font-medium text-[#344E41]/90 hover:border-[#588157]"
                >
                  See pricing
                </a>
              </div>
            </div>
          )}

          {tier !== 'free' && (
          <>
          <div className="rounded-xl border border-[#A3B18A] bg-[#E4E2D8] p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Plain-English explanation</h3>
              <span className="rounded bg-[#CFCCBE] px-2 py-0.5 font-mono text-xs text-[#3A5A40]/80">
                {result.explanation_provider}
              </span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-[#344E41]/90">
              {result.explanation}
            </p>
          </div>

          <div className="rounded-xl border border-[#A3B18A] bg-[#E4E2D8] p-5">
            <h3 className="text-lg font-semibold">Citations</h3>
            <ul className="mt-3 space-y-3">
              {result.citations.map((c) => (
                <li key={c.key} className="border-l-2 border-[#588157] pl-3 text-sm">
                  <p className="font-medium text-[#3A5A40]">
                    {c.source} — {c.reference}
                  </p>
                  <p className="mt-1 text-[#3A5A40]/80">{c.text}</p>
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-[#588157] hover:underline">
                      {c.url}
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </div>
          </>
          )}
        </section>
      )}

      <footer className="mt-10 border-t border-[#A3B18A]/50 pt-4 text-xs text-[#3A5A40]/60">
        Demo scope: PAYE-only UK salary, single tax year, fixed GBP/USD 1.27. Not tax advice.
      </footer>
    </main>
  );
}

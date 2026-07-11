'use client';

import { Lexend } from 'next/font/google';
import Image from 'next/image';
import Link from 'next/link';
import { Fragment, useEffect, useRef, useState } from 'react';

// Same wordmark font as the landing page (app/page.tsx), instantiated here
// since this is a separate client-component tree.
const lexend = Lexend({ subsets: ['latin'], variable: '--font-forest' });

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

type DependentInfo = {
  first_name: string;
  last_name: string;
  ssn: string;
  relationship: string;
};

type PersonalInfo = {
  first_name: string;
  last_name: string;
  ssn: string;
  street_address: string;
  apt_no: string;
  city: string;
  state: string;
  zip_code: string;
  foreign_country: string;
  foreign_province: string;
  foreign_postal_code: string;
  dependents: DependentInfo[];
};

const EMPTY_PERSONAL: Omit<PersonalInfo, 'dependents'> = {
  first_name: '',
  last_name: '',
  ssn: '',
  street_address: '',
  apt_no: '',
  city: '',
  state: '',
  zip_code: '',
  foreign_country: '',
  foreign_province: '',
  foreign_postal_code: '',
};

const EMPTY_DEPENDENT: DependentInfo = { first_name: '', last_name: '', ssn: '', relationship: '' };

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

// The explanation LLM may bold key figures with **double asterisks** (the only
// markdown it is allowed). Render those as real emphasis instead of literal stars.
const renderEmphasis = (text: string) =>
  text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={i} className="font-semibold text-[#114B4C]">
        {part.slice(2, -2)}
      </strong>
    ) : (
      part
    )
  );

function TraceViewer({ trace, citations }: { trace: TraceStep[]; citations: Citation[] }) {
  return (
    <ol className="mt-3 space-y-2">
      {trace.map((t, i) => {
        const cite = citations.find((c) => c.key === t.citation_key);
        return (
          <li key={i} className="rounded border border-[#A7C4BA] bg-[#FAFCFA] p-3 text-sm">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-[#1E3231]">
                {i + 1}. {t.step}
              </span>
              <span className="font-mono text-[#114B4C]">{t.result}</span>
            </div>
            <div className="mt-1 font-mono text-xs text-[#114B4C]/80">{t.formula}</div>
            <div className="mt-1 font-mono text-xs text-[#114B4C]/60">
              {Object.entries(t.inputs)
                .map(([k, v]) => `${k}=${v}`)
                .join('  ·  ')}
            </div>
            {cite && (
              <div className="mt-2 border-l-2 border-[#2E7D6B] pl-2 text-xs text-[#114B4C]/80">
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
        recommended ? 'border-[#114B4C] bg-[#2E7D6B]/10' : 'border-[#A7C4BA] bg-[#E2EBE6]'
      }`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {result.route === 'FEIE' ? 'Foreign Earned Income Exclusion' : 'Foreign Tax Credit'}
        </h3>
        {recommended && (
          <span className="rounded-full bg-[#114B4C] px-3 py-0.5 text-xs font-bold text-[#FAFCFA]">
            RECOMMENDED
          </span>
        )}
      </div>
      {result.eligible ? (
        <p className="mt-2 text-3xl font-bold">{usd(result.us_tax_owed)}</p>
      ) : (
        <p className="mt-2 text-3xl font-bold text-[#114B4C]/60">Not eligible</p>
      )}
      <p className="mt-2 text-sm text-[#1E3231]/90">{result.detail}</p>
      {traceEnabled && (
        <>
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="mt-3 text-xs font-medium text-[#2E7D6B] hover:text-[#1E3231]"
          >
            {showTrace ? '▾ Hide' : '▸ Show'} calculation trace ({result.trace.length} steps)
          </button>
          {showTrace && <TraceViewer trace={result.trace} citations={citations} />}
        </>
      )}
    </div>
  );
}

const gbp = (n: number) =>
  n.toLocaleString('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 });

function WhatIfPanel({
  baseBody,
  baseSalary,
  baseRoute,
  baseImpact,
}: {
  baseBody: Record<string, unknown>;
  baseSalary: number;
  baseRoute: string;
  baseImpact: number;
}) {
  const [salary, setSalary] = useState(baseSalary);
  const [live, setLive] = useState<{ route: string; impact: number } | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const seqRef = useRef(0);

  useEffect(
    () => () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      seqRef.current += 1; // drop any in-flight response after unmount
    },
    []
  );

  function runScenario(value: number) {
    const seq = ++seqRef.current;
    setLiveLoading(true);
    setLiveError(false);
    fetch(`${API_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...baseBody, uk_salary: value }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`API error ${res.status}`);
        return (await res.json()) as AnalyzeResponse;
      })
      .then((data) => {
        if (seq !== seqRef.current) return;
        setLive({ route: data.recommended_route, impact: data.us_tax_impact });
        setLiveLoading(false);
      })
      .catch(() => {
        if (seq !== seqRef.current) return;
        setLiveError(true);
        setLiveLoading(false);
      });
  }

  const onSlide = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value);
    setSalary(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runScenario(value), 400);
  };

  const shownRoute = live?.route ?? baseRoute;
  const shownImpact = live?.impact ?? baseImpact;
  const delta = shownImpact - baseImpact;
  const higher = delta > 0;

  // Anchor the step grid on baseSalary so the thumb can sit exactly on the
  // analyzed salary (browsers snap range values to min + k*step).
  const halfRange = Math.max(1000, Math.floor((baseSalary * 0.5) / 1000) * 1000);
  const sliderMin = baseSalary - halfRange;
  const sliderMax = baseSalary + halfRange;

  return (
    <div className="rounded-xl border border-[#A7C4BA] bg-[#E2EBE6] p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">What if?</h3>
        {liveLoading && (
          <span className="animate-pulse text-xs font-medium text-[#114B4C]/60">updating…</span>
        )}
      </div>
      <p className="mt-1 text-xs text-[#114B4C]/60">
        Drag to see how the recommendation shifts with your UK salary — your original result above
        stays untouched.
      </p>
      <div className="mt-4">
        <div className="flex items-baseline justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-[#114B4C]/80">
            UK salary
          </span>
          <span className="font-mono text-sm font-semibold text-[#1E3231]">{gbp(salary)}</span>
        </div>
        <input
          type="range"
          min={sliderMin}
          max={sliderMax}
          step={1000}
          value={salary}
          onChange={onSlide}
          aria-label="What-if UK salary"
          className="mt-2 w-full accent-[#114B4C]"
        />
        <div className="flex justify-between font-mono text-xs text-[#114B4C]/60">
          <span>{gbp(sliderMin)}</span>
          <span>{gbp(sliderMax)}</span>
        </div>
        {liveError && (
          <p className="mt-2 text-xs text-red-800">
            Couldn&apos;t compute this scenario — adjust the slider to retry.
          </p>
        )}
      </div>
      <div className="mt-4 flex flex-wrap items-baseline gap-x-8 gap-y-2 rounded-lg border border-[#A7C4BA] bg-[#FAFCFA] p-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">
            Recommended route
          </p>
          <p className="mt-0.5 text-xl font-bold text-[#1E3231]">{shownRoute}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">
            Est. US tax impact
          </p>
          <p className="mt-0.5 text-xl font-bold text-[#1E3231]">{usd(shownImpact)}</p>
        </div>
        <p className={`text-sm font-semibold ${higher ? 'text-amber-700' : 'text-[#2E7D6B]'}`}>
          {delta === 0
            ? 'no change vs your estimate'
            : `${higher ? '+' : '−'}${usd(Math.abs(delta))} vs your estimate`}
        </p>
      </div>
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
    <div className="mt-2 rounded-lg border border-[#A7C4BA] bg-[#FAFCFA] p-4">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-xs text-[#114B4C]/60">
          Deterministic line entries — not a filed return.
          {anyCited && ' Click a cited line to see the law behind it.'}
        </p>
        <span className="flex shrink-0 items-baseline gap-3">
          {onDownload && (
            <button
              onClick={onDownload}
              className="rounded bg-[#114B4C] px-2.5 py-1 text-xs font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
            >
              Download PDF
            </button>
          )}
          <span className="font-mono text-xs text-[#114B4C]/60">TY{fp.tax_year}</span>
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
                  className={`border-t border-[#A7C4BA]/50 ${
                    cite ? 'cursor-pointer hover:bg-[#F2F5F3]/50' : ''
                  }`}
                  onClick={() => cite && setOpenLine(isOpen ? null : ln.line)}
                >
                  <td className="w-12 py-2 pr-3 align-top font-mono text-[#114B4C]/80">{ln.line}</td>
                  <td className="py-2 pr-3 align-top text-[#1E3231]/90">
                    {ln.label}
                    {cite && <span className="ml-2 text-xs text-[#2E7D6B]">{isOpen ? '▾ why' : '▸ why'}</span>}
                    {ln.note && <span className="mt-0.5 block text-xs text-[#114B4C]/60">{ln.note}</span>}
                  </td>
                  {ln.text_value !== null ? (
                    <td className="max-w-[16rem] py-2 text-right align-top text-xs italic text-[#2E7D6B]">
                      {ln.text_value}
                    </td>
                  ) : (
                    <td
                      className={`py-2 text-right align-top font-mono ${
                        ln.value === null ? 'text-[#114B4C]/60' : 'text-[#114B4C]'
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
                  <tr className="bg-[#F2F5F3]/40">
                    <td colSpan={3} className="px-3 py-3">
                      <p className="text-xs font-semibold text-[#1E3231]">Why this number (line {ln.line})</p>
                      <p className="mt-1 text-xs font-medium text-[#114B4C]/90">
                        {cite.source} — {cite.reference}
                      </p>
                      <p className="mt-1 text-xs leading-relaxed text-[#114B4C]/80">{cite.text}</p>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      {fp.flows_to && <p className="mt-2 text-xs font-medium text-[#2E7D6B]">→ flows to {fp.flows_to}</p>}
      {fp.note && <p className="mt-1 text-xs text-[#114B4C]/60">{fp.note}</p>}
    </div>
  );
}

const pField =
  'mt-1 w-full rounded-md border border-[#A7C4BA] bg-[#FAFCFA] px-3 py-2 text-sm focus:border-[#2E7D6B] focus:outline-none';
const pLabel = 'block text-xs font-medium uppercase tracking-wide text-[#114B4C]/80';

function PersonalInfoPanel({
  personal,
  onFieldChange,
  dependentsCount,
  onDependentChange,
  extractBusy,
  extractError,
  onExtract,
  onApply,
}: {
  personal: PersonalInfo;
  onFieldChange: (key: keyof Omit<PersonalInfo, 'dependents'>, value: string) => void;
  dependentsCount: number;
  onDependentChange: (index: number, key: keyof DependentInfo, value: string) => void;
  extractBusy: boolean;
  extractError: string;
  onExtract: (file: File) => void;
  onApply: () => void;
}) {
  const [justApplied, setJustApplied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  useEffect(() => setJustApplied(false), [personal]);

  const handleFiles = (files: FileList | null) => {
    if (files && files[0]) onExtract(files[0]);
  };

  const textField = (key: keyof Omit<PersonalInfo, 'dependents'>, title: string, placeholder = '') => (
    <div>
      <label className={pLabel}>{title}</label>
      <input
        className={pField}
        value={personal[key]}
        placeholder={placeholder}
        onChange={(e) => onFieldChange(key, e.target.value)}
      />
    </div>
  );

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="text-base font-semibold">Personal information</h4>
        <button
          onClick={() => {
            onApply();
            setJustApplied(true);
          }}
          className="rounded bg-[#114B4C] px-2.5 py-1 text-xs font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
        >
          Fill the forms
        </button>
      </div>
      <p className="mt-1 text-sm text-[#114B4C]/80">
        Names, SSN, and address for the form headers. Optional — forms download with these fields
        blank if you skip this.
      </p>
      {justApplied && (
        <p className="mt-2 rounded-md border border-[#2E7D6B]/50 bg-[#2E7D6B]/10 px-3 py-2 text-xs text-[#114B4C]">
          Applied — the PDF previews and downloads now include this information.
        </p>
      )}

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileRef.current?.click()}
        className="mt-4 cursor-pointer rounded-lg border-2 border-dashed border-[#A7C4BA] bg-[#FAFCFA] px-4 py-6 text-center transition-colors hover:border-[#2E7D6B]"
      >
        <p className="text-sm font-medium text-[#1E3231]">
          {extractBusy ? 'Reading document…' : 'Drop a passport or ID photo here, or click to choose'}
        </p>
        <p className="mt-1 text-xs text-[#114B4C]/70">
          A vision model extracts the printed fields for your review. Processed in memory and sent
          to the model provider only for extraction — nothing is stored. It never computes a tax
          number.
        </p>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
      {extractError && (
        <p className="mt-2 rounded-md border border-red-300 bg-red-100 px-3 py-2 text-xs text-red-800">
          {extractError}
        </p>
      )}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {textField('first_name', 'First name')}
        {textField('last_name', 'Last name')}
        {textField('ssn', 'Social security number', '123-45-6789')}
        {textField('street_address', 'Street address')}
        {textField('apt_no', 'Apt no. (optional)')}
        {textField('city', 'City')}
        {textField('foreign_country', 'Country', 'United Kingdom')}
        {textField('foreign_province', 'County / province (optional)')}
        {textField('foreign_postal_code', 'Postcode')}
      </div>

      {dependentsCount > 0 && (
        <div className="mt-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">
            Dependents ({Math.min(dependentsCount, 4)})
          </p>
          {Array.from({ length: Math.min(dependentsCount, 4) }).map((_, i) => {
            const dep = personal.dependents[i] ?? EMPTY_DEPENDENT;
            return (
              <div key={i} className="mt-3 grid gap-3 rounded-lg border border-[#A7C4BA]/60 bg-[#FAFCFA] p-3 sm:grid-cols-4">
                {(
                  [
                    ['first_name', 'First name'],
                    ['last_name', 'Last name'],
                    ['ssn', 'SSN'],
                    ['relationship', 'Relationship'],
                  ] as const
                ).map(([key, title]) => (
                  <div key={key}>
                    <label className={pLabel}>{title}</label>
                    <input
                      className={pField}
                      value={dep[key]}
                      onChange={(e) => onDependentChange(i, key, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            );
          })}
          {dependentsCount > 4 && (
            <p className="mt-2 text-xs text-[#114B4C]/70">
              Form 1040 lists four dependents on the face of the return; additional dependents
              attach on a statement.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

const PERSONAL_KEY = '__personal__';

function FilingsMasterDetail({
  flags,
  previews,
  citations,
  onDownloadForm,
  onDownloadPacket,
  fetchPdfUrl,
  personalPanel,
  version = 0,
}: {
  flags: FilingFlag[];
  previews: FormPreview[];
  citations: Citation[];
  onDownloadForm: (form: string) => void;
  onDownloadPacket: () => void;
  fetchPdfUrl: (form: string) => Promise<string | null>;
  personalPanel?: React.ReactNode;
  version?: number;
}) {
  const required = flags.filter((f) => f.required);
  // US: required forms only. UK: always list all SA forms — the not-required
  // ones render greyed out so the "why not" reasoning stays visible.
  const groups = (['US', 'UK'] as const)
    .map((juris) => {
      const all = flags.filter((f) => f.jurisdiction === juris);
      const items =
        juris === 'UK'
          ? [...all.filter((f) => f.required), ...all.filter((f) => !f.required)]
          : all.filter((f) => f.required);
      return { juris, items };
    })
    .filter((g) => g.items.length > 0);
  const firstPreviewable =
    required.find((f) => previews.some((p) => p.form === f.form))?.form ?? required[0]?.form ?? null;
  const [selected, setSelected] = useState<string | null>(firstPreviewable);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  const selFlag = flags.find((f) => f.form === selected);
  const pdfSupported = !!selected && !!selFlag?.required && SUPPORTED_PDFS.has(selected);
  const selPreview = selFlag?.required ? previews.find((p) => p.form === selected) : undefined;

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
  }, [selected, version]);

  return (
    <div className="rounded-xl border border-[#A7C4BA] bg-[#E2EBE6] p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Required Filings</h3>
        <button
          onClick={onDownloadPacket}
          className="rounded-md bg-[#114B4C] px-3 py-1.5 text-xs font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
        >
          Download filing packet (ZIP)
        </button>
      </div>
      <div className="mt-4 grid gap-5 lg:grid-cols-[280px_1fr]">
        <div>
          {personalPanel && (
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">
                Your details
              </p>
              <ul className="mt-2">
                <li>
                  <button
                    onClick={() => setSelected(PERSONAL_KEY)}
                    className={`w-full cursor-pointer rounded-lg border px-3 py-2 text-left text-sm transition-colors duration-150 ${
                      selected === PERSONAL_KEY
                        ? 'border-[#114B4C] bg-[#2E7D6B]/15 font-semibold'
                        : 'border-[#A7C4BA]/60 bg-[#FAFCFA] hover:border-[#2E7D6B]'
                    }`}
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span>Personal information</span>
                      <span className="shrink-0 text-[10px] text-[#114B4C]/60">names, SSN, address</span>
                    </span>
                  </button>
                </li>
              </ul>
            </div>
          )}
          {groups.map(({ juris, items }) => (
            <div key={juris} className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">
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
                            ? 'border-[#114B4C] bg-[#2E7D6B]/15 font-semibold'
                            : f.required
                              ? 'border-[#A7C4BA]/60 bg-[#FAFCFA] hover:border-[#2E7D6B]'
                              : 'border-[#A7C4BA]/40 bg-transparent text-[#1E3231]/45 hover:border-[#A7C4BA] hover:text-[#1E3231]/70'
                        }`}
                      >
                        <span className="flex items-center justify-between gap-2">
                          <span>{f.form}</span>
                          {!f.required ? (
                            <span className="shrink-0 text-[10px] uppercase tracking-wide text-[#114B4C]/45">not needed</span>
                          ) : (
                            !hasPreview && <span className="shrink-0 text-[10px] text-[#114B4C]/60">no preview</span>
                          )}
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
          {selected === PERSONAL_KEY && personalPanel ? (
            personalPanel
          ) : selFlag ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h4 className="text-base font-semibold">{selFlag.form}</h4>
                {!selFlag.required && (
                  <span className="rounded-full border border-[#A7C4BA] px-3 py-0.5 text-xs font-semibold text-[#114B4C]/60">
                    Not required for this profile
                  </span>
                )}
                {pdfSupported && (
                  <button
                    onClick={() => onDownloadForm(selFlag.form)}
                    className="rounded bg-[#114B4C] px-2.5 py-1 text-xs font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
                  >
                    Download PDF
                  </button>
                )}
              </div>
              <p className="mt-1 text-sm text-[#114B4C]/80">{selFlag.reason}</p>
              {selPreview ? (
                <FormPreviewTable fp={selPreview} citations={citations} />
              ) : !selFlag.required ? (
                <p className="mt-4 text-sm text-[#114B4C]/70">
                  Nothing to file here — the reason above explains why, and what would change that.
                </p>
              ) : (
                <p className="mt-4 text-sm text-[#114B4C]/70">
                  No line preview for this filing — see the reason above for what it requires.
                </p>
              )}
              {pdfSupported && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/70">PDF preview</p>
                  {pdfLoading && <p className="mt-2 text-sm text-[#114B4C]/70">Generating PDF…</p>}
                  {pdfUrl && (
                    <iframe
                      title={`${selFlag.form} filled PDF preview`}
                      src={`${pdfUrl}#view=FitH`}
                      className="mt-2 h-[560px] w-full rounded-lg border border-[#A7C4BA] bg-white"
                    />
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-[#114B4C]/70">Select a filing to see its detail.</p>
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
  // US: required forms only. UK: always list all SA forms — not-required ones
  // render greyed out so the "why not" reasoning stays visible.
  const groups = (['US', 'UK'] as const)
    .map((juris) => {
      const all = flags.filter((f) => f.jurisdiction === juris);
      const items =
        juris === 'UK'
          ? [...all.filter((f) => f.required), ...all.filter((f) => !f.required)]
          : all.filter((f) => f.required);
      return { juris, items };
    })
    .filter((g) => g.items.length > 0);
  return (
    <div className="rounded-xl border border-[#A7C4BA] bg-[#E2EBE6] p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Required Filings</h3>
        {previewsEnabled && onDownloadPacket && (
          <button
            onClick={onDownloadPacket}
            className="rounded-md bg-[#114B4C] px-3 py-1.5 text-xs font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
          >
            Download filing packet (ZIP)
          </button>
        )}
      </div>
      {previewsEnabled && (
        <p className="mt-1 text-xs text-[#114B4C]/60">Click a form to see its computed line preview.</p>
      )}
      {groups.map(({ juris, items }) => (
        <div key={juris} className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]/60">
            {juris === 'US' ? '🇺🇸 US — IRS / FinCEN' : '🇬🇧 UK — HMRC Self Assessment'}
          </p>
          <ul className="mt-2 space-y-2">
            {items.map((f) => {
              const fp = previewsEnabled && f.required ? previews.find((p) => p.form === f.form) : undefined;
              const isOpen = !!open[f.form];
              const row = (
                <span className={`flex w-full items-start gap-3 ${f.required ? '' : 'opacity-55'}`}>
                  {f.required ? (
                    <span className="mt-0.5 shrink-0 rounded bg-[#114B4C] px-2 py-0.5 text-xs font-bold text-[#FAFCFA]">
                      FILE
                    </span>
                  ) : (
                    <span className="mt-0.5 shrink-0 rounded border border-[#A7C4BA] px-2 py-0.5 text-xs font-bold text-[#114B4C]/60">
                      SKIP
                    </span>
                  )}
                  <span>
                    <span className="font-medium">{f.form}</span>
                    {fp && (
                      <span className="ml-2 text-xs font-medium text-[#2E7D6B]">
                        {isOpen ? '▾ Hide preview' : '▸ Preview'}
                      </span>
                    )}
                    <span className="block text-[#114B4C]/80">{f.reason}</span>
                  </span>
                </span>
              );
              return (
                <li key={f.form} className="text-sm">
                  {fp ? (
                    <button
                      type="button"
                      onClick={() => setOpen({ ...open, [f.form]: !isOpen })}
                      className="w-full rounded-md text-left hover:bg-[#F2F5F3]/60"
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
    uk_salary: '',
    uk_tax_paid: '',
    filing_status: 'single',
    days_abroad: '',
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
  // Identity block for form headers. `personal` is the live draft; only the
  // applied snapshot ever reaches a PDF, so half-typed values never leak in.
  const [personal, setPersonal] = useState<PersonalInfo>({ ...EMPTY_PERSONAL, dependents: [] });
  const [appliedPersonal, setAppliedPersonal] = useState<PersonalInfo | null>(null);
  const [pdfVersion, setPdfVersion] = useState(0);
  const [extractBusy, setExtractBusy] = useState(false);
  const [extractError, setExtractError] = useState('');

  const depCount = analyzedBody ? Number(analyzedBody.dependents ?? 0) : 0;

  function setPersonalField(key: keyof Omit<PersonalInfo, 'dependents'>, value: string) {
    setPersonal((p) => ({ ...p, [key]: value }));
  }

  function setDependentField(index: number, key: keyof DependentInfo, value: string) {
    setPersonal((p) => {
      const deps = [...p.dependents];
      while (deps.length <= index) deps.push({ ...EMPTY_DEPENDENT });
      deps[index] = { ...deps[index], [key]: value };
      return { ...p, dependents: deps };
    });
  }

  function clearPdfCache() {
    Object.values(pdfCache.current).forEach((u) => URL.revokeObjectURL(u));
    pdfCache.current = {};
  }

  function applyPersonal() {
    setAppliedPersonal({
      ...personal,
      dependents: personal.dependents.slice(0, Math.min(depCount, 4)),
    });
    clearPdfCache();
    setPdfVersion((v) => v + 1);
  }

  async function extractFromDocument(file: File) {
    setExtractBusy(true);
    setExtractError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API_URL}/extract-identity`, { method: 'POST', body: fd });
      if (!res.ok) {
        const detail = (await res.json().catch(() => null))?.detail;
        throw new Error(detail || `Extraction failed (${res.status})`);
      }
      const fields: Record<string, string> = await res.json();
      setPersonal((p) => ({
        ...p,
        ...Object.fromEntries(Object.entries(fields).filter(([, v]) => v)),
      }));
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Extraction failed');
    } finally {
      setExtractBusy(false);
    }
  }

  async function fetchPdfUrl(formName: string): Promise<string | null> {
    if (pdfCache.current[formName]) return pdfCache.current[formName];
    if (!analyzedBody) return null;
    try {
      const res = await fetch(`${API_URL}/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile: analyzedBody,
          form: formName,
          personal: appliedPersonal ?? undefined,
        }),
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
      // empty input falls back to the greyed placeholder default
      uk_salary: Number(form.uk_salary || 200000),
      uk_tax_paid: Number(form.uk_tax_paid || 60000),
      filing_status: form.filing_status,
      days_abroad: Number(form.days_abroad || 340),
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
    'mt-1 w-full rounded-md border border-[#A7C4BA] bg-[#FAFCFA] px-3 py-2 text-sm focus:border-[#2E7D6B] focus:outline-none';
  const label = 'block text-xs font-medium uppercase tracking-wide text-[#114B4C]/80';

  return (
    <main className={`${lexend.variable} mx-auto max-w-4xl px-4 py-10`}>
      <header className="mb-8">
        <h1 className="flex items-center gap-3 text-3xl font-bold">
          <Link href="/" className="transition-opacity hover:opacity-75">
            <Image src="/longhand-logo-2.png" alt="Longhand" width={150} height={29} priority />
          </Link>
          {tier === 'free' && (
            <span className="rounded-full border border-[#A7C4BA] px-3 py-1 text-xs font-medium text-[#114B4C]/80">
              Free estimate
            </span>
          )}
        </h1>
        <p className="mt-1 text-[#114B4C]/80">
          FTC vs FEIE for US citizens working in the UK. Python does the math — every number
          traces back to the paragraph that produced it.
        </p>
      </header>

      <form onSubmit={analyze} className="grid grid-cols-2 gap-4 rounded-xl border border-[#A7C4BA]/50 bg-[#E2EBE6] p-5 md:grid-cols-3">
        <div>
          <label className={label}>UK salary (£)</label>
          <input
            className={field}
            type="number"
            min="0"
            placeholder="200000"
            value={form.uk_salary}
            onChange={set('uk_salary')}
          />
        </div>
        <div>
          <label className={label}>UK tax paid (£)</label>
          <input className={field} type="number" min="0" placeholder="60000" value={form.uk_tax_paid} onChange={set('uk_tax_paid')} />
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
          <input className={field} type="number" min="0" max="366" placeholder="340" value={form.days_abroad} onChange={set('days_abroad')} />
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
            <label key={key} className="flex cursor-pointer items-center gap-2 text-sm text-[#1E3231]/90">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-[#A7C4BA] bg-[#FAFCFA] accent-[#114B4C]"
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
            className="w-full rounded-md bg-[#114B4C] px-4 py-2.5 font-semibold text-[#FAFCFA] hover:bg-[#1E3231] disabled:opacity-50"
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
          <div className="rounded-xl border border-[#114B4C] bg-[#2E7D6B]/15 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#114B4C]">
              Recommendation
            </p>
            <p className="mt-1 text-2xl font-bold">
              Elect the {result.recommended_route} — estimated US tax {usd(result.us_tax_impact)}
            </p>
            <p className="mt-2 text-sm text-[#1E3231]/90">{result.recommendation_reason}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <RouteCard result={result.feie} recommended={result.recommended_route === 'FEIE'} citations={result.citations} traceEnabled={tier !== 'free'} />
            <RouteCard result={result.ftc} recommended={result.recommended_route === 'FTC'} citations={result.citations} traceEnabled={tier !== 'free'} />
          </div>

          {tier !== 'free' && analyzedBody && (
            <WhatIfPanel
              key={`whatif-${analysisId}`}
              baseBody={analyzedBody}
              baseSalary={Number(analyzedBody?.uk_salary ?? (form.uk_salary || 200000))}
              baseRoute={result.recommended_route}
              baseImpact={result.us_tax_impact}
            />
          )}

          {tier === 'free' ? (
            <RequiredFilings
              flags={result.filing_flags}
              previews={result.form_previews}
              previewsEnabled={false}
            />
          ) : (
            <FilingsMasterDetail
              key={`filings-${analysisId}`}
              flags={result.filing_flags}
              previews={result.form_previews}
              citations={result.citations}
              onDownloadForm={(f) =>
                downloadBlob(
                  '/pdf',
                  {
                    profile: analyzedBody ?? buildBody(),
                    form: f,
                    personal: appliedPersonal ?? undefined,
                  },
                  pdfFilename(f)
                )
              }
              onDownloadPacket={() =>
                downloadBlob(
                  '/packet',
                  {
                    profile: analyzedBody ?? buildBody(),
                    personal: appliedPersonal ?? undefined,
                  },
                  'longhand-filing-packet.zip'
                )
              }
              fetchPdfUrl={fetchPdfUrl}
              version={pdfVersion}
              personalPanel={
                <PersonalInfoPanel
                  personal={personal}
                  onFieldChange={setPersonalField}
                  dependentsCount={depCount}
                  onDependentChange={setDependentField}
                  extractBusy={extractBusy}
                  extractError={extractError}
                  onExtract={extractFromDocument}
                  onApply={applyPersonal}
                />
              }
            />
          )}

          {tier === 'free' && (
            <div className="rounded-xl border border-[#114B4C]/50 bg-[#2E7D6B]/10 p-5">
              <h3 className="text-lg font-semibold">This is the free estimate.</h3>
              <p className="mt-2 text-sm text-[#1E3231]/90">
                Filer adds the step-by-step calculation trace, line-by-line previews of every
                required form, legal citations for each number, and a plain-English explanation.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <a
                  href="/app"
                  className="rounded-md bg-[#114B4C] px-4 py-2 text-sm font-semibold text-[#FAFCFA] hover:bg-[#1E3231]"
                >
                  Try the full version
                </a>
                <a
                  href="/#pricing"
                  className="rounded-md border border-[#A7C4BA] px-4 py-2 text-sm font-medium text-[#1E3231]/90 hover:border-[#2E7D6B]"
                >
                  See pricing
                </a>
              </div>
            </div>
          )}

          {tier !== 'free' && (
          <>
          <div className="rounded-xl border border-[#A7C4BA] bg-[#E2EBE6] p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Plain-English explanation</h3>
              <span className="rounded bg-[#D3E0DA] px-2 py-0.5 font-mono text-xs text-[#114B4C]/80">
                {result.explanation_provider}
              </span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-[#1E3231]/90">
              {renderEmphasis(result.explanation)}
            </p>
          </div>

          <div className="rounded-xl border border-[#A7C4BA] bg-[#E2EBE6] p-5">
            <h3 className="text-lg font-semibold">Citations</h3>
            <ul className="mt-3 space-y-3">
              {result.citations.map((c) => (
                <li key={c.key} className="border-l-2 border-[#2E7D6B] pl-3 text-sm">
                  <p className="font-medium text-[#114B4C]">
                    {c.source} — {c.reference}
                  </p>
                  <p className="mt-1 text-[#114B4C]/80">{c.text}</p>
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-[#2E7D6B] hover:underline">
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

      <footer className="mt-10 border-t border-[#A7C4BA]/50 pt-4 text-xs text-[#114B4C]/60">
        Demo scope: PAYE-only UK salary, single tax year, fixed GBP/USD 1.27. Not tax advice.
      </footer>
    </main>
  );
}

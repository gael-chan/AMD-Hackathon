<div align="center">

# 🧾 Provenance

### AI reads the tax law. Python does the math. Every number traces back to the exact paragraph that produced it.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![AMD MI300X](https://img.shields.io/badge/AMD-MI300X-ED1C24?style=flat&logo=amd&logoColor=white)](https://www.amd.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

**Built for AMD Developer Hackathon: ACT II · Unicorn Track · July 2026**

[Demo](#quick-start) · [Architecture](#architecture) · [Data Model](docs/Erd.png) · [Full ERD Pack](docs/provenance_erd_v3_professional_pack.pdf)

</div>

---

## The Problem

~300,000 US citizens live and work in the UK. Every year they face a decision that can swing their US tax bill by **thousands of dollars**: claim the Foreign Earned Income Exclusion (FEIE) or the Foreign Tax Credit (FTC)?

Today's options:

| Option | Cost | Problem |
|---|---|---|
| TurboTax / H&R Block | $115–320/yr | Refuses complex expat cases |
| Human accountant | $500–1,500+/yr | Black box — "trust me" |
| Generic AI chatbot | Free | Hallucinates numbers, no audit trail |

**Nobody can answer "prove this number is right" with anything better than reputation. Provenance fixes that.**

---

## What We Built

A deterministic, auditable tax assistant for PAYE salaried US expats in the UK.

| You provide | Provenance returns |
|---|---|
| UK salary (£) | FEIE vs FTC comparison — exact figures |
| UK tax paid (£) | Recommended route + estimated US tax impact |
| Filing status | 14 US & UK filing flags — see [Forms Coverage](#forms-coverage) |
| Days abroad | Deterministic line-by-line form previews |
| Dependents · foreign accounts | Cited IRS / HMRC / US–UK treaty paragraphs |
| ISA / PFIC holdings · pension | Full calculation trace + plain-English AI explanation |

### What makes this different

| Other tools | Provenance |
|---|---|
| LLM calculates the numbers | **Python calculates. LLM only explains.** |
| "Here's your answer" | Every number traces to the exact law paragraph |
| Black box output | Full step-by-step calculation trace, always visible |
| Generic advice | Flags the exact forms you need to file |

> **Core architectural law:** The LLM never touches numbers. Deterministic Python functions run all tax math. The LLM receives pre-computed results + pre-fetched citations and returns plain English only. Break this rule and the audit claim dies.

---

## Forms Coverage

Every form gets a **flag** (required or not, with a cited reason). Most also get a **preview** — the exact line entries, computed deterministically with verbatim captions from the official form. The demo chain (Form 1040, 1116, 2555, Schedules 1 & 3) also downloads as **filled official PDFs** — generated in memory from vendored blank templates and never stored, individually or as a ZIP packet with a provenance manifest. Form structures track the newest official revisions — including the brand-new Schedule 1-A and the UK's post-remittance-basis FIG-regime pages. A preview line shows **"—"** whenever the amount needs data outside demo scope: the engine never prints a number it didn't compute.

### 🇺🇸 US — IRS / FinCEN

| Form | What it is | Flag | Line preview |
|---|---|:---:|:---:|
| **Form 1040** | The core return — wages (line 1h, no W-2), AGI, tax, credits, total tax | ✅ always | ✅ full⁰ |
| **Form 2555** | FEIE election — income chain, cap, exclusion → Schedule 1 | ✅ | ✅ full |
| **Form 1116** | Foreign Tax Credit — §904 limitation chain → Schedule 3 | ✅ | ✅ full |
| **Schedule 1** (1040) | FEIE exclusion entered as negative on line 8d | ✅ | ✅ full |
| **Schedule 2** (1040) | Additional taxes — §1291 PFIC tax lands here | ✅ | ◐ partial¹ |
| **Schedule 3** (1040) | FTC credit claimed on line 1 | ✅ | ✅ full |
| **Schedule 1-A** (1040) | Tips/overtime/car-loan/senior deductions — the newest 1040 schedule | ✅² | —² |
| **Form 8621** | PFIC information return — **the Stocks & Shares ISA trap** | ✅ | ◐ partial³ |
| **Form 8833** | Treaty-based position disclosure (Article 18 pension deferral) | ✅ | ✅ text template |
| **Form 8938** | FATCA statement of foreign financial assets | ✅ | ◐ partial⁴ |
| **FBAR** (FinCEN 114) | Foreign account report — e-filed with FinCEN, not the IRS | ✅ | — |

### 🇬🇧 UK — HMRC Self Assessment

| Form | What it is | Flag | Line preview |
|---|---|:---:|:---:|
| **SA100** | Main Self Assessment return — TR2 supplementary-page answers | ✅ | ✅ |
| **SA106** | Foreign pages — non-UK income + Foreign Tax Credit Relief | ✅ | ◐ partial⁵ |
| **SA109** | Residence, domicile & FIG regime pages | ✅ | ◐ partial⁶ |

⁰ Line 17 (AMT/excess-APTC) assumed zero rather than evaluated — stated on the line itself; line 16 under FEIE uses the stacking-rule worksheet.
¹ NIIT/AMT not evaluated; Additional Medicare Tax deterministically $0 via the US–UK Totalization Agreement.
² Brand-new schedule — the flag explains from which tax year it first applies; its line preview activates once multi-year support lands.
³ Value-range checkbox and §1291-fund default computed; Part V is fully deterministic ($0) when no distribution occurred, honest-blank when one did (needs distribution history).
⁴ Summary value + Part IV count of Forms 8621 (FATCA duplicate-reporting exception); per-account detail not collected.
⁵ Income row computed; FTCR columns need the US withholding amount.
⁶ Residence boxes computed; flags the remittance-basis → FIG regime transition (abolished 6 April 2025) for non-dom profiles.

---

## Architecture

![Provenance System Architecture](docs/Architecture.png)

The system has three strictly separated layers:

**1. Deterministic Engine** — Pure Python, `Decimal` arithmetic, zero LLM involvement. Computes FEIE exclusion, FTC credit, US tax liability, and filing flags. Every function returns its result alongside the citation key that justifies it.

**2. Citation Layer** — Curated IRS/HMRC/treaty snippets retrieved by citation key. No vector DB, no embeddings — hand-picked for reliability over breadth.

**3. Explanation Layer** — AMD MI300X receives pre-computed numbers + pre-fetched citations. Returns plain-English explanation only. Fireworks AI is the fallback if AMD is unavailable.

---

## Data Model

![Provenance ERD v4](docs/Erd.png)

Four domain bands: **Knowledge Base** · **Deterministic Engine** · **Users & Filings** · **Operations (Roadmap)**

The demo audit story spine:
```
tax_profiles → filings → code_versions → filing_citations → tax_rules → source_documents
```
Every output number traces through this chain to the source paragraph.

→ [Full modular ERD + relationship catalogue](docs/provenance_erd_v3_professional_pack.pdf)

---

## Design Decisions

| Decision | What we chose | Why |
|---|---|---|
| LLM role | Explanation only | Hallucinated tax numbers are a liability, not a feature |
| RAG approach | Curated snippets, not bulk ingestion | 6 reliable citations beat 600 uncertain ones for a demo |
| FX rate | Fixed GBP/USD 1.27 constant | Live FX adds failure points with zero demo value |
| Database | None in MVP | Filing persistence is roadmap; the audit trail is in the trace |
| Auth | None in MVP | Single-session demo; users table is roadmap |
| Tax year | 2024 constants hardcoded | Parameterising years adds complexity with no demo upside |

---

## Demo Scope (July 11)

**In scope:**

- PAYE UK salary earner only
- Single tax year per analysis — form previews track the newest official form revisions
- FTC vs FEIE election comparison
- 14 US & UK filing flags + deterministic form previews ([Forms Coverage](#forms-coverage))
- PFIC/ISA detection (Form 8621), treaty disclosure (8833), FATCA (8938), UK Self Assessment (SA100/106/109)
- Plain-English LLM explanation with cited paragraphs
- Full calculation trace visible in UI

**Out of scope — not built, not promised:**

- Self-employment / freelance income
- Multi-year carryforward
- PFIC §1291 excess-distribution tax math (Form 8621 is flagged & previewed; the deferred-tax computation needs distribution history)
- Actually filing the forms
- LLM chat / Q&A loop
- Live FX rates

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| API | FastAPI + Pydantic v2 |
| Calculation | Pure Python · `Decimal` arithmetic · no floats |
| Citation RAG | Curated dict — IRS / HMRC / US–UK treaty snippets |
| LLM (primary) | AMD MI300X via AMD Developer Cloud |
| LLM (fallback) | Fireworks AI — `accounts/fireworks/models/gpt-oss-120b` |
| Frontend | Next.js 14 + Tailwind CSS |
| Deployment | Docker Compose |

---

## Quick Start

```bash
git clone https://github.com/V-Vekaria/AMD-Hackathon
cd AMD-Hackathon
cp .env.example .env        # add your AMD + Fireworks keys (optional — degrades gracefully)
docker compose up --build
```

Frontend → http://localhost:3000  
API docs → http://localhost:8000/docs

**Without Docker:**
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

**Run the engine test suite** (109 tests: hand-computed bracket goldens, stacking-rule and §904 scenarios, threshold boundary pins, and cross-form consistency invariants swept over a profile grid):
```bash
cd backend && pytest tests -q
```

**Test the API directly:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "uk_salary": 85000,
    "uk_tax_paid": 24000,
    "filing_status": "single",
    "days_abroad": 340,
    "dependents": 0,
    "foreign_account_balance_over_10k": false
  }'
```

---

## Repo Structure

```
provenance/
├── backend/
│   ├── main.py            # FastAPI — /analyze endpoint
│   ├── models.py          # Pydantic schemas
│   ├── tax_engine.py      # deterministic FEIE/FTC calculator + filing flags
│   ├── snippets.py        # curated IRS/HMRC/treaty citations
│   ├── forms/             # deterministic line-by-line form previews
│   │   ├── form2555.py    #   FEIE election      → Schedule 1
│   │   ├── form1116.py    #   Foreign Tax Credit → Schedule 3
│   │   ├── form8621.py    #   PFIC (the ISA trap)
│   │   ├── form8833.py    #   treaty disclosure (Art. 18 pension)
│   │   ├── form8938.py    #   FATCA
│   │   ├── schedule1.py … schedule3.py, schedule1a.py
│   │   └── sa100.py, sa106.py, sa109.py   # UK Self Assessment
│   ├── llm/
│   │   └── client.py      # AMD MI300X + Fireworks fallback
│   ├── tests/             # pytest: golden math, boundaries, cross-form invariants
│   └── requirements.txt
├── frontend/              # Next.js — form + result card + trace viewer
├── docs/
│   ├── Architecture.png   # system architecture diagram
│   ├── Erd.png            # data model (single image)
│   └── provenance_erd_v3_professional_pack.pdf
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── README.md
```

---

## Environment Variables

```bash
# .env.example — all keys optional; with none set the API returns the
# deterministic trace summary instead of an LLM explanation
AMD_API_KEY=your_amd_key_here
AMD_MODEL_ENDPOINT=https://your-amd-endpoint/v1/chat/completions   # OpenAI-compatible
FIREWORKS_API_KEY=your_fireworks_key_here
GBP_USD_RATE=1.27
```

---

## Market

| | |
|---|---|
| US citizens in the UK | ~200–300K |
| US citizens abroad (total addressable) | ~9M |
| Current cheapest option | $115/yr — and it refuses complex cases |
| Current human option | $500–1,500+/yr |

UK is the wedge market. The policy-to-code architecture extends to any dual-filing jurisdiction pair — Canada, Australia, Germany — with zero changes to the engine core.

---

## Roadmap

- [ ] Persistent filing history (tax_profiles + filings tables)
- [ ] User auth + subscription
- [ ] Policy-change alerts mapped to your specific filing
- [x] PFIC detection + Form 8621 flag & preview (§1291 tax math still to come)
- [ ] Form 8621 §1291 excess-distribution computation (needs distribution history intake)
- [x] Fill the official PDFs — demo chain done (1040, 1116, 2555, Schedules 1 & 3; per-form download + ZIP packet with provenance manifest)
- [ ] PDF filling for the disclosure forms (8621/8833/8938) and UK SA pages (HMRC PDFs are print-only — needs coordinate overlay)
- [ ] Brokerage CSV import
- [ ] Multi-year carryforward tracking
- [ ] What-if simulator (FTC vs FEIE with salary scenarios)
- [ ] Jurisdiction #2 via swappable module pack — same engine, new rules file
- [ ] E-file integrations (IRS MeF, HMRC-recognised software)

---

## Team

· Gael · [Vishnu Vekaria](https://github.com/V-Vekaria)

---

*AMD Developer Hackathon: ACT II · Unicorn Track · lablab.ai × AMD × NativelyAI · July 2026*

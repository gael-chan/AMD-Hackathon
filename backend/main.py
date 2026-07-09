"""Provenance API — FastAPI app exposing POST /analyze and PDF downloads."""
import io
import logging
import zipfile
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm.client import explain
from models import AnalyzeResponse, TaxProfile
from pdf_fill import fill_form, supported_forms
from tax_engine import GBP_USD_RATE, analyze

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Provenance",
    description="Auditable FTC vs FEIE analysis for US citizens working in the UK. "
    "Deterministic Python computes every number; the LLM only explains.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo scope; lock down post-hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_profile(profile: TaxProfile) -> AnalyzeResponse:
    # 1. Deterministic engine computes everything (numbers, flags, citations).
    result = analyze(profile)
    # 2. LLM explains the already-computed result — it never calculates.
    explanation, provider = await explain(result.model_dump())
    result.explanation = explanation
    result.explanation_provider = provider
    return result


class PdfRequest(BaseModel):
    profile: TaxProfile
    form: str


def _safe_filename(form: str) -> str:
    return form.lower().replace(" (form 1040)", "-1040").replace(" ", "-") + ".pdf"


@app.post("/pdf")
async def download_pdf(req: PdfRequest) -> Response:
    """Fill the official template for one required form. Generated in memory,
    streamed to the client, never stored."""
    if req.form not in supported_forms():
        raise HTTPException(404, f"No PDF template for {req.form}")
    result = analyze(req.profile)
    preview = next((fp for fp in result.form_previews if fp.form == req.form), None)
    if preview is None:
        raise HTTPException(404, f"{req.form} is not part of this profile's filings")
    pdf = fill_form(preview, req.profile)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(req.form)}"'},
    )


@app.post("/packet")
async def download_packet(profile: TaxProfile) -> Response:
    """Zip every supported filled form for this profile plus a provenance
    manifest. In-memory only."""
    result = analyze(profile)
    fillable = [fp for fp in result.form_previews if fp.form in supported_forms()]
    if not fillable:
        raise HTTPException(404, "No fillable forms for this profile")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in fillable:
            zf.writestr(_safe_filename(fp.form), fill_form(fp, profile))
        manifest = "\n".join([
            "Provenance filing packet",
            f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            f"Recommended route: {result.recommended_route}",
            f"Estimated US tax: ${result.us_tax_impact:,.2f}",
            f"FX rate (fixed demo): GBP/USD {GBP_USD_RATE}",
            "Calculation constants: tax year 2024; templates: 2025 form revisions.",
            f"Forms included: {', '.join(fp.form for fp in fillable)}",
            "Deterministic engine output - no LLM touched any number. Not tax advice.",
        ])
        zf.writestr("manifest.txt", manifest)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="provenance-filing-packet.zip"'},
    )

"""Longhand API — FastAPI app exposing POST /analyze and PDF downloads."""
import io
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load backend/.env before any module reads os.environ at import time
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, File, HTTPException, Response, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from llm.client import answer_question, explain  # noqa: E402
from llm.extract import extract_identity  # noqa: E402
from models import AnalyzeResponse, PersonalInfo, TaxProfile  # noqa: E402
from pdf_fill import fill_form, supported_forms  # noqa: E402
from tax_engine import GBP_USD_RATE, analyze  # noqa: E402

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Longhand",
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


class AskRequest(BaseModel):
    question: str
    explanation: str
    history: list[dict] = []


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    """Grounded Q&A about an already-generated explanation. The LLM may only
    restate what the explanation says — it never calculates. The 3-question
    quota is enforced client-side (demo scope)."""
    if len(req.question) > 500:
        raise HTTPException(413, "Question too long (500 characters max)")
    answer, provider = await answer_question(req.question, req.explanation, req.history)
    return {"answer": answer, "provider": provider}


class PdfRequest(BaseModel):
    profile: TaxProfile
    form: str
    personal: Optional[PersonalInfo] = None


class PacketRequest(BaseModel):
    profile: TaxProfile
    personal: Optional[PersonalInfo] = None


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
    pdf = fill_form(preview, req.profile, req.personal)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_safe_filename(req.form)}"'},
    )


@app.post("/packet")
async def download_packet(req: PacketRequest) -> Response:
    """Zip every supported filled form for this profile plus a provenance
    manifest. In-memory only."""
    profile = req.profile
    result = analyze(profile)
    fillable = [fp for fp in result.form_previews if fp.form in supported_forms()]
    if not fillable:
        raise HTTPException(404, "No fillable forms for this profile")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in fillable:
            zf.writestr(_safe_filename(fp.form), fill_form(fp, profile, req.personal))
        manifest = "\n".join([
            "Longhand filing packet",
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
        headers={"Content-Disposition": 'attachment; filename="longhand-filing-packet.zip"'},
    )


@app.post("/extract-identity")
async def extract_identity_endpoint(file: UploadFile = File(...)) -> dict:
    """Extract name/address fields from an uploaded ID document image using a
    vision LLM. The image is processed in memory and sent to the model
    provider for extraction only — never stored. The user reviews every
    extracted value before it touches a form (the LLM still never computes
    a tax number)."""
    raw = await file.read()
    if len(raw) > 8_000_000:
        raise HTTPException(413, "Image too large (8 MB max)")
    fields = await extract_identity(raw, file.content_type or "image/jpeg")
    if fields is None:
        raise HTTPException(
            503,
            "No vision model configured — set FIREWORKS_API_KEY in backend/.env to enable extraction.",
        )
    return fields

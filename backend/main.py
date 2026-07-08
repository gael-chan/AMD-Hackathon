"""Provenance API — FastAPI app exposing POST /analyze."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm.client import explain
from models import AnalyzeResponse, TaxProfile
from tax_engine import analyze

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

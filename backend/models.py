"""Pydantic schemas for the /analyze endpoint."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FilingStatus(str, Enum):
    single = "single"
    married_filing_jointly = "married_filing_jointly"
    married_filing_separately = "married_filing_separately"
    head_of_household = "head_of_household"


class TaxProfile(BaseModel):
    uk_salary: float = Field(..., ge=0, description="Gross UK salary in GBP")
    uk_tax_paid: float = Field(..., ge=0, description="UK income tax paid via PAYE, in GBP")
    filing_status: FilingStatus = FilingStatus.single
    days_abroad: int = Field(..., ge=0, le=366, description="Days physically outside the US in the tax year")
    dependents: int = Field(0, ge=0, description="Number of qualifying-child dependents")
    foreign_account_balance: Optional[float] = Field(
        None, ge=0, description="Peak aggregate foreign account balance in USD (optional; drives FBAR/8938 flags)"
    )
    foreign_account_balance_over_10k: Optional[bool] = Field(
        None, description="Set true if aggregate foreign accounts exceeded $10,000 (used when exact balance not given)"
    )


class TraceStep(BaseModel):
    step: str
    formula: str
    inputs: dict
    result: str
    citation_key: Optional[str] = None


class RouteResult(BaseModel):
    route: str  # "FEIE" or "FTC"
    eligible: bool
    us_tax_owed: float
    detail: str
    trace: list[TraceStep]


class FilingFlag(BaseModel):
    form: str
    required: bool
    reason: str
    citation_key: Optional[str] = None


class Citation(BaseModel):
    key: str
    source: str
    reference: str
    text: str
    url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    feie: RouteResult
    ftc: RouteResult
    recommended_route: str
    recommendation_reason: str
    us_tax_impact: float
    filing_flags: list[FilingFlag]
    citations: list[Citation]
    explanation: str
    explanation_provider: str  # "amd" | "fireworks" | "deterministic-fallback"

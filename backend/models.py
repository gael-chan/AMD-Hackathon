"""Pydantic schemas for the /analyze endpoint."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FilingStatus(str, Enum):
    single = "single"
    married_filing_jointly = "married_filing_jointly"
    married_filing_separately = "married_filing_separately"
    head_of_household = "head_of_household"


class UkResidenceStatus(str, Enum):
    full_year_resident = "full_year_resident"
    split_year = "split_year"
    non_resident = "non_resident"


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
    uk_tax_residence: UkResidenceStatus = Field(
        UkResidenceStatus.full_year_resident, description="UK tax residence position for the year (drives SA109)"
    )
    uk_non_domiciled: bool = Field(False, description="Claiming non-UK domicile status (drives SA109)")
    claims_uk_remittance_basis: bool = Field(False, description="Electing the remittance basis of UK taxation (drives SA109)")
    foreign_source_income_or_gains_gbp: Optional[float] = Field(
        None, ge=0,
        description="Non-UK-source income/gains taxable in the UK requiring Foreign Tax Credit Relief, e.g. "
        "US brokerage income or US withholding on RSUs (drives SA106)",
    )
    pfic_holdings_value: Optional[float] = Field(
        None, ge=0,
        description="Year-end aggregate value in USD of PFIC holdings — e.g. UK-domiciled funds/ETFs inside a "
        "Stocks & Shares ISA (drives Form 8621)",
    )
    pfic_distribution_or_disposal: bool = Field(
        False, description="Received a distribution from, or sold shares of, a PFIC during the year (drives Form 8621)"
    )
    uk_workplace_pension: bool = Field(
        False, description="Contributes to a UK workplace pension and relies on treaty Article 18 to defer US tax "
        "on pension growth (drives Form 8833)"
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
    jurisdiction: str = "US"  # "US" | "UK"
    required: bool
    reason: str
    citation_key: Optional[str] = None


class FormLine(BaseModel):
    line: str  # e.g. "8d"
    label: str  # exact caption from the official form
    value: Optional[float] = None  # None = form line applies but amount is outside demo scope
    text_value: Optional[str] = None  # for disclosure forms whose entries are text, not amounts
    citation_key: Optional[str] = None
    note: Optional[str] = None


class FormPreview(BaseModel):
    form: str  # e.g. "Schedule 1 (Form 1040)"
    tax_year: int
    lines: list[FormLine]
    flows_to: Optional[str] = None  # where the bottom line lands
    note: Optional[str] = None  # scope caveats for this form


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
    form_previews: list[FormPreview] = []
    citations: list[Citation]
    explanation: str
    explanation_provider: str  # "amd" | "fireworks" | "deterministic-fallback"

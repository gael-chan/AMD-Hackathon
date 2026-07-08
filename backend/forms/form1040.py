"""Form 1040 — U.S. Individual Income Tax Return, tax year 2024.

The core return every other preview flows into. Fully deterministic for
demo scope with two stated assumptions carried on the lines themselves:
line 17 (AMT/excess-APTC) is assumed zero rather than evaluated, and line
16 under FEIE uses the Foreign Earned Income Tax Worksheet (stacking rule),
not the plain bracket amount. UK wages have no Form W-2, so they enter on
line 1h, not 1a. Captions quoted from the official form (2024 structure:
single line 11 AGI).
"""
from decimal import Decimal
from typing import Optional

from models import FilingStatus, FormLine, FormPreview

TAX_YEAR = 2024

_STATUS_LABEL = {
    FilingStatus.single: "Single",
    FilingStatus.married_filing_jointly: "Married filing jointly",
    FilingStatus.married_filing_separately: "Married filing separately",
    FilingStatus.head_of_household: "Head of household",
}


def build_form_1040(
    route: str,
    filing_status: FilingStatus,
    income_usd: Decimal,
    standard_deduction: Decimal,
    schedule_1_amount: Decimal,  # negative FEIE exclusion, or 0 when FTC route
    line_16_tax: Decimal,  # stacked-rate tax (FEIE) or bracket tax (FTC), before credits
    ctc_applied: Decimal,
    schedule_3_credit: Decimal,  # FTC credit, or 0 when FEIE route
    pfic_distribution_pending: bool,
) -> FormPreview:
    """Line entries for the core return, mirroring the engine's route result."""
    total_income = income_usd + schedule_1_amount  # schedule_1_amount <= 0
    agi = total_income
    taxable = max(Decimal("0"), agi - standard_deduction)
    line_22 = max(Decimal("0"), line_16_tax - ctc_applied - schedule_3_credit)
    line_23: Optional[Decimal] = None if pfic_distribution_pending else Decimal("0")
    line_24 = None if line_23 is None else line_22 + line_23

    lines = [
        FormLine(
            line="status",
            label="Filing Status",
            text_value=_STATUS_LABEL[filing_status],
        ),
        FormLine(
            line="1a",
            label="Total amount from Form(s) W-2, box 1",
            value=0.0,
            note="No W-2 — a UK employer does not issue one; the salary belongs on line 1h.",
        ),
        FormLine(
            line="1h",
            label="Other earned income. Enter type and amount",
            value=float(income_usd),
            citation_key="form_1040_core",
            note='Type: "Foreign wages — UK PAYE employment (no W-2)".',
        ),
        FormLine(
            line="1z",
            label="Add lines 1a through 1h",
            value=float(income_usd),
        ),
        FormLine(
            line="8",
            label="Additional income from Schedule 1, line 10",
            value=float(schedule_1_amount),
            citation_key="schedule_1_2555" if schedule_1_amount < 0 else None,
            note="The Form 2555 exclusion arrives here as a negative amount." if schedule_1_amount < 0
            else "Schedule 1 not required on the FTC route in demo scope.",
        ),
        FormLine(
            line="9",
            label="Add lines 1z, 2b, 3b, 4b, 5b, 6b, 7, and 8. This is your total income",
            value=float(total_income),
        ),
        FormLine(
            line="11",
            label="Subtract line 10 from line 9. This is your adjusted gross income",
            value=float(agi),
            note="No Schedule 1 Part II adjustments in demo scope.",
        ),
        FormLine(
            line="12",
            label="Standard deduction or itemized deductions (from Schedule A)",
            value=float(standard_deduction),
        ),
        FormLine(
            line="15",
            label="Subtract line 14 from line 11. If zero or less, enter -0-. This is your taxable income",
            value=float(taxable),
        ),
        FormLine(
            line="16",
            label="Tax (see instructions)",
            value=float(line_16_tax),
            citation_key="pub54_stacking" if route == "FEIE" else "form_1040_core",
            note="Foreign Earned Income Tax Worksheet (stacking rule) — not the plain bracket amount."
            if route == "FEIE" else
            "Computed from the 2024 rate schedule; the IRS tax tables ($50 ranges) can differ by a "
            "few dollars below $100,000 taxable income.",
        ),
        FormLine(
            line="17",
            label="Amount from Schedule 2, line 3",
            value=0.0,
            note="AMT and excess-APTC repayment assumed zero — not evaluated in demo scope.",
        ),
        FormLine(
            line="19",
            label="Child tax credit or credit for other dependents from Schedule 8812",
            value=float(ctc_applied),
            note=None if ctc_applied > 0 else "No qualifying-child dependents reported.",
        ),
        FormLine(
            line="20",
            label="Amount from Schedule 3, line 8",
            value=float(schedule_3_credit),
            citation_key="schedule_3_ftc" if schedule_3_credit > 0 else None,
            note="The Form 1116 foreign tax credit arrives here." if schedule_3_credit > 0
            else "Schedule 3 not required on the FEIE route in demo scope.",
        ),
        FormLine(
            line="22",
            label="Subtract line 21 from line 18. If zero or less, enter -0-",
            value=float(line_22),
        ),
        FormLine(
            line="23",
            label="Other taxes, including self-employment tax, from Schedule 2, line 21",
            value=None if line_23 is None else 0.0,
            citation_key="form_8621_pfic" if line_23 is None else None,
            note="Pending — the §1291 tax from Form 8621 lands here once computed (distribution "
            "history required)." if line_23 is None else
            "No self-employment tax (PAYE employee); UK wages FICA-exempt under the Totalization Agreement.",
        ),
        FormLine(
            line="24",
            label="Add lines 22 and 23. This is your total tax",
            value=None if line_24 is None else float(line_24),
            citation_key="form_1040_core",
            note="Cannot be totaled until line 23 is computed." if line_24 is None else None,
        ),
    ]
    return FormPreview(
        form="Form 1040",
        tax_year=TAX_YEAR,
        lines=lines,
        flows_to=None,
        note="The core return — every schedule and election form above attaches to it. No US "
        "withholding or estimated payments collected in demo scope, so line 37 (amount you owe) "
        "equals line 24. 2024 line structure (single line 11 AGI).",
    )

"""SA106 — UK Self Assessment Foreign pages (2026 form, year to 5 April 2026).

Page F 2 'Income from overseas sources' columns for the reported non-UK
income. Amounts are in UK pounds (the engine's foreign_source_income field
is already GBP). The foreign-tax-taken-off column and the Foreign Tax
Credit Relief claim need the US withholding amount, which is not collected,
so they stay honest-blank. Captions quoted from the official form.
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2026  # UK tax year 6 April 2025 - 5 April 2026


def build_sa106(foreign_income_gbp: Decimal) -> FormPreview:
    """Page F 2 row for the aggregate non-UK-source income (GBP)."""
    return FormPreview(
        form="SA106 (Foreign)",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="F2.A",
                label="Country or territory code",
                text_value="USA",
                note="Demo scope assumes the non-UK income is US-source (e.g. US brokerage or RSU income).",
            ),
            FormLine(
                line="F2.B",
                label="Amount of income arising or received before any tax taken off",
                value=float(foreign_income_gbp),
                citation_key="sa106_foreign",
                note="All entries in UK pounds (£). Aggregate across sources; use a separate row per "
                "source/country when filing.",
            ),
            FormLine(
                line="F2.C",
                label="Foreign tax taken off or paid",
                value=None,
                note="US withholding on this income not collected in demo scope.",
            ),
            FormLine(
                line="F2.E",
                label="To claim Foreign Tax Credit Relief — put 'X' in the box",
                value=None,
                note="Claim only if foreign tax was actually withheld (column C) — check the US-UK "
                "treaty limit for the relief rate.",
            ),
            FormLine(
                line="2",
                label="If you're calculating your tax, enter the total Foreign Tax Credit Relief on your income",
                value=None,
                citation_key="sa106_foreign",
                note="Not computed — requires column C and the Helpsheet 263 working sheet.",
            ),
        ],
        flows_to="SA100 (attached as the Foreign supplementary pages)",
        note="UK tax year 2025-26 (2026 form as supplied); the TY2024 US computation corresponds to "
        "the 2024-25 UK return. Amounts in GBP.",
    )

"""Form 2555 — Foreign Earned Income (the FEIE election), tax year 2024.

Nearly fully deterministic: the engine already computes the income and the
exclusion. Demo-scope assumptions surfaced on the lines themselves: the
qualifying 12-month period is assumed to span the whole tax year (so the
line 39 ratio is 1.000 and the cap is not prorated), and there is no
employer-provided housing, so Part VI is zero. Captions quoted from the
official form; the maximum-exclusion amount is the 2024 figure ($126,500 —
the 2025 revision of the form shows $130,000).
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2024
DAYS_IN_2024 = 366  # leap year


def build_form_2555(income_usd: Decimal, excluded: Decimal, cap: Decimal, days_abroad: int) -> FormPreview:
    """Line entries for Form 2555 when the FEIE is elected."""
    income = float(income_usd)
    return FormPreview(
        form="Form 2555",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="16",
                label="The physical presence test is based on the 12-month period from ... through ...",
                text_value=None,
                value=None,
                note=f"Exact period dates not collected — {days_abroad} days abroad reported, which "
                "satisfies the 330-day requirement. Enter the qualifying 12-month window before filing.",
            ),
            FormLine(
                line="17",
                label="Enter your principal country of employment during your tax year",
                text_value="United Kingdom",
                citation_key="irc_911_feie",
            ),
            FormLine(
                line="19",
                label="Total wages, salaries, bonuses, commissions, etc.",
                value=income,
                note="UK PAYE salary converted at the fixed demo rate.",
            ),
            FormLine(
                line="26",
                label="Subtract line 25 from line 24. This is your foreign earned income",
                value=income,
                note="Lines 20-23 and 25 are zero in demo scope (no non-cash income, allowances, or deferrals).",
            ),
            FormLine(
                line="27",
                label="Enter the amount from line 26",
                value=income,
            ),
            FormLine(
                line="37",
                label="Maximum foreign earned income exclusion",
                value=float(cap),
                citation_key="irc_911_feie",
                note="Tax year 2024 limit ($126,500). The 2025 revision of the form shows $130,000.",
            ),
            FormLine(
                line="38",
                label="Enter the number of days in your qualifying period that fall within your tax year",
                text_value=str(DAYS_IN_2024),
                note="Assumes the qualifying 12-month period spans the entire tax year.",
            ),
            FormLine(
                line="39",
                label="If line 38 and the number of days in your tax year are the same, enter \"1.000\"",
                text_value="1.000",
            ),
            FormLine(
                line="40",
                label="Multiply line 37 by line 39",
                value=float(cap),
                note="No proration — full-year qualifying period.",
            ),
            FormLine(
                line="41",
                label="Subtract line 36 from line 27",
                value=income,
                note="Line 36 (housing exclusion) is zero in demo scope.",
            ),
            FormLine(
                line="42",
                label="Foreign earned income exclusion. Enter the smaller of line 40 or line 41",
                value=float(excluded),
                citation_key="irc_911_feie",
            ),
            FormLine(
                line="45",
                label="Subtract line 44 from line 43. Enter the result here and on Schedule 1 (Form 1040), line 8d",
                value=float(excluded),
                citation_key="schedule_1_2555",
                note="Line 44 (deductions allocable to excluded income) is zero in demo scope.",
            ),
        ],
        flows_to="Schedule 1 (Form 1040), line 8d",
        note="Parts I-III general information (address, employer, travel table) not collected in demo "
        "scope. Part VI (housing exclusion) is zero — no employer-provided housing amounts reported.",
    )

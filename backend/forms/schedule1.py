"""Schedule 1 (Form 1040) — Additional Income and Adjustments to Income, tax year 2024.

Demo scope (PAYE salaried expat electing FEIE) touches exactly three Part I
lines: the Form 2555 exclusion enters on line 8d as a negative, totals through
line 9, and lands on line 10, which flows to Form 1040 line 8. Lines 1-7 and
all of Part II are zero for this profile. Line captions are quoted verbatim
from the official 2024 form.
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_schedule_1(feie_excluded_usd: Decimal) -> FormPreview:
    """Line entries for Schedule 1 when the FEIE is elected.

    feie_excluded_usd: the exclusion computed by the engine (positive Decimal);
    entered on the form as a negative per the line 8d instruction.
    """
    exclusion_entry = float(-feie_excluded_usd)
    return FormPreview(
        form="Schedule 1 (Form 1040)",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="8d",
                label="Foreign earned income exclusion from Form 2555",
                value=exclusion_entry,
                citation_key="schedule_1_2555",
                note="Entered as a negative amount (in parentheses on the printed form).",
            ),
            FormLine(
                line="9",
                label="Total other income. Add lines 8a through 8z",
                value=exclusion_entry,
                note="Lines 8a-8c and 8e-8z are zero in demo scope.",
            ),
            FormLine(
                line="10",
                label="Add lines 1 through 7 and 9. This is your additional income. "
                "Enter here and on Form 1040, 1040-SR, or 1040-NR, line 8",
                value=exclusion_entry,
                citation_key="schedule_1_2555",
                note="Lines 1-7 are zero in demo scope (PAYE salary only).",
            ),
        ],
        flows_to="Form 1040, line 8",
        note="Part II (Adjustments to Income) is zero in demo scope; line 25 flows $0.00 to Form 1040, line 10.",
    )

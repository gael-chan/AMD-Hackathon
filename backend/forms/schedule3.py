"""Schedule 3 (Form 1040) — Additional Credits and Payments, tax year 2024.

Demo scope (FTC route) touches two Part I lines: the Form 1116 foreign tax
credit enters on line 1 and totals through line 8 onto Form 1040 line 20.
Lines 2-7 and all of Part II are zero for a PAYE salaried expat. Line
captions are quoted verbatim from the official 2024 form.
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_schedule_3(ftc_credit_usd: Decimal) -> FormPreview:
    """Line entries for Schedule 3 when the FTC is elected.

    ftc_credit_usd: the credit computed by the engine — UK tax paid capped at
    the §904 limitation, so it never exceeds gross US tax.
    """
    credit = float(ftc_credit_usd)
    return FormPreview(
        form="Schedule 3 (Form 1040)",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="1",
                label="Foreign tax credit. Attach Form 1116 if required",
                value=credit,
                citation_key="schedule_3_ftc",
                note="UK PAYE income tax, capped at the §904 limitation (Form 1116, line 21).",
            ),
            FormLine(
                line="8",
                label="Add lines 1 through 4, 5a, 5b, and 7. Enter here and on Form 1040, "
                "1040-SR, or 1040-NR, line 20",
                value=credit,
                citation_key="schedule_3_ftc",
                note="Lines 2-7 are zero in demo scope.",
            ),
        ],
        flows_to="Form 1040, line 20",
        note="Part II (Other Payments and Refundable Credits) is zero in demo scope.",
    )

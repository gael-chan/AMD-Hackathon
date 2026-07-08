"""Form 1116 — Foreign Tax Credit (the FTC election), tax year 2024.

Nearly fully deterministic in demo scope: all income is foreign-source
general-category UK wages, so every ratio on the form is 1.0000 and the
standard deduction allocates fully against foreign income. The §904
limitation (line 21) therefore equals gross US tax, and the credit is the
smaller of that and UK tax paid. Captions quoted from the official form
(2025 revision; line structure unchanged from 2024).
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_form_1116(
    income_usd: Decimal,
    standard_deduction: Decimal,
    gross_tax: Decimal,
    uk_tax_usd: Decimal,
    credit: Decimal,
) -> FormPreview:
    """Line entries for Form 1116 when the FTC is elected.

    The §904 limitation equals gross_tax because the foreign/total income
    ratio is 1 in demo scope; credit = min(uk_tax_usd, limitation).
    """
    taxable = income_usd - standard_deduction
    if taxable < 0:
        taxable = Decimal("0")
    excess = uk_tax_usd - gross_tax
    lines = [
        FormLine(
            line="cat.",
            label="Use a separate Form 1116 for each category of income — check only one box",
            text_value="(d) General category income — resident of United Kingdom",
            citation_key="irc_901_ftc",
            note="UK employment wages are general-category income; column A country: United Kingdom.",
        ),
        FormLine(
            line="1a",
            label="Gross income from sources within country shown above and of the type checked above",
            value=float(income_usd),
            note="UK PAYE salary converted at the fixed demo rate.",
        ),
        FormLine(
            line="3a",
            label="Certain itemized deductions or standard deduction",
            value=float(standard_deduction),
            note="Standard deduction; allocates fully against foreign income because the line 3f "
            "ratio is 1.0000 (all income is foreign-source).",
        ),
        FormLine(
            line="7",
            label="Subtract line 6 from line 1a. Enter the result here and on line 15, page 2",
            value=float(taxable),
        ),
        FormLine(
            line="II.8",
            label="Foreign taxes paid or accrued — total, in U.S. dollars (column (u))",
            value=float(uk_tax_usd),
            citation_key="treaty_art24",
            note="UK income tax withheld under PAYE (evidenced by form P60), converted at the fixed "
            "demo rate. Date paid and per-column split not collected.",
        ),
        FormLine(
            line="9",
            label="Enter the amount from line 8. These are your total foreign taxes paid or accrued "
            "for the category of income checked above Part I",
            value=float(uk_tax_usd),
        ),
        FormLine(
            line="10",
            label="Enter the sum of any carryover of foreign taxes plus any carrybacks to the current tax year",
            value=0.0,
            note="No carryover in demo scope — multi-year tracking is on the roadmap.",
        ),
        FormLine(
            line="14",
            label="Combine lines 11, 12, and 13. This is the total amount of foreign taxes available for credit",
            value=float(uk_tax_usd),
        ),
        FormLine(
            line="17",
            label="Combine the amounts on lines 15 and 16. This is your net foreign source taxable income",
            value=float(taxable),
            note="Line 16 adjustments are zero in demo scope.",
        ),
        FormLine(
            line="18",
            label="Enter your taxable income (Form 1040, line 15)",
            value=float(taxable),
            note="All income is foreign-source in demo scope, so lines 17 and 18 are equal.",
        ),
        FormLine(
            line="19",
            label="Divide line 17 by line 18. If line 17 is more than line 18, enter \"1\"",
            text_value="1.0000",
        ),
        FormLine(
            line="20",
            label="Individuals: Enter the total of Form 1040, line 16, and Schedule 2 (Form 1040), line 1z",
            value=float(gross_tax),
            note="US tax before credits, from the 2024 brackets.",
        ),
        FormLine(
            line="21",
            label="Multiply line 20 by line 19 (maximum amount of credit)",
            value=float(gross_tax),
            citation_key="irc_901_ftc",
            note="The §904 limitation.",
        ),
        FormLine(
            line="24",
            label="Enter the smaller of line 14 or line 23. Enter here and on the appropriate line of Part IV",
            value=float(credit),
        ),
        FormLine(
            line="35",
            label="Subtract line 34 from line 33. This is your foreign tax credit. Enter here and on "
            "Schedule 3 (Form 1040), line 1",
            value=float(credit),
            citation_key="schedule_3_ftc",
        ),
    ]
    note = ("Single category (general), single country — column A / line A only. Lines 12-13, 16, 22 "
            "and 25-34 are zero or pass-throughs in demo scope.")
    if excess > 0:
        note += (f" Excess credit of ${excess:,.2f} carries forward up to 10 years — Schedule B "
                 "(Form 1116) tracking is on the roadmap.")
    return FormPreview(
        form="Form 1116",
        tax_year=TAX_YEAR,
        lines=lines,
        flows_to="Schedule 3 (Form 1040), line 1",
        note=note,
    )

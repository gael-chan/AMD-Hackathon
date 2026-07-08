"""Schedule 2 (Form 1040) — Additional Taxes, tax year 2024.

Only emitted when a PFIC distribution/disposal makes the form required. The
§1291 excess-distribution tax needs data outside demo scope (distribution
history, holding periods), so those lines carry value=None — the engine
never prints a number it did not compute. Line 11 IS deterministic: UK PAYE
wages are FICA-exempt under the US-UK Totalization Agreement, so the
Additional Medicare Tax (which piggybacks on the Medicare wage base) is zero.
Line captions are quoted verbatim from the official 2024 form.
"""
from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_schedule_2() -> FormPreview:
    """Line entries for Schedule 2 when a PFIC distribution/disposal occurred."""
    return FormPreview(
        form="Schedule 2 (Form 1040)",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="11",
                label="Additional Medicare Tax. Attach Form 8959 if required",
                value=0.0,
                citation_key="totalization_agreement",
                note="UK PAYE wages are exempt from US Medicare tax under the US-UK Totalization Agreement.",
            ),
            FormLine(
                line="12",
                label="Net investment income tax. Attach Form 8960",
                value=None,
                note="Not evaluated in demo scope — depends on MAGI and net investment income.",
            ),
            FormLine(
                line="17",
                label="Other additional taxes",
                value=None,
                citation_key="form_8621_pfic",
                note="The §1291 excess-distribution tax from Form 8621 is included here. Not computed in "
                "demo scope — requires distribution history and holding periods.",
            ),
            FormLine(
                line="21",
                label="Add lines 4, 7 through 16, and 18. These are your total other taxes. "
                "Enter here and on Form 1040 or 1040-SR, line 23",
                value=None,
                note="Cannot be totaled until lines 12 and 17 are computed.",
            ),
        ],
        flows_to="Form 1040, line 23",
        note="Part I (AMT, excess APTC repayment) is not evaluated in demo scope. Lines marked '—' apply "
        "but need data outside the current engine.",
    )

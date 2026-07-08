"""Form 8621 — Information Return by a Shareholder of a PFIC, tax year 2024.

The ISA trap form. Demo scope defaults the fund to a section 1291 fund: a QEF
election needs a PFIC Annual Information Statement (UK ISA funds essentially
never issue one) and no mark-to-market election is on file. With no
distribution or disposal during the year, Part V is deterministically zero
and the filing is informational only. With a distribution/disposal, the
excess-distribution amounts need holding-period data outside demo scope, so
those lines carry value=None. Line captions quoted from the official form.

Form 8621 is filed once per PFIC; the engine holds one aggregate value, so
the preview treats the aggregate as a single fund and says so.
"""
from decimal import Decimal
from typing import Optional

from models import FormLine, FormPreview

TAX_YEAR = 2024

# Part I line 4 value-range checkboxes
_VALUE_BOXES = [
    (Decimal("50000"), "(a) $0-50,000"),
    (Decimal("100000"), "(b) $50,001-100,000"),
    (Decimal("150000"), "(c) $100,001-150,000"),
    (Decimal("200000"), "(d) $150,001-200,000"),
]


def _value_box(value: Decimal) -> str:
    for upper, box in _VALUE_BOXES:
        if value <= upper:
            return box
    return "(e) If more than $200,000, list value"


def build_form_8621(pfic_value: Optional[Decimal], had_distribution_or_disposal: bool) -> FormPreview:
    """Line entries for Form 8621 when filing is required (over the §1298(f)
    de minimis threshold, or any distribution/disposal during the year)."""
    lines = [
        FormLine(
            line="I.4",
            label="Value of shares at end of tax year",
            value=float(pfic_value) if pfic_value is not None else None,
            citation_key="form_8621_pfic",
            note=f"Check box {_value_box(pfic_value)}." if pfic_value is not None
            else "Year-end value not reported; required to determine the value-range checkbox.",
        ),
        FormLine(
            line="I.5a",
            label="Type of PFIC and amount of excess distribution: Section 1291 fund",
            value=None,
            note="Checkbox, no amount. Default regime — a QEF election requires a PFIC Annual "
            "Information Statement (UK ISA funds essentially never issue one) and no "
            "mark-to-market election is on file.",
        ),
    ]

    if had_distribution_or_disposal:
        lines += [
            FormLine(
                line="V.15a",
                label="Enter your total distributions from the section 1291 fund during the current tax year",
                value=None,
                note="Not computed in demo scope — requires the distribution amounts.",
            ),
            FormLine(
                line="V.15e",
                label="Subtract line 15d from line 15a. This amount, if more than zero, is the excess distribution",
                value=None,
                note="Requires the prior three years' distribution history (the 125% base).",
            ),
            FormLine(
                line="V.16e",
                label="Aggregate increases in tax (before credits)",
                value=None,
                citation_key="form_8621_pfic",
                note="The §1291 deferred tax, allocated over the holding period at each year's highest "
                "rate. Flows to Schedule 2 as additional tax once computed.",
            ),
            FormLine(
                line="V.16f",
                label="Interest accrued on deferred tax",
                value=None,
                note="Underpayment-rate interest on each prior year's deferred tax.",
            ),
        ]
        flows_to = "Schedule 2 (Form 1040), line 17 — once the §1291 amounts are computed"
        note = ("A distribution/disposal occurred, so the section 1291 excess-distribution regime applies. "
                "Amounts need data outside demo scope (distribution history, acquisition dates). "
                "One Form 8621 is required per PFIC — the engine holds a single aggregate value.")
    else:
        lines += [
            FormLine(
                line="V.15a",
                label="Enter your total distributions from the section 1291 fund during the current tax year",
                value=0.0,
                note="No distributions or dispositions reported for the year.",
            ),
            FormLine(
                line="V.15e",
                label="Subtract line 15d from line 15a. This amount, if more than zero, is the excess distribution",
                value=0.0,
            ),
            FormLine(
                line="V.16e",
                label="Aggregate increases in tax (before credits)",
                value=0.0,
                citation_key="form_8621_pfic",
                note="No excess distribution, so no §1291 deferred tax this year.",
            ),
        ]
        flows_to = None
        note = ("Informational filing only — holdings exceed the §1298(f) de minimis threshold but there "
                "was no distribution or disposal, so no §1291 tax is due this year. One Form 8621 is "
                "required per PFIC — the engine holds a single aggregate value.")

    return FormPreview(
        form="Form 8621",
        tax_year=TAX_YEAR,
        lines=lines,
        flows_to=flows_to,
        note=note,
    )

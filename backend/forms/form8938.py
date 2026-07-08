"""Form 8938 — Statement of Specified Foreign Financial Assets (FATCA), tax year 2024.

Emitted when the aggregate balance exceeds the living-abroad threshold. The
engine holds one aggregate peak balance, so the summary value is filled and
the per-account detail (Parts V/VI) is flagged as not collected. Part IV
cross-references Form 8621: PFIC holdings already reported there are
excepted from duplicate reporting here and only counted. Captions quoted
from the official form.
"""
from decimal import Decimal

from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_form_8938(balance: Decimal, threshold: Decimal, files_8621: bool) -> FormPreview:
    """Line entries for Form 8938 when reporting is required.

    balance: peak aggregate foreign account balance (USD).
    threshold: the living-abroad threshold applied for the filing status.
    files_8621: whether a Form 8621 is also being filed (Part IV exception).
    """
    lines = [
        FormLine(
            line="I.1",
            label="Number of deposit accounts (reported in Part V)",
            value=None,
            note="Per-account detail (institution, account number, deposit vs custodial split) "
            "not collected in demo scope.",
        ),
        FormLine(
            line="I.2",
            label="Maximum value of all deposit accounts",
            value=float(balance),
            citation_key="form_8938",
            note="Aggregate peak across all foreign accounts as reported; the deposit/custodial "
            "split for Parts I and V needs per-account data.",
        ),
        FormLine(
            line="III",
            label="Summary of Tax Items Attributable to Specified Foreign Financial Assets",
            value=None,
            note="Interest/dividends attributable to the accounts not collected in demo scope.",
        ),
    ]
    if files_8621:
        lines.append(FormLine(
            line="IV",
            label="Excepted Specified Foreign Financial Assets — number of Forms 8621",
            value=1.0,
            citation_key="form_8621_pfic",
            note="ISA PFIC holdings are reported on Form 8621 and excepted from duplicate "
            "reporting on this form; they are only counted here.",
        ))
    return FormPreview(
        form="Form 8938",
        tax_year=TAX_YEAR,
        lines=lines,
        flows_to=None,
        note=f"Required — peak aggregate balance ${balance:,.0f} exceeds the ${threshold:,.0f} "
        "living-abroad threshold. Filed with the income tax return, in addition to (not instead "
        "of) the FBAR.",
    )

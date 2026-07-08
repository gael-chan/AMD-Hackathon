"""Form 8833 — Treaty-Based Return Position Disclosure (§6114), tax year 2024.

Demo scope covers one position: deferral of US tax on earnings accruing in a
UK employer ("workplace") pension scheme under Article 18 of the US-UK
treaty. The disclosure is text, not arithmetic — the entries below are
deterministic templates from the treaty citations; the deferred amount
itself is outside demo scope. Line captions quoted from the official form.
"""
from models import FormLine, FormPreview

TAX_YEAR = 2024


def build_form_8833() -> FormPreview:
    """Template entries for the Article 18 pension-deferral disclosure."""
    return FormPreview(
        form="Form 8833",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="1a",
                label="Enter the specific treaty position relied on: Treaty country",
                text_value="United Kingdom",
                citation_key="form_8833_treaty",
            ),
            FormLine(
                line="1b",
                label="Article(s)",
                text_value="Article 18 (Pension Schemes)",
                citation_key="form_8833_treaty",
            ),
            FormLine(
                line="2",
                label="List the Internal Revenue Code provision(s) overruled or modified by the "
                "treaty-based return position",
                text_value="IRC §§ 61, 83, 402(b) — current US taxation of employer pension "
                "contributions and accrued earnings",
            ),
            FormLine(
                line="4",
                label="List the provision(s) of the limitation on benefits article (if any) in the "
                "treaty that the taxpayer relies on",
                text_value="Article 23(2)(a) — individual resident of a Contracting State",
            ),
            FormLine(
                line="6",
                label="Explain the treaty-based return position taken. Include a brief summary of "
                "the facts on which it is based",
                text_value="Taxpayer is a US citizen resident in the UK participating in a UK "
                "employer pension scheme. Under Article 18(1), earnings accruing within the scheme "
                "are not taxed by the US until distributed.",
                note="Amount of deferred earnings not computed in demo scope — attach the figure "
                "before filing.",
            ),
        ],
        flows_to=None,
        note="Protective disclosure documenting the Article 18 pension position; entries are "
        "deterministic templates — review before filing. Attached to Form 1040.",
    )

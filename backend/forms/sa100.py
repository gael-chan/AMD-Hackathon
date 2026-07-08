"""SA100 — UK Self Assessment main tax return (2026 form, year to 5 April 2026).

The engine's deterministic contribution is page TR 2: which supplementary
pages must accompany the return. Captions quoted from the official form.
Note the year mismatch surfaced on the card: the US-side computation is
TY2024, whose corresponding UK return is 2024-25 (SA100 2025) — the user
supplied the 2026 forms, whose structure is used here.
"""
from models import FormLine, FormPreview

TAX_YEAR = 2026  # UK tax year 6 April 2025 - 5 April 2026


def build_sa100(has_sa106: bool, has_sa109: bool) -> FormPreview:
    """TR 2 supplementary-pages answers driving the rest of the return."""
    return FormPreview(
        form="SA100 (Self Assessment)",
        tax_year=TAX_YEAR,
        lines=[
            FormLine(
                line="TR2.1",
                label="Employment. Were you an employee, director, office holder or agency worker in the year?",
                text_value="Yes — 1 employment",
                citation_key="sa100_main",
                note="UK PAYE salary. Requires a separate Employment page (SA102) — not yet built by "
                "this engine.",
            ),
            FormLine(
                line="TR2.5",
                label="Foreign. Do you need to fill in the 'Foreign' pages?",
                text_value="Yes" if has_sa106 else "No",
                citation_key="sa106_foreign" if has_sa106 else None,
                note="Non-UK-source income reported — see the SA106 preview." if has_sa106
                else "No non-UK-source income or gains reported.",
            ),
            FormLine(
                line="TR2.8",
                label="Residence and foreign income and gains (FIG) regime etc. Do you need to complete these pages?",
                text_value="Yes" if has_sa109 else "No",
                citation_key="sa109_residence" if has_sa109 else None,
                note="Residence/domicile position requires the SA109 pages — see its preview." if has_sa109
                else "Full-year UK resident with no FIG/residence claims.",
            ),
        ],
        flows_to=None,
        note="UK tax year 6 April 2025 to 5 April 2026 (2026 form as supplied). Caution: the US-side "
        "computation is TY2024, whose corresponding UK return is 2024-25 — filed on the SA100 2025. "
        "Personal details (TR 1) and income boxes (TR 3+) not collected in demo scope.",
    )

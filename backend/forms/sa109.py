"""SA109 — UK Self Assessment Residence pages (2026 form, year to 5 April 2026).

The 2026 form is the FIG-regime revision: the remittance basis was abolished
from 6 April 2025 and boxes 25-27 are marked 'not in use'. A profile that
claims non-dom/remittance status therefore gets an explicit regime-transition
entry instead of an invented box number — on the 2024-25 return (SA109 2025)
those claims go in boxes 23/28; from 2025-26 the 4-year FIG regime applies.
Captions quoted from the official form.
"""
from models import FormLine, FormPreview

TAX_YEAR = 2026  # UK tax year 6 April 2025 - 5 April 2026


def build_sa109(non_resident: bool, split_year: bool, non_dom_or_remittance: bool) -> FormPreview:
    """Residence-status boxes plus the FIG-regime position."""
    lines = [
        FormLine(
            line="1",
            label="If you were not resident in the UK for the year, put 'X' in the box",
            text_value="X" if non_resident else "—",
            citation_key="sa109_residence",
        ),
        FormLine(
            line="3",
            label="If your circumstances meet the criteria for split year treatment, put 'X' in the box",
            text_value="X" if split_year else "—",
            citation_key="sa109_residence",
            note="If claiming split year, box 6 needs the date the UK part of the year begins or ends "
            "— not collected in demo scope." if split_year else None,
        ),
        FormLine(
            line="10",
            label="Number of days spent in the UK during the year",
            value=None,
            note="Not collected — the profile's days-abroad field counts days outside the US (for the "
            "IRS physical presence test), which is not the same as UK presence days.",
        ),
    ]
    if non_dom_or_remittance:
        lines.append(FormLine(
            line="FIG",
            label="Foreign income and gains (FIG) regime, Overseas Workday Relief (OWR) and "
            "temporary repatriation facility (TRF)",
            text_value="Regime transition applies",
            citation_key="sa109_residence",
            note="The remittance basis was abolished from 6 April 2025 — this 2026 form has no "
            "remittance-basis boxes (25-27 are 'not in use'). For the 2024-25 return (SA109 2025) "
            "the non-dom/remittance claim goes in boxes 23/28; from 2025-26, consider the 4-year "
            "FIG regime instead (eligibility: first 4 years of UK residence after 10 consecutive "
            "non-resident years).",
        ))
    return FormPreview(
        form="SA109 (Residence)",
        tax_year=TAX_YEAR,
        lines=lines,
        flows_to="SA100 (attached as the Residence supplementary pages)",
        note="UK tax year 2025-26 (2026 form as supplied); the TY2024 US computation corresponds to "
        "the 2024-25 UK return, where the remittance basis still applied.",
    )

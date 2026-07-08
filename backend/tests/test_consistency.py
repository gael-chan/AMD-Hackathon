"""Cross-form consistency invariants, swept over a grid of profiles.

These are the audit-trail guarantees: numbers that appear on two forms must
be identical, previews must exist exactly for the required forms that have
builders, the 1040 bottom line must equal the engine's headline number, and
every citation key must resolve to a real snippet.
"""
from decimal import Decimal

import pytest

from models import TaxProfile
from snippets import SNIPPETS
from tax_engine import GBP_USD_RATE, analyze

# Forms that have preview builders (FBAR is flag-only; Schedule 1-A never
# emits for a 2024-constants engine).
PREVIEWABLE = {
    "Form 1040", "Form 2555", "Form 1116",
    "Schedule 1 (Form 1040)", "Schedule 2 (Form 1040)", "Schedule 3 (Form 1040)",
    "Form 8621", "Form 8833", "Form 8938",
    "SA106 (Foreign)", "SA109 (Residence)", "SA100 (Self Assessment)",
}

GRID = [
    dict(uk_salary=s, uk_tax_paid=t, filing_status="single",
         days_abroad=d, dependents=dep)
    for s in (20000, 85000, 120000, 400000)
    for t in (0, 5000, 24000, 60000)
    for d in (329, 340)
    for dep in (0, 2)
]

EXTRAS = [
    dict(uk_salary=85000, uk_tax_paid=24000, filing_status="married_filing_jointly",
         days_abroad=340, dependents=1, foreign_account_balance=250000,
         pfic_holdings_value=30000, uk_workplace_pension=True,
         foreign_source_income_or_gains_gbp=4000),
    dict(uk_salary=85000, uk_tax_paid=24000, filing_status="single",
         days_abroad=340, dependents=0, pfic_distribution_or_disposal=True,
         pfic_holdings_value=30000),
]


def preview(result, form):
    return next((fp for fp in result.form_previews if fp.form == form), None)


def line(fp, n):
    return next(ln for ln in fp.lines if ln.line == n)


@pytest.mark.parametrize("profile", GRID + EXTRAS)
def test_invariants(profile):
    r = analyze(TaxProfile(**profile))

    required = {f.form for f in r.filing_flags if f.required}
    previewed = {fp.form for fp in r.form_previews}

    # 1. Previews exist exactly for required-and-previewable forms
    assert previewed == (required & PREVIEWABLE)

    # 2. Election-form bottom lines equal their schedule entries
    if r.recommended_route == "FTC":
        f1116, sch3, f1040 = preview(r, "Form 1116"), preview(r, "Schedule 3 (Form 1040)"), preview(r, "Form 1040")
        credit = line(f1116, "35").value
        assert line(f1116, "24").value == credit
        assert line(sch3, "1").value == credit == line(sch3, "8").value
        assert line(f1040, "20").value == credit
    else:
        f2555, sch1, f1040 = preview(r, "Form 2555"), preview(r, "Schedule 1 (Form 1040)"), preview(r, "Form 1040")
        excluded = line(f2555, "45").value
        assert line(f2555, "42").value == excluded
        assert line(sch1, "8d").value == -excluded == line(sch1, "10").value
        assert line(f1040, "8").value == -excluded
        # The exclusion is min(income, cap)
        income = float(round(Decimal(str(profile["uk_salary"])) * GBP_USD_RATE, 2))
        assert excluded == min(income, 126500.0)

    # 3. 1040 line 24 equals the engine's headline number (when computable)
    line24 = line(preview(r, "Form 1040"), "24").value
    if profile.get("pfic_distribution_or_disposal"):
        assert line24 is None  # honest-pending §1291
    else:
        assert line24 == pytest.approx(r.us_tax_impact, abs=0.005)

    # 4. Every citation key used anywhere resolves to a real snippet
    used = {f.citation_key for f in r.filing_flags if f.citation_key}
    used |= {s.citation_key for route in (r.feie, r.ftc) for s in route.trace if s.citation_key}
    used |= {ln.citation_key for fp in r.form_previews for ln in fp.lines if ln.citation_key}
    assert used <= set(SNIPPETS)

    # 5. The citations panel covers every required flag's citation
    panel = {c.key for c in r.citations}
    assert {f.citation_key for f in r.filing_flags if f.required and f.citation_key} <= panel


def test_legacy_payload_still_works():
    """The original six-field API contract must keep parsing and analyzing."""
    r = analyze(TaxProfile(uk_salary=85000, uk_tax_paid=24000, filing_status="single",
                           days_abroad=340, dependents=0,
                           foreign_account_balance_over_10k=False))
    assert len(r.filing_flags) == 14
    assert {f.jurisdiction for f in r.filing_flags} == {"US", "UK"}

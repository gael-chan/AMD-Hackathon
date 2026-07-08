"""Route-level golden scenarios: FEIE stacking rule, FTC §904 limitation,
physical-presence boundary, CTC floor, and the recommendation logic.

FX is pinned by the engine default GBP_USD_RATE=1.27, so:
£85,000 -> $107,950 · £24,000 -> $30,480 · £120,000 -> $152,400 · £150,000 -> $190,500
"""
from decimal import Decimal

import pytest

from models import TaxProfile
from tax_engine import analyze

BASE = dict(uk_salary=85000, uk_tax_paid=24000, filing_status="single",
            days_abroad=340, dependents=0)


def run(**overrides):
    return analyze(TaxProfile(**{**BASE, **overrides}))


# ---- The demo headline scenario ----

def test_sarah_default_both_routes_zero_ftc_recommended():
    r = run()
    assert r.feie.eligible and r.feie.us_tax_owed == 0.0
    assert r.ftc.us_tax_owed == 0.0
    # Equal outcomes break toward FTC (carryforward + no revocation lock-out)
    assert r.recommended_route == "FTC"
    assert r.us_tax_impact == 0.0


def test_sarah_ftc_credit_capped_at_limitation_with_excess():
    """UK tax $30,480 vs gross US tax $15,590: credit caps at 15,590,
    excess 14,890 carries forward — asserted via the trace and detail."""
    r = run()
    step = next(s for s in r.ftc.trace if s.step.startswith("Foreign tax credit"))
    assert step.result == "15590.00"
    assert "14,890.00 carries forward" in r.ftc.detail


# ---- FEIE math ----

def test_feie_full_exclusion_under_cap():
    r = run(uk_tax_paid=5000)  # low UK tax makes FEIE win
    assert r.recommended_route == "FEIE"
    assert r.feie.us_tax_owed == 0.0


def test_feie_stacking_rule_over_cap():
    """£120,000 -> $152,400. Excluded 126,500; taxable = 152,400-126,500-14,600
    = 11,300. Stacked tax = tax(138,800... [11,300+126,500=137,800]) - tax(126,500)
    = 26,114.50 - 23,402.50 = 2,712.00 — NOT the plain bracket tax on 11,300
    (which would be 1,130)."""
    r = run(uk_salary=120000, uk_tax_paid=0)
    assert r.recommended_route == "FEIE"
    assert r.feie.us_tax_owed == 2712.00


# ---- Physical presence boundary ----

@pytest.mark.parametrize("days,eligible", [(329, False), (330, True)])
def test_physical_presence_threshold(days, eligible):
    r = run(days_abroad=days)
    assert r.feie.eligible is eligible
    if not eligible:
        assert r.recommended_route == "FTC"
        assert "physical presence test not met" in r.recommendation_reason


# ---- Child tax credit ----

def test_ctc_never_negative():
    r = run(uk_tax_paid=5000, dependents=3)  # FEIE route, tax already 0
    assert r.recommended_route == "FEIE"
    assert r.feie.us_tax_owed == 0.0


def test_ctc_reduces_residual_ftc_tax():
    """£150,000/£20,000, 1 dependent: gross 35,258.50, credit 25,400,
    residual 9,858.50, CTC 2,000 -> 7,858.50."""
    r = run(uk_salary=150000, uk_tax_paid=20000, dependents=1)
    assert r.recommended_route == "FTC"
    assert r.us_tax_impact == 7858.50


# ---- Recommendation direction ----

def test_high_uk_tax_prefers_ftc_and_low_prefers_feie():
    assert run(uk_tax_paid=30000).recommended_route == "FTC"
    assert run(uk_tax_paid=0).recommended_route == "FEIE"

"""Boundary pins for every filing-flag threshold. The engine uses strict '>'
everywhere: a balance exactly AT a threshold does not trigger the form.
These tests make that a decision, not an accident."""
import pytest

from models import TaxProfile
from tax_engine import analyze

BASE = dict(uk_salary=85000, uk_tax_paid=24000, filing_status="single",
            days_abroad=340, dependents=0)


def flag(result, form):
    return next(f for f in result.filing_flags if f.form == form)


def run(**overrides):
    return analyze(TaxProfile(**{**BASE, **overrides}))


# ---- FBAR: $10,000 aggregate ----

@pytest.mark.parametrize("balance,required", [
    (10000, False), (10000.01, True), (None, False),
])
def test_fbar_threshold(balance, required):
    r = run(foreign_account_balance=balance)
    assert flag(r, "FBAR (FinCEN 114)").required is required


def test_fbar_boolean_fallback_without_exact_balance():
    r = run(foreign_account_balance_over_10k=True)
    assert flag(r, "FBAR (FinCEN 114)").required is True


# ---- Form 8621: §1298(f) de minimis $25k / $50k MFJ ----

@pytest.mark.parametrize("value,status,required", [
    (25000, "single", False),
    (25000.01, "single", True),
    (50000, "married_filing_jointly", False),
    (50000.01, "married_filing_jointly", True),
])
def test_pfic_de_minimis(value, status, required):
    r = run(pfic_holdings_value=value, filing_status=status)
    assert flag(r, "Form 8621").required is required


def test_pfic_distribution_overrides_de_minimis():
    """Any distribution/disposal requires 8621 regardless of value."""
    r = run(pfic_holdings_value=1000, pfic_distribution_or_disposal=True)
    assert flag(r, "Form 8621").required is True
    r2 = run(pfic_distribution_or_disposal=True)  # no value reported at all
    assert flag(r2, "Form 8621").required is True


# ---- Form 8938: living-abroad thresholds $200k / $400k MFJ ----

@pytest.mark.parametrize("balance,status,required", [
    (200000, "single", False),
    (200000.01, "single", True),
    (400000, "married_filing_jointly", False),
    (400000.01, "married_filing_jointly", True),
])
def test_form_8938_threshold(balance, status, required):
    r = run(foreign_account_balance=balance, filing_status=status)
    assert flag(r, "Form 8938").required is required


# ---- UK flags ----

def test_sa106_triggers_on_any_positive_foreign_income():
    assert flag(run(), "SA106 (Foreign)").required is False
    assert flag(run(foreign_source_income_or_gains_gbp=0), "SA106 (Foreign)").required is False
    assert flag(run(foreign_source_income_or_gains_gbp=0.01), "SA106 (Foreign)").required is True


@pytest.mark.parametrize("overrides,required", [
    (dict(), False),
    (dict(uk_tax_residence="split_year"), True),
    (dict(uk_tax_residence="non_resident"), True),
    (dict(uk_non_domiciled=True), True),
    (dict(claims_uk_remittance_basis=True), True),
])
def test_sa109_triggers(overrides, required):
    assert flag(run(**overrides), "SA109 (Residence)").required is required


def test_sa100_follows_supplementary_pages():
    assert flag(run(), "SA100 (Self Assessment)").required is False
    assert flag(run(foreign_source_income_or_gains_gbp=100), "SA100 (Self Assessment)").required is True
    assert flag(run(uk_non_domiciled=True), "SA100 (Self Assessment)").required is True


# ---- Always-on / never-on ----

def test_form_1040_always_required_and_schedule_1a_never():
    r = run()
    assert flag(r, "Form 1040").required is True
    assert flag(r, "Schedule 1-A (Form 1040)").required is False

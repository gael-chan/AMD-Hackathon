"""Golden tests for the 2024 progressive bracket math — every expected value
hand-computed from the IRS rate schedule and pinned exactly."""
from decimal import Decimal

import pytest

from models import FilingStatus
from tax_engine import tax_from_brackets

S = FilingStatus.single
MFJ = FilingStatus.married_filing_jointly


@pytest.mark.parametrize("taxable,expected", [
    # Zero and negative floor
    ("0", "0"),
    ("-100", "0"),
    # First bracket: 10% flat
    ("10000", "1000.00"),
    # Exactly at the first bracket edge: 11,600 x 10%
    ("11600", "1160.00"),
    # One dollar past the edge picks up 12 cents
    ("11601", "1160.12"),
    # Second edge: 1,160 + 35,550 x 12% = 5,426
    ("47150", "5426.00"),
    # Sarah's taxable income: 5,426 + 46,200 x 22% = 15,590
    ("93350", "15590.00"),
    # Third edge: 5,426 + 53,375 x 22% = 17,168.50
    ("100525", "17168.50"),
    # Deep case crossing five brackets:
    # 17,168.50 + 91,425x24% + 51,775x32% + 6,275x35% = 57,874.75
    ("250000", "57874.75"),
])
def test_single_brackets(taxable, expected):
    assert tax_from_brackets(Decimal(taxable), S) == Decimal(expected)


def test_mfj_brackets():
    # 23,200x10% + 71,100x12% + 5,700x22% = 2,320 + 8,532 + 1,254 = 12,106
    assert tax_from_brackets(Decimal("100000"), MFJ) == Decimal("12106.00")


def test_rounding_half_up_to_cents():
    # 93,351.27 taxable: 5,426 + 46,201.27 x 22% = 15,590.2794 -> 15,590.28
    assert tax_from_brackets(Decimal("93351.27"), S) == Decimal("15590.28")


def test_monotonic_in_income():
    """More taxable income can never mean less tax."""
    points = [Decimal(x) for x in ("0", "11600", "47150", "93350", "100525", "191950", "609350", "800000")]
    taxes = [tax_from_brackets(p, S) for p in points]
    assert taxes == sorted(taxes)

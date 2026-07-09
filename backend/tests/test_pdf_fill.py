"""Round-trip tests for PDF filling: every mapped field in the filled PDF
must carry exactly the value the preview computed, and the packet must
contain each supported form plus the provenance manifest."""
import io
import zipfile
from decimal import Decimal

import pytest
from pypdf import PdfReader

from models import TaxProfile
from pdf_fill import SPECS, fill_form, supported_forms
from tax_engine import analyze

FTC_PROFILE = TaxProfile(uk_salary=85000, uk_tax_paid=24000, filing_status="single",
                         days_abroad=340, dependents=0)
FEIE_PROFILE = TaxProfile(uk_salary=85000, uk_tax_paid=5000, filing_status="single",
                          days_abroad=340, dependents=0)

FTC_FORMS = ["Form 1040", "Form 1116", "Schedule 3 (Form 1040)"]
FEIE_FORMS = ["Form 1040", "Form 2555", "Schedule 1 (Form 1040)"]


def preview_for(profile, form):
    r = analyze(profile)
    return next(fp for fp in r.form_previews if fp.form == form)


def read_short_fields(pdf_bytes) -> dict[str, str]:
    fields = PdfReader(io.BytesIO(pdf_bytes)).get_fields() or {}
    out = {}
    for name, f in fields.items():
        v = f.get("/V")
        if v in (None, "", "/Off"):
            continue
        short = name.split(".")[-1]
        for suffix in ("[0]", "[1]", "[2]"):
            short = short.replace(suffix, "")
        out[short] = str(v)
    return out


@pytest.mark.parametrize("profile,form", [(FTC_PROFILE, f) for f in FTC_FORMS]
                         + [(FEIE_PROFILE, f) for f in FEIE_FORMS])
def test_round_trip_values(profile, form):
    preview = preview_for(profile, form)
    filled = read_short_fields(fill_form(preview, profile))
    spec = SPECS[form]
    for ln in preview.lines:
        short = spec.fields.get(ln.line)
        if short is None:
            continue
        if ln.text_value is not None:
            assert filled.get(short) == ln.text_value, f"{form} line {ln.line}"
        elif ln.value is not None:
            expected = f"{abs(ln.value):,.2f}" if (form == "Schedule 1 (Form 1040)" and ln.line == "8d") \
                else f"{ln.value:,.2f}"
            assert filled.get(short) == expected, f"{form} line {ln.line}"
        else:
            # never-bluff: uncomputed lines stay blank
            assert short not in filled, f"{form} line {ln.line} should be blank"


def test_1040_filing_status_checkbox():
    filled = read_short_fields(fill_form(preview_for(FTC_PROFILE, "Form 1040"), FTC_PROFILE))
    assert filled.get("Checkbox_ReadOrder") == "/1"  # Single


def test_1116_category_checkbox_general():
    filled = read_short_fields(fill_form(preview_for(FTC_PROFILE, "Form 1116"), FTC_PROFILE))
    assert filled.get("LineC-D_ReadOrder") == "/4"  # box d: general category


def test_1116_credit_chain_consistent():
    """Line 35 on the PDF equals Schedule 3 line 1 on its PDF."""
    f1116 = read_short_fields(fill_form(preview_for(FTC_PROFILE, "Form 1116"), FTC_PROFILE))
    sch3 = read_short_fields(fill_form(preview_for(FTC_PROFILE, "Schedule 3 (Form 1040)"), FTC_PROFILE))
    assert f1116["f2_27"] == sch3["f1_03"] == "15,590.00"


def test_supported_forms_registry():
    assert set(supported_forms()) == set(FTC_FORMS) | set(FEIE_FORMS)


def test_packet_contents():
    from main import download_packet
    import asyncio

    resp = asyncio.run(download_packet(FTC_PROFILE))
    zf = zipfile.ZipFile(io.BytesIO(resp.body))
    names = set(zf.namelist())
    assert "manifest.txt" in names
    assert {"form-1116.pdf", "schedule-3-1040.pdf", "form-1040.pdf"} <= names
    manifest = zf.read("manifest.txt").decode()
    assert "Recommended route: FTC" in manifest
    assert "GBP/USD" in manifest

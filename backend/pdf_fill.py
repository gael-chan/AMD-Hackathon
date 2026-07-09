"""Fill official IRS PDF templates from FormPreview line values.

Templates are the blank AcroForm PDFs vendored in forms/templates/ (2025
revisions carrying the engine's TY2024 numbers — noted in the packet
manifest). Field mappings were built by rendering every field's own index
onto the page and reading the result; they map our FormLine.line ids to the
short IRS field names (e.g. "f1_03"), resolved to fully-qualified names at
fill time. Values the engine did not compute stay blank — the never-bluff
rule extends to PDFs. Filled files are returned as bytes and never written
to disk.
"""
import io
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

from models import FilingStatus, FormPreview, TaxProfile

TEMPLATES = Path(__file__).parent / "forms" / "templates"

# Fields whose printed parentheses denote a negative entry: write |value|
ABS_FIELDS = {"f1040s1.pdf": {"f1_16"}}


def _fmt(v: float) -> str:
    return f"{v:,.2f}"


def _line_map(preview: FormPreview) -> dict[str, Optional[float]]:
    return {ln.line: ln.value for ln in preview.lines}


def _num(preview: FormPreview, line: str) -> Optional[Decimal]:
    v = _line_map(preview).get(line)
    return None if v is None else Decimal(str(v))


@dataclass
class FormSpec:
    template: str
    # FormLine.line id -> short PDF field name
    fields: dict[str, str]
    # (short field name -> value) computed from preview/profile, for sums the
    # form needs that equal values the engine already computed
    extras: Callable[[FormPreview, TaxProfile], dict[str, str]] = lambda p, t: {}
    # (widget-name fragment, state) checkboxes to tick
    checkboxes: Callable[[FormPreview, TaxProfile], list[tuple[str, str]]] = lambda p, t: []


def _f1040_extras(preview: FormPreview, profile: TaxProfile) -> dict[str, str]:
    out: dict[str, str] = {"f1_54": "Foreign wages - UK PAYE (no W-2)"}
    agi = _num(preview, "11")
    if agi is not None:
        out["f2_01"] = _fmt(float(agi))  # line 11b mirrors 11a
    std = _num(preview, "12")
    if std is not None:
        out["f2_05"] = _fmt(float(std))  # line 14 = 12e (13a/13b blank)
    tax, sch2 = _num(preview, "16"), _num(preview, "17")
    if tax is not None and sch2 is not None:
        out["f2_10"] = _fmt(float(tax + sch2))  # line 18 = 16 + 17
    ctc, sch3 = _num(preview, "19"), _num(preview, "20")
    if ctc is not None and sch3 is not None:
        out["f2_13"] = _fmt(float(ctc + sch3))  # line 21 = 19 + 20
    total = _num(preview, "24")
    if total is not None:
        out["f2_35"] = _fmt(float(total))  # line 37: no payments collected in demo scope
    return out


def _f1040_checkboxes(preview: FormPreview, profile: TaxProfile) -> list[tuple[str, str]]:
    state = {
        FilingStatus.single: "/1",
        FilingStatus.married_filing_jointly: "/2",
        FilingStatus.married_filing_separately: "/3",
        FilingStatus.head_of_household: "/4",
    }[profile.filing_status]
    return [("c1_8", state)]


def _f1116_extras(preview: FormPreview, profile: TaxProfile) -> dict[str, str]:
    out: dict[str, str] = {
        "f1_03": "United Kingdom",  # h: resident of
        "f1_04": "United Kingdom",  # i: column A country
    }
    income = _num(preview, "1a")
    if income is not None:
        out["f1_13"] = _fmt(float(income))  # 1a total column
        out["f1_26"] = _fmt(float(income))  # 3d gross foreign source income
        out["f1_29"] = _fmt(float(income))  # 3e gross income all sources
    std = _num(preview, "3a")
    if std is not None:
        out["f1_23"] = _fmt(float(std))  # 3c = 3a + 3b
        out["f1_35"] = _fmt(float(std))  # 3g = 3c x 3f (ratio 1.0000)
        out["f1_47"] = _fmt(float(std))  # 6 column A
        out["f1_50"] = _fmt(float(std))  # 6 total
    out["f1_32"] = "1.0000"  # 3f
    uk_tax = _num(preview, "II.8")
    if uk_tax is not None:
        out["f1_60"] = _fmt(float(uk_tax))  # Part II row A col (t)
        out["f1_61"] = _fmt(float(uk_tax))  # Part II row A col (u)
        out["f2_03"] = _fmt(float(uk_tax))  # line 11 = 9 + 10 (10 is 0)
    line7 = _num(preview, "7")
    if line7 is not None:
        out["f2_07"] = _fmt(float(line7))  # line 15 = line 7
    limitation = _num(preview, "21")
    if limitation is not None:
        out["f2_15"] = _fmt(float(limitation))  # line 23 = 21 + 22
    credit = _num(preview, "24")
    if credit is not None:
        out["f2_20"] = _fmt(float(credit))  # line 28: general category credit
        out["f2_24"] = _fmt(float(credit))  # line 32 = sum 25-31
        out["f2_25"] = _fmt(float(credit))  # line 33 = smaller of 20 or 32
    return out


def _f1116_checkboxes(preview: FormPreview, profile: TaxProfile) -> list[tuple[str, str]]:
    return [
        ("LineC-D_ReadOrder[0].c1_1[1]", "/4"),  # box d: general category income
        ("ActiveHeaderElements[0].c1_3[0]", "/1"),  # Part II (j): taxes paid
    ]


def _f2555_extras(preview: FormPreview, profile: TaxProfile) -> dict[str, str]:
    out: dict[str, str] = {"f3_15": "1", "f3_16": "000"}  # line 39 ratio 1.000
    income = _num(preview, "19")
    if income is not None:
        out["f2_51"] = _fmt(float(income))  # line 24 = line 19 (20-23 blank)
    excluded = _num(preview, "42")
    if excluded is not None:
        out["f3_20"] = _fmt(float(excluded))  # line 43 = 36 + 42 (36 blank)
    return out


SPECS: dict[str, FormSpec] = {
    "Schedule 3 (Form 1040)": FormSpec(
        template="f1040s3.pdf",
        fields={"1": "f1_03", "8": "f1_25"},
    ),
    "Schedule 1 (Form 1040)": FormSpec(
        template="f1040s1.pdf",
        fields={"8d": "f1_16", "9": "f1_37", "10": "f1_38"},
    ),
    "Form 1040": FormSpec(
        template="f1040.pdf",
        fields={
            "1a": "f1_47", "1h": "f1_55", "1z": "f1_57", "8": "f1_72",
            "9": "f1_73", "11": "f1_75", "12": "f2_02", "15": "f2_06",
            "16": "f2_08", "17": "f2_09", "19": "f2_11", "20": "f2_12",
            "22": "f2_14", "23": "f2_15", "24": "f2_16",
        },
        extras=_f1040_extras,
        checkboxes=_f1040_checkboxes,
    ),
    "Form 1116": FormSpec(
        template="f1116.pdf",
        fields={
            "1a": "f1_10", "3a": "f1_17", "7": "f1_51", "II.8": "f1_82",
            "9": "f2_01", "10": "f2_02", "14": "f2_06", "17": "f2_09",
            "18": "f2_10", "19": "f2_11", "20": "f2_12", "21": "f2_13",
            "24": "f2_16", "35": "f2_27",
        },
        extras=_f1116_extras,
        checkboxes=_f1116_checkboxes,
    ),
    "Form 2555": FormSpec(
        template="f2555.pdf",
        fields={
            "17": "f2_3", "19": "f2_28", "26": "f2_53", "27": "f3_1",
            "37": "f3_13", "38": "f3_14", "40": "f3_17", "41": "f3_18",
            "42": "f3_19", "45": "f3_22",
        },
        extras=_f2555_extras,
    ),
}


def supported_forms() -> list[str]:
    return list(SPECS)


def _full_name(obj) -> str:
    parts = []
    while obj is not None:
        t = obj.get("/T")
        if t:
            parts.append(str(t))
        parent = obj.get("/Parent")
        obj = parent.get_object() if parent is not None else None
    return ".".join(reversed(parts))


def _short(name: str) -> str:
    return name.split(".")[-1].replace("[0]", "").replace("[1]", "").replace("[2]", "")


def fill_form(preview: FormPreview, profile: TaxProfile) -> bytes:
    """Fill the official template for this preview; returns PDF bytes."""
    spec = SPECS[preview.form]
    abs_fields = ABS_FIELDS.get(spec.template, set())

    values: dict[str, str] = {}
    for ln in preview.lines:
        short = spec.fields.get(ln.line)
        if short is None:
            continue
        if ln.text_value is not None:
            values[short] = ln.text_value
        elif ln.value is not None:
            v = abs(ln.value) if short in abs_fields else ln.value
            values[short] = _fmt(v)
    values.update(spec.extras(preview, profile))

    writer = PdfWriter(clone_from=str(TEMPLATES / spec.template))

    # IRS templates ship a dual AcroForm+XFA structure; browser PDF viewers
    # (Chrome/PDF.js) cannot render XFA and show a blank page. The static
    # AcroForm layer is complete, so drop the XFA entry.
    acro = writer._root_object.get("/AcroForm")
    if acro is not None:
        acro_obj = acro.get_object()
        if "/XFA" in acro_obj:
            del acro_obj[NameObject("/XFA")]

    for page in writer.pages:
        page_values: dict[str, str] = {}
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            full = _full_name(obj)
            if _short(full) in values:
                page_values[full] = values[_short(full)]
        if page_values:
            writer.update_page_form_field_values(page, page_values)

    for fragment, state in spec.checkboxes(preview, profile):
        _set_checkbox(writer, fragment, state)

    try:
        writer.set_need_appearances_writer(True)
    except Exception:
        pass

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _set_checkbox(writer: PdfWriter, fragment: str, state: str) -> None:
    """Tick the checkbox/radio widget whose qualified name contains fragment
    and whose appearance dictionary knows the requested state."""
    for page in writer.pages:
        for annot in page.get("/Annots") or []:
            obj = annot.get_object()
            full = _full_name(obj)
            if fragment not in full and fragment not in full.replace("].", "]."):
                continue
            ap = obj.get("/AP")
            states = set()
            if ap is not None:
                n = ap.get_object().get("/N")
                if n is not None:
                    states = {str(k) for k in n.get_object().keys()}
            if state in states or not states:
                obj[NameObject("/AS")] = NameObject(state)
                target = obj.get("/Parent")
                target_obj = target.get_object() if target is not None else obj
                target_obj[NameObject("/V")] = NameObject(state)
                return

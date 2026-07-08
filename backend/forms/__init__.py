"""Deterministic form-line builders.

Each builder takes pre-computed engine values and returns a FormPreview —
the exact line entries for an official IRS/HMRC form, with citation keys.
Same architectural law as the tax engine: pure Python, Decimal in, no LLM.
"""
from forms.form1116 import build_form_1116
from forms.form2555 import build_form_2555
from forms.form8621 import build_form_8621
from forms.form8833 import build_form_8833
from forms.form8938 import build_form_8938
from forms.sa100 import build_sa100
from forms.sa106 import build_sa106
from forms.sa109 import build_sa109
from forms.schedule1 import build_schedule_1
from forms.schedule1a import build_schedule_1a
from forms.schedule2 import build_schedule_2
from forms.schedule3 import build_schedule_3

__all__ = [
    "build_form_1116",
    "build_form_2555",
    "build_form_8621",
    "build_form_8833",
    "build_form_8938",
    "build_sa100",
    "build_sa106",
    "build_sa109",
    "build_schedule_1",
    "build_schedule_1a",
    "build_schedule_2",
    "build_schedule_3",
]

"""Schedule 1-A (Form 1040) — Additional Deductions.

First applies to tax year 2025 (deductions for qualified tips, overtime pay,
car loan interest, and the enhanced senior deduction). This engine computes
tax year 2024, for which the schedule does not exist, so the builder emits
nothing. When the engine is parameterized by year, add the TY2025+ line logic
here; the filing flag (citation key schedule_1a_2025) already explains the
situation to the user.
"""
from typing import Optional

from models import FormPreview

ENGINE_TAX_YEAR = 2024
FIRST_APPLICABLE_YEAR = 2025


def build_schedule_1a() -> Optional[FormPreview]:
    """Returns None for tax years before 2025 — the form did not exist."""
    if ENGINE_TAX_YEAR < FIRST_APPLICABLE_YEAR:
        return None
    raise NotImplementedError("TY2025+ Schedule 1-A lines not yet implemented")

"""Deterministic FEIE/FTC tax engine — tax year 2024, PAYE-only demo scope.

Pure Python, Decimal arithmetic, no floats in the math path, no LLM anywhere.
Every step is appended to a trace with the citation key that justifies it.
"""
import os
from decimal import Decimal, ROUND_HALF_UP

from models import (
    AnalyzeResponse,
    Citation,
    FilingFlag,
    FilingStatus,
    RouteResult,
    TaxProfile,
    TraceStep,
    UkResidenceStatus,
)
from forms import (
    build_form_1040,
    build_form_1116,
    build_form_2555,
    build_form_8621,
    build_form_8833,
    build_form_8938,
    build_sa100,
    build_sa106,
    build_sa109,
    build_schedule_1,
    build_schedule_1a,
    build_schedule_2,
    build_schedule_3,
)
from snippets import get_snippets

# ---- Tax year 2024 constants (hardcoded by design — see README "Design Decisions") ----

GBP_USD_RATE = Decimal(os.getenv("GBP_USD_RATE", "1.27"))

FEIE_LIMIT_2024 = Decimal("126500")
PHYSICAL_PRESENCE_MIN_DAYS = 330

STANDARD_DEDUCTION_2024 = {
    FilingStatus.single: Decimal("14600"),
    FilingStatus.married_filing_jointly: Decimal("29200"),
    FilingStatus.married_filing_separately: Decimal("14600"),
    FilingStatus.head_of_household: Decimal("21900"),
}

# (upper bound of bracket, marginal rate) — 2024 IRS brackets
BRACKETS_2024 = {
    FilingStatus.single: [
        (Decimal("11600"), Decimal("0.10")),
        (Decimal("47150"), Decimal("0.12")),
        (Decimal("100525"), Decimal("0.22")),
        (Decimal("191950"), Decimal("0.24")),
        (Decimal("243725"), Decimal("0.32")),
        (Decimal("609350"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.married_filing_jointly: [
        (Decimal("23200"), Decimal("0.10")),
        (Decimal("94300"), Decimal("0.12")),
        (Decimal("201050"), Decimal("0.22")),
        (Decimal("383900"), Decimal("0.24")),
        (Decimal("487450"), Decimal("0.32")),
        (Decimal("731200"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.married_filing_separately: [
        (Decimal("11600"), Decimal("0.10")),
        (Decimal("47150"), Decimal("0.12")),
        (Decimal("100525"), Decimal("0.22")),
        (Decimal("191950"), Decimal("0.24")),
        (Decimal("243725"), Decimal("0.32")),
        (Decimal("365600"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
    FilingStatus.head_of_household: [
        (Decimal("16550"), Decimal("0.10")),
        (Decimal("63100"), Decimal("0.12")),
        (Decimal("100500"), Decimal("0.22")),
        (Decimal("191950"), Decimal("0.24")),
        (Decimal("243700"), Decimal("0.32")),
        (Decimal("609350"), Decimal("0.35")),
        (None, Decimal("0.37")),
    ],
}

CHILD_TAX_CREDIT_PER_CHILD = Decimal("2000")

FBAR_THRESHOLD = Decimal("10000")
FORM_8938_THRESHOLD_ABROAD = {
    FilingStatus.single: Decimal("200000"),
    FilingStatus.married_filing_separately: Decimal("200000"),
    FilingStatus.head_of_household: Decimal("200000"),
    FilingStatus.married_filing_jointly: Decimal("400000"),
}

# §1298(f) de minimis exception — no Form 8621 needed below this aggregate PFIC
# value, provided there was also no distribution/disposal during the year.
PFIC_DE_MINIMIS = {
    FilingStatus.single: Decimal("25000"),
    FilingStatus.married_filing_separately: Decimal("25000"),
    FilingStatus.head_of_household: Decimal("25000"),
    FilingStatus.married_filing_jointly: Decimal("50000"),
}

CENT = Decimal("0.01")


def _round(d: Decimal) -> Decimal:
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


def tax_from_brackets(taxable: Decimal, status: FilingStatus) -> Decimal:
    """Progressive tax on taxable income using 2024 brackets. Pure, Decimal-only."""
    if taxable <= 0:
        return Decimal("0")
    tax = Decimal("0")
    lower = Decimal("0")
    for upper, rate in BRACKETS_2024[status]:
        if upper is None or taxable <= upper:
            tax += (taxable - lower) * rate
            break
        tax += (upper - lower) * rate
        lower = upper
    return _round(tax)


def compute_feie(income_usd: Decimal, profile: TaxProfile) -> tuple[RouteResult, Decimal]:
    """FEIE route: exclude foreign earned income up to the limit, tax the rest
    under the stacking rule (Foreign Earned Income Tax Worksheet).
    Returns the route result and the excluded amount (0 if ineligible)."""
    trace: list[TraceStep] = []
    status = profile.filing_status

    eligible = profile.days_abroad >= PHYSICAL_PRESENCE_MIN_DAYS
    trace.append(TraceStep(
        step="Physical presence test",
        formula=f"days_abroad >= {PHYSICAL_PRESENCE_MIN_DAYS}",
        inputs={"days_abroad": profile.days_abroad},
        result="PASS" if eligible else "FAIL",
        citation_key="irc_911_feie",
    ))
    if not eligible:
        return RouteResult(
            route="FEIE", eligible=False, us_tax_owed=0.0,
            detail=f"Not eligible: only {profile.days_abroad} days abroad; the physical "
                   f"presence test requires at least {PHYSICAL_PRESENCE_MIN_DAYS}.",
            trace=trace,
        ), Decimal("0")

    excluded = min(income_usd, FEIE_LIMIT_2024)
    trace.append(TraceStep(
        step="FEIE exclusion",
        formula=f"min(foreign_earned_income, {FEIE_LIMIT_2024})",
        inputs={"foreign_earned_income_usd": str(income_usd), "feie_limit_2024": str(FEIE_LIMIT_2024)},
        result=str(excluded),
        citation_key="irc_911_feie",
    ))

    std = STANDARD_DEDUCTION_2024[status]
    taxable = max(Decimal("0"), income_usd - excluded - std)
    trace.append(TraceStep(
        step="Taxable income after exclusion",
        formula="max(0, income - excluded - standard_deduction)",
        inputs={"income_usd": str(income_usd), "excluded": str(excluded), "standard_deduction": str(std)},
        result=str(taxable),
        citation_key="irc_911_feie",
    ))

    # Stacking rule: tax the remainder at the rates that would apply without the exclusion
    tax_with_excluded = tax_from_brackets(taxable + excluded, status)
    tax_on_excluded = tax_from_brackets(excluded, status)
    tax = max(Decimal("0"), tax_with_excluded - tax_on_excluded)
    trace.append(TraceStep(
        step="Tax under stacking rule",
        formula="tax(taxable + excluded) - tax(excluded)",
        inputs={"tax_with_excluded": str(tax_with_excluded), "tax_on_excluded": str(tax_on_excluded)},
        result=str(tax),
        citation_key="pub54_stacking",
    ))

    if profile.dependents > 0:
        ctc = CHILD_TAX_CREDIT_PER_CHILD * profile.dependents
        applied = min(tax, ctc)
        tax -= applied
        trace.append(TraceStep(
            step="Child tax credit (nonrefundable portion)",
            formula=f"min(tax, {CHILD_TAX_CREDIT_PER_CHILD} x dependents)",
            inputs={"dependents": profile.dependents, "credit_available": str(ctc)},
            result=str(tax),
        ))

    tax = _round(tax)
    return RouteResult(
        route="FEIE", eligible=True, us_tax_owed=float(tax),
        detail=f"Excludes ${excluded:,.0f} of foreign earned income under §911; "
               f"remaining US tax ${tax:,.2f} (stacking rule applied).",
        trace=trace,
    ), excluded


def compute_ftc(income_usd: Decimal, uk_tax_usd: Decimal, profile: TaxProfile) -> tuple[RouteResult, Decimal]:
    """FTC route: full US tax computation, then credit UK tax up to the §904 limitation.
    Returns the route result and the credited amount."""
    trace: list[TraceStep] = []
    status = profile.filing_status

    std = STANDARD_DEDUCTION_2024[status]
    taxable = max(Decimal("0"), income_usd - std)
    trace.append(TraceStep(
        step="US taxable income",
        formula="max(0, income - standard_deduction)",
        inputs={"income_usd": str(income_usd), "standard_deduction": str(std)},
        result=str(taxable),
    ))

    gross_tax = tax_from_brackets(taxable, status)
    trace.append(TraceStep(
        step="US tax before credits",
        formula="progressive 2024 brackets",
        inputs={"taxable_income": str(taxable), "filing_status": status.value},
        result=str(gross_tax),
    ))

    # §904 limitation: US tax x (foreign-source taxable income / total taxable income).
    # PAYE-only demo scope: all income is foreign-source, so the ratio is 1.
    limitation = gross_tax  # ratio = foreign taxable / total taxable = 1 for this profile
    credit = min(uk_tax_usd, limitation)
    trace.append(TraceStep(
        step="Foreign tax credit (§904 limitation)",
        formula="min(uk_tax_paid_usd, us_tax x foreign_income/total_income)",
        inputs={"uk_tax_paid_usd": str(uk_tax_usd), "limitation": str(limitation)},
        result=str(credit),
        citation_key="irc_901_ftc",
    ))

    tax = max(Decimal("0"), gross_tax - credit)
    trace.append(TraceStep(
        step="US tax after foreign tax credit",
        formula="max(0, us_tax - credit)",
        inputs={"us_tax": str(gross_tax), "credit": str(credit)},
        result=str(tax),
        citation_key="treaty_art24",
    ))

    excess_credit = _round(max(Decimal("0"), uk_tax_usd - limitation))
    if excess_credit > 0:
        trace.append(TraceStep(
            step="Excess credit carryforward",
            formula="uk_tax_paid_usd - limitation",
            inputs={"uk_tax_paid_usd": str(uk_tax_usd), "limitation": str(limitation)},
            result=f"{excess_credit} (carries forward up to 10 years)",
            citation_key="irc_901_ftc",
        ))

    if profile.dependents > 0:
        ctc = CHILD_TAX_CREDIT_PER_CHILD * profile.dependents
        applied = min(tax, ctc)
        tax -= applied
        trace.append(TraceStep(
            step="Child tax credit (nonrefundable portion)",
            formula=f"min(tax, {CHILD_TAX_CREDIT_PER_CHILD} x dependents)",
            inputs={"dependents": profile.dependents, "credit_available": str(ctc)},
            result=str(tax),
        ))

    tax = _round(tax)
    detail = f"Credits ${credit:,.2f} of UK tax against US liability; residual US tax ${tax:,.2f}."
    if excess_credit > 0:
        detail += f" Excess credit of ${excess_credit:,.2f} carries forward up to 10 years."
    return RouteResult(route="FTC", eligible=True, us_tax_owed=float(tax), detail=detail, trace=trace), _round(credit)


def pfic_8621_required(profile: TaxProfile) -> tuple[Decimal | None, bool]:
    """Aggregate PFIC value and whether Form 8621 must be filed — §1298(f):
    over the de minimis threshold, or any distribution/disposal in the year."""
    value = Decimal(str(profile.pfic_holdings_value)) if profile.pfic_holdings_value is not None else None
    over = value is not None and value > PFIC_DE_MINIMIS[profile.filing_status]
    return value, over or profile.pfic_distribution_or_disposal


def form_8938_required(profile: TaxProfile) -> tuple[Decimal | None, bool]:
    """Peak aggregate balance and whether Form 8938 must be filed — balance
    over the living-abroad threshold for the filing status."""
    balance = Decimal(str(profile.foreign_account_balance)) if profile.foreign_account_balance is not None else None
    threshold = FORM_8938_THRESHOLD_ABROAD[profile.filing_status]
    return balance, balance is not None and balance > threshold


def uk_sa_required(profile: TaxProfile) -> tuple[bool, bool, bool]:
    """(sa106, sa109, sa100) — SA106 for non-UK-source income, SA109 for
    residence/domicile/remittance claims, SA100 whenever either page attaches."""
    foreign_income = Decimal(str(profile.foreign_source_income_or_gains_gbp)) \
        if profile.foreign_source_income_or_gains_gbp is not None else None
    sa106 = foreign_income is not None and foreign_income > 0
    sa109 = (
        profile.uk_tax_residence != UkResidenceStatus.full_year_resident
        or profile.uk_non_domiciled
        or profile.claims_uk_remittance_basis
    )
    return sa106, sa109, sa106 or sa109


def compute_filing_flags(profile: TaxProfile, recommended: str, feie_eligible: bool) -> list[FilingFlag]:
    # ---- US: the core return ----
    flags = [
        FilingFlag(
            form="Form 1040",
            required=True,
            reason="The core return — a US citizen files on worldwide income regardless of residence; "
            "every schedule and election form attaches to it.",
            citation_key="form_1040_core",
        ),
        # ---- US: route election forms ----
        FilingFlag(
            form="Form 2555",
            required=(recommended == "FEIE"),
            reason="Required to elect the Foreign Earned Income Exclusion."
            if recommended == "FEIE" else
            ("FEIE available but FTC recommended; only file if electing FEIE."
             if feie_eligible else "Not eligible — physical presence test not met."),
            citation_key="irc_911_feie",
        ),
        FilingFlag(
            form="Form 1116",
            required=(recommended == "FTC"),
            reason="Required to claim the Foreign Tax Credit for UK PAYE income tax."
            if recommended == "FTC" else "Not needed if electing FEIE with no residual foreign tax to credit.",
            citation_key="irc_901_ftc",
        ),
    ]

    # ---- US: 1040 schedules that follow mechanically from the election ----
    flags.append(FilingFlag(
        form="Schedule 1 (Form 1040)",
        required=(recommended == "FEIE"),
        reason="The Form 2555 exclusion is reported as a negative amount on Schedule 1, line 8d."
        if recommended == "FEIE" else "Not triggered — no FEIE exclusion or other additional income/adjustments in scope.",
        citation_key="schedule_1_2555",
    ))
    flags.append(FilingFlag(
        form="Schedule 3 (Form 1040)",
        required=(recommended == "FTC"),
        reason="The Form 1116 foreign tax credit is claimed on Schedule 3, Part I, line 1."
        if recommended == "FTC" else "Not triggered — no foreign tax credit or other Schedule 3 credits in scope.",
        citation_key="schedule_3_ftc",
    ))
    flags.append(FilingFlag(
        form="Schedule 2 (Form 1040)",
        required=profile.pfic_distribution_or_disposal,
        reason="PFIC §1291 excess-distribution tax from a distribution/disposal is reported as an additional tax on Schedule 2."
        if profile.pfic_distribution_or_disposal else
        "Not triggered — UK PAYE wages are exempt from US Social Security/Medicare under the US–UK Totalization "
        "Agreement; NIIT and AMT are not evaluated by this tool.",
        citation_key="totalization_agreement",
    ))
    flags.append(FilingFlag(
        form="Schedule 1-A (Form 1040)",
        required=False,
        reason="Not applicable — Schedule 1-A (tips/overtime/car-loan/senior deductions) first applies to tax "
        "year 2025; this analysis uses tax year 2024.",
        citation_key="schedule_1a_2025",
    ))

    # ---- US: PFIC (the ISA trap) ----
    pfic_value, pfic_required = pfic_8621_required(profile)
    de_minimis = PFIC_DE_MINIMIS[profile.filing_status]
    if pfic_required:
        pfic_reason = (
            "PFIC distribution or disposal during the year — the de minimis exception does not apply."
            if profile.pfic_distribution_or_disposal else
            f"Aggregate PFIC holdings (e.g. funds inside a Stocks & Shares ISA) exceed the ${de_minimis:,.0f} "
            f"de minimis threshold. One Form 8621 is required per PFIC."
        )
    elif pfic_value is not None:
        pfic_reason = (f"Holdings reported but at or below the ${de_minimis:,.0f} de minimis threshold with no "
                       "distribution/disposal — filing excused under §1298(f). Note: UK funds/ETFs in an ISA are "
                       "still PFICs; the exception is value-based, not permanent.")
    else:
        pfic_reason = ("Not triggered — no PFIC holdings reported. Caution: UK-domiciled funds, unit trusts, and "
                       "ETFs held in a Stocks & Shares ISA are PFICs even though the ISA is tax-free in the UK.")
    flags.append(FilingFlag(
        form="Form 8621",
        required=pfic_required,
        reason=pfic_reason,
        citation_key="form_8621_pfic",
    ))

    # ---- US: treaty disclosure ----
    flags.append(FilingFlag(
        form="Form 8833",
        required=profile.uk_workplace_pension,
        reason="Disclosing reliance on US–UK Treaty Article 18 to defer US tax on UK workplace pension growth."
        if profile.uk_workplace_pension else "Not triggered — no treaty-based return position reported.",
        citation_key="form_8833_treaty",
    ))

    # ---- US: information reporting ----
    balance = Decimal(str(profile.foreign_account_balance)) if profile.foreign_account_balance is not None else None
    over_10k = (balance is not None and balance > FBAR_THRESHOLD) or bool(profile.foreign_account_balance_over_10k)
    flags.append(FilingFlag(
        form="FBAR (FinCEN 114)",
        required=over_10k,
        reason="Aggregate foreign account balance exceeded $10,000 during the year."
        if over_10k else "Not triggered — aggregate foreign accounts did not exceed $10,000 (or not reported).",
        citation_key="fbar_fincen114",
    ))

    threshold_8938 = FORM_8938_THRESHOLD_ABROAD[profile.filing_status]
    _, over_8938 = form_8938_required(profile)
    flags.append(FilingFlag(
        form="Form 8938",
        required=over_8938,
        reason=f"Specified foreign financial assets exceed the ${threshold_8938:,.0f} threshold for taxpayers living abroad."
        if over_8938 else f"Not triggered — below the ${threshold_8938:,.0f} living-abroad threshold (or balance not reported).",
        citation_key="form_8938",
    ))

    # ---- UK: Self Assessment ----
    sa106_required, sa109_required, sa100_required = uk_sa_required(profile)
    flags.append(FilingFlag(
        form="SA106 (Foreign)",
        jurisdiction="UK",
        required=sa106_required,
        reason="Non-UK-source income/gains reported — required to declare them and claim Foreign Tax Credit "
        "Relief for any US tax paid (e.g. US withholding on RSUs)."
        if sa106_required else "Not triggered — no non-UK-source income or gains reported.",
        citation_key="sa106_foreign",
    ))

    if sa109_required:
        sa109_triggers = []
        if profile.uk_tax_residence == UkResidenceStatus.split_year:
            sa109_triggers.append("split-year treatment")
        elif profile.uk_tax_residence == UkResidenceStatus.non_resident:
            sa109_triggers.append("non-resident status")
        if profile.uk_non_domiciled:
            sa109_triggers.append("non-UK domicile")
        if profile.claims_uk_remittance_basis:
            sa109_triggers.append("remittance basis election")
        sa109_reason = "Required to declare: " + ", ".join(sa109_triggers) + "."
    else:
        sa109_reason = "Not triggered — full-year UK resident, UK domiciled, no remittance basis claim."
    flags.append(FilingFlag(
        form="SA109 (Residence)",
        jurisdiction="UK",
        required=sa109_required,
        reason=sa109_reason,
        citation_key="sa109_residence",
    ))

    flags.append(FilingFlag(
        form="SA100 (Self Assessment)",
        jurisdiction="UK",
        required=sa100_required,
        reason="The main Self Assessment return is required because supplementary pages "
        f"({', '.join(f for f, r in [('SA106', sa106_required), ('SA109', sa109_required)] if r)}) must be attached to it."
        if sa100_required else
        "Not triggered — PAYE collects UK tax at source and no supplementary pages are needed. HMRC may still "
        "issue a notice to file.",
        citation_key="sa100_main",
    ))

    return flags


def analyze(profile: TaxProfile) -> AnalyzeResponse:
    """Run both routes, compare, recommend. Returns everything except the LLM explanation."""
    income_usd = _round(Decimal(str(profile.uk_salary)) * GBP_USD_RATE)
    uk_tax_usd = _round(Decimal(str(profile.uk_tax_paid)) * GBP_USD_RATE)
    fx_trace = TraceStep(
        step="Currency conversion",
        formula=f"GBP x {GBP_USD_RATE} (fixed demo rate)",
        inputs={"uk_salary_gbp": str(profile.uk_salary), "uk_tax_paid_gbp": str(profile.uk_tax_paid)},
        result=f"income ${income_usd}, UK tax ${uk_tax_usd}",
    )

    feie, feie_excluded = compute_feie(income_usd, profile)
    ftc, ftc_credit = compute_ftc(income_usd, uk_tax_usd, profile)
    feie.trace.insert(0, fx_trace)
    ftc.trace.insert(0, fx_trace)

    if not feie.eligible:
        recommended, reason = "FTC", (
            "FEIE is unavailable (physical presence test not met), so the Foreign Tax Credit is the only route."
        )
    elif feie.us_tax_owed < ftc.us_tax_owed:
        recommended, reason = "FEIE", (
            f"FEIE leaves ${feie.us_tax_owed:,.2f} of US tax vs ${ftc.us_tax_owed:,.2f} under FTC — "
            f"saving ${ftc.us_tax_owed - feie.us_tax_owed:,.2f}."
        )
    else:
        saving = feie.us_tax_owed - ftc.us_tax_owed
        reason = (
            f"FTC leaves ${ftc.us_tax_owed:,.2f} of US tax vs ${feie.us_tax_owed:,.2f} under FEIE"
            + (f" — saving ${saving:,.2f}." if saving > 0 else ".")
        )
        if saving == 0:
            reason += (" With equal outcomes, FTC is preferred: excess credits carry forward 10 years and it "
                       "avoids the FEIE revocation lock-out (5-year wait to re-elect).")
        recommended = "FTC"

    flags = compute_filing_flags(profile, recommended, feie.eligible)

    # Emit a preview for every form the engine can speak to, election form
    # first since its bottom line feeds the schedule. Schedule 1-A's builder
    # returns None for TY2024 (the form first exists for TY2025).
    form_previews = []
    std = STANDARD_DEDUCTION_2024[profile.filing_status]
    ctc_available = CHILD_TAX_CREDIT_PER_CHILD * profile.dependents
    if recommended == "FEIE":
        form_previews.append(build_form_2555(income_usd, feie_excluded, FEIE_LIMIT_2024, profile.days_abroad))
        form_previews.append(build_schedule_1(feie_excluded))
        # Line 16 via the Foreign Earned Income Tax Worksheet, mirroring compute_feie
        taxable_after_exclusion = max(Decimal("0"), income_usd - feie_excluded - std)
        line_16 = max(Decimal("0"),
                      tax_from_brackets(taxable_after_exclusion + feie_excluded, profile.filing_status)
                      - tax_from_brackets(feie_excluded, profile.filing_status))
        form_previews.append(build_form_1040(
            route="FEIE", filing_status=profile.filing_status, income_usd=income_usd,
            standard_deduction=std, schedule_1_amount=-feie_excluded, line_16_tax=line_16,
            ctc_applied=min(line_16, ctc_available), schedule_3_credit=Decimal("0"),
            pfic_distribution_pending=profile.pfic_distribution_or_disposal,
        ))
    else:
        taxable = max(Decimal("0"), income_usd - std)
        gross_tax = tax_from_brackets(taxable, profile.filing_status)
        form_previews.append(build_form_1116(income_usd, std, gross_tax, uk_tax_usd, ftc_credit))
        form_previews.append(build_schedule_3(ftc_credit))
        form_previews.append(build_form_1040(
            route="FTC", filing_status=profile.filing_status, income_usd=income_usd,
            standard_deduction=std, schedule_1_amount=Decimal("0"), line_16_tax=gross_tax,
            ctc_applied=min(max(Decimal("0"), gross_tax - ftc_credit), ctc_available),
            schedule_3_credit=ftc_credit,
            pfic_distribution_pending=profile.pfic_distribution_or_disposal,
        ))
    if profile.pfic_distribution_or_disposal:
        form_previews.append(build_schedule_2())
    pfic_value, pfic_required = pfic_8621_required(profile)
    if pfic_required:
        form_previews.append(build_form_8621(pfic_value, profile.pfic_distribution_or_disposal))
    if profile.uk_workplace_pension:
        form_previews.append(build_form_8833())
    balance_8938, required_8938 = form_8938_required(profile)
    if required_8938:
        form_previews.append(build_form_8938(
            balance_8938, FORM_8938_THRESHOLD_ABROAD[profile.filing_status], files_8621=pfic_required,
        ))
    schedule_1a = build_schedule_1a()
    if schedule_1a is not None:
        form_previews.append(schedule_1a)

    # UK side — main return last, since the supplementary pages attach to it
    sa106_req, sa109_req, sa100_req = uk_sa_required(profile)
    if sa106_req:
        form_previews.append(build_sa106(Decimal(str(profile.foreign_source_income_or_gains_gbp))))
    if sa109_req:
        form_previews.append(build_sa109(
            non_resident=(profile.uk_tax_residence == UkResidenceStatus.non_resident),
            split_year=(profile.uk_tax_residence == UkResidenceStatus.split_year),
            non_dom_or_remittance=(profile.uk_non_domiciled or profile.claims_uk_remittance_basis),
        ))
    if sa100_req:
        form_previews.append(build_sa100(has_sa106=sa106_req, has_sa109=sa109_req))

    citation_keys = [s.citation_key for r in (feie, ftc) for s in r.trace if s.citation_key]
    citation_keys += [f.citation_key for f in flags if f.required and f.citation_key]
    citation_keys += [ln.citation_key for fp in form_previews for ln in fp.lines if ln.citation_key]
    citations = [Citation(**snip) for snip in get_snippets(citation_keys)]

    us_tax_impact = feie.us_tax_owed if recommended == "FEIE" else ftc.us_tax_owed

    return AnalyzeResponse(
        feie=feie,
        ftc=ftc,
        recommended_route=recommended,
        recommendation_reason=reason,
        us_tax_impact=us_tax_impact,
        filing_flags=flags,
        form_previews=form_previews,
        citations=citations,
        explanation="",  # filled in by the LLM layer (explanation only, never math)
        explanation_provider="",
    )

"""Curated IRS / HMRC / US-UK treaty citation snippets.

Hand-picked, keyed by citation id. The tax engine tags every trace step and
filing flag with one of these keys; the API returns the full snippet so each
number resolves to the paragraph that justifies it. No vector DB, no
embeddings — six reliable citations beat six hundred uncertain ones.
"""

SNIPPETS: dict[str, dict] = {
    "irc_911_feie": {
        "source": "IRS — 26 USC §911 / IRS Pub 54 (2024)",
        "reference": "§911(a), §911(b)(2)(D); Pub 54 ch. 4 — Foreign Earned Income Exclusion",
        "text": (
            "A qualified individual may elect to exclude foreign earned income from gross "
            "income, up to the inflation-adjusted limit — $126,500 for tax year 2024. To "
            "qualify under the physical presence test, the taxpayer must be present in a "
            "foreign country or countries for at least 330 full days during any period of "
            "12 consecutive months."
        ),
        "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-earned-income-exclusion",
    },
    "pub54_stacking": {
        "source": "IRS Pub 54 (2024) — Foreign Earned Income Tax Worksheet",
        "reference": "Form 1040 instructions; Pub 54 — figuring tax on non-excluded income",
        "text": (
            "If you claim the foreign earned income exclusion, you must figure the tax on "
            "your remaining non-excluded income using the tax rates that would have applied "
            "had you not claimed the exclusion (the 'stacking rule'): compute tax on taxable "
            "income plus the excluded amount, then subtract the tax computed on the excluded "
            "amount alone."
        ),
        "url": "https://www.irs.gov/publications/p54",
    },
    "irc_901_ftc": {
        "source": "IRS — 26 USC §901 / Form 1116 instructions (2024)",
        "reference": "§901(b), §904(a) limitation; Form 1116 line 21",
        "text": (
            "A US citizen may claim a credit for income taxes paid or accrued to a foreign "
            "country. The credit cannot exceed the same proportion of total US tax that "
            "foreign-source taxable income bears to total taxable income (the §904 "
            "limitation). UK income tax withheld under PAYE is a creditable foreign income "
            "tax. Excess credits carry back 1 year and forward 10 years."
        ),
        "url": "https://www.irs.gov/forms-pubs/about-form-1116",
    },
    "treaty_art24": {
        "source": "US–UK Income Tax Treaty (2001) / HMRC DT19850",
        "reference": "Article 24 — Relief from Double Taxation",
        "text": (
            "In accordance with US law, the United States shall allow to a resident or "
            "citizen of the United States as a credit against US tax the income tax paid or "
            "accrued to the United Kingdom. UK income tax collected through PAYE on "
            "employment income (evidenced by form P60) qualifies for this relief."
        ),
        "url": "https://www.gov.uk/hmrc-internal-manuals/double-taxation-relief/dt19850",
    },
    "fbar_fincen114": {
        "source": "FinCEN — Report of Foreign Bank and Financial Accounts (FBAR)",
        "reference": "31 CFR §1010.350; FinCEN Form 114",
        "text": (
            "A US person must file an FBAR (FinCEN Form 114) if the aggregate value of all "
            "foreign financial accounts exceeded $10,000 at any time during the calendar "
            "year. Filed electronically with FinCEN, separate from the tax return. Civil "
            "penalties for non-willful violations start around $10,000 per violation."
        ),
        "url": "https://www.fincen.gov/report-foreign-bank-and-financial-accounts",
    },
    "form_8938": {
        "source": "IRS — Form 8938 (FATCA) instructions (2024)",
        "reference": "26 USC §6038D; Form 8938 reporting thresholds for taxpayers living abroad",
        "text": (
            "Taxpayers living abroad must file Form 8938 if total specified foreign "
            "financial assets exceed $200,000 on the last day of the year or $300,000 at any "
            "time ($400,000 / $600,000 if married filing jointly). Filed with the income tax "
            "return, in addition to (not instead of) the FBAR."
        ),
        "url": "https://www.irs.gov/forms-pubs/about-form-8938",
    },
    "form_1040_core": {
        "source": "IRS — Form 1040, U.S. Individual Income Tax Return (2024)",
        "reference": "26 USC §1, §6012(a) — filing requirement; Form 1040 lines 1h, 8, 16, 19-24",
        "text": (
            "A US citizen must file Form 1040 reporting worldwide income regardless of where they "
            "live. Foreign wages with no Form W-2 are reported on line 1h (other earned income). "
            "Every schedule and election form attaches to the 1040: Schedule 1 flows to line 8, "
            "the tax computation to line 16, credits to lines 19-21, and total tax lands on line 24."
        ),
        "url": "https://www.irs.gov/forms-pubs/about-form-1040",
    },
    "form_8621_pfic": {
        "source": "IRS — Form 8621 instructions (2024)",
        "reference": "26 USC §1291–1298; §1298(f) reporting; de minimis exception ($25,000 / $50,000 MFJ)",
        "text": (
            "A US person who is a direct or indirect shareholder of a Passive Foreign Investment "
            "Company must file Form 8621 for each PFIC. Non-US pooled funds — including UK unit "
            "trusts, OEICs, and ETFs held inside a Stocks & Shares ISA — are generally PFICs; the "
            "ISA wrapper is not recognized by the IRS. Filing is excused under the de minimis "
            "exception only if aggregate PFIC value is $25,000 or less ($50,000 married filing "
            "jointly) AND there was no excess distribution, disposition, or QEF/mark-to-market "
            "election during the year."
        ),
        "url": "https://www.irs.gov/forms-pubs/about-form-8621",
    },
    "form_8833_treaty": {
        "source": "IRS — Form 8833 instructions; 26 USC §6114",
        "reference": "Treaty-based return position disclosure; US–UK Treaty Article 18 (pension schemes)",
        "text": (
            "A taxpayer who takes a position that a US tax treaty overrides or modifies the "
            "Internal Revenue Code must disclose it on Form 8833. Relying on Article 18 of the "
            "US–UK treaty to defer US tax on earnings accruing inside a UK workplace pension "
            "scheme is a treaty-based position commonly disclosed this way."
        ),
        "url": "https://www.irs.gov/forms-pubs/about-form-8833",
    },
    "schedule_1a_2025": {
        "source": "IRS — Schedule 1-A (Form 1040), Additional Deductions",
        "reference": "New for tax year 2025 — deductions for tips, overtime, car loan interest, seniors",
        "text": (
            "Schedule 1-A (Form 1040) is a new schedule first applicable to tax year 2025 returns, "
            "used to claim the deductions for qualified tips, overtime pay, car loan interest, and "
            "the enhanced senior deduction. It does not exist for tax year 2024 returns."
        ),
        "url": "https://www.irs.gov/newsroom/schedule-1-a-additional-deductions-what-to-know-about-the-new-form",
    },
    "schedule_1_2555": {
        "source": "IRS — Schedule 1 (Form 1040), Form 2555 instructions (2024)",
        "reference": "Schedule 1, line 8d — Foreign earned income exclusion from Form 2555",
        "text": (
            "A taxpayer who elects the Foreign Earned Income Exclusion on Form 2555 reports the "
            "excluded amount as a negative entry on Schedule 1 (Form 1040), line 8d. Schedule 1 "
            "must be attached to Form 1040 whenever this exclusion is claimed."
        ),
        "url": "https://www.irs.gov/forms-pubs/schedules-for-form-1040",
    },
    "schedule_3_ftc": {
        "source": "IRS — Schedule 3 (Form 1040) instructions (2024)",
        "reference": "Schedule 3, Part I, line 1 — Foreign tax credit (attach Form 1116 if required)",
        "text": (
            "The Foreign Tax Credit computed on Form 1116 is carried to Schedule 3 (Form 1040), "
            "line 1, which then flows to Form 1040. Schedule 3 must be attached whenever the "
            "credit is claimed."
        ),
        "url": "https://www.irs.gov/forms-pubs/schedules-for-form-1040",
    },
    "totalization_agreement": {
        "source": "SSA — US–UK Totalization Agreement (1985, as amended 1997)",
        "reference": "Agreement on Social Security, Article 4 — coverage exemption for detached/local UK employment",
        "text": (
            "Under the US–UK Totalization Agreement, wages of a US citizen employed and covered "
            "under the UK National Insurance system are generally exempt from US Social Security "
            "and Medicare (FICA) taxes, including the Additional Medicare Tax, which piggybacks on "
            "the same wage base. Schedule 2 (Form 1040) additional taxes — Net Investment Income "
            "Tax, AMT, and PFIC §1291 excess-distribution tax — are not evaluated by this tool."
        ),
        "url": "https://www.ssa.gov/international/Agreement_Pamphlets/uk.html",
    },
    "sa100_main": {
        "source": "HMRC — Self Assessment tax returns: Overview",
        "reference": "Who must complete a Self Assessment tax return (SA100)",
        "text": (
            "A Self Assessment return (SA100) is required for untaxed income not collected via "
            "PAYE, including foreign income, and is mandatory whenever supplementary pages such "
            "as SA106 (Foreign) or SA109 (Residence) must be filed, since they attach to the SA100."
        ),
        "url": "https://www.gov.uk/self-assessment-tax-returns",
    },
    "sa106_foreign": {
        "source": "HMRC — Self Assessment: Foreign (SA106) notes",
        "reference": "SA106 — reporting foreign income/gains and claiming Foreign Tax Credit Relief",
        "text": (
            "The Foreign pages (SA106) must be completed to report non-UK-source income and "
            "gains and to claim Foreign Tax Credit Relief for tax already paid to another "
            "country on that income, e.g. US withholding on US-sourced RSU income."
        ),
        "url": "https://www.gov.uk/government/publications/self-assessment-foreign-sa106",
    },
    "sa109_residence": {
        "source": "HMRC — Self Assessment: Residence, remittance basis etc (SA109) notes",
        "reference": "SA109 — residence, domicile, split-year treatment, and remittance basis claims",
        "text": (
            "The Residence, remittance basis etc pages (SA109) must be completed if not UK "
            "resident for the full year, due split-year treatment, non-UK domiciled, or electing "
            "the remittance basis of taxation for foreign income or gains."
        ),
        "url": "https://www.gov.uk/government/publications/self-assessment-residence-remittance-basis-etc-sa109",
    },
}


def get_snippet(key: str) -> dict | None:
    return SNIPPETS.get(key)


def get_snippets(keys: list[str]) -> list[dict]:
    """Return full snippet dicts (with their key) for the given citation keys, deduplicated."""
    seen: list[dict] = []
    for key in dict.fromkeys(keys):
        snip = SNIPPETS.get(key)
        if snip:
            seen.append({"key": key, **snip})
    return seen

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

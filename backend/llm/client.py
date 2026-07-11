"""LLM explanation layer.

Provider chain: AMD MI300X (primary, activates when AMD_API_KEY +
AMD_MODEL_ENDPOINT are set) -> Fireworks AI (fallback, FIREWORKS_API_KEY) ->
deterministic template built from the calculation trace (no keys needed).

Architectural rule enforced here: the LLM NEVER calculates. It receives
pre-computed numbers from tax_engine.py and pre-fetched citations from
snippets.py, and returns plain English only.
"""
import logging
import os

import httpx

logger = logging.getLogger("longhand.llm")

AMD_API_KEY = os.getenv("AMD_API_KEY", "")
AMD_MODEL_ENDPOINT = os.getenv("AMD_MODEL_ENDPOINT", "")  # OpenAI-compatible /v1/chat/completions URL
AMD_MODEL = os.getenv("AMD_MODEL", "meta-llama/Llama-3.1-70B-Instruct")

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "")
FIREWORKS_ENDPOINT = "https://api.fireworks.ai/inference/v1/chat/completions"
FIREWORKS_MODEL = os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/gpt-oss-120b")

REQUEST_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

SYSTEM_PROMPT = (
    "You are the explanation layer of Longhand, an auditable US expat tax assistant. "
    "You will receive pre-computed tax results and pre-fetched legal citations. "
    "STRICT RULES: Never perform arithmetic. Never introduce numbers that are not in the "
    "provided results. Never cite laws or figures beyond the provided citations. "
    "Your only job is to explain, speaking directly to the taxpayer as 'you', why the "
    "recommended route was chosen and what the numbers mean for them. "
    "VOICE: Write like a friendly adviser talking across the table, not a report. Short "
    "sentences, everyday words, no jargon without a one-phrase translation. Use a simple "
    "analogy when it genuinely helps (e.g. carried-forward credits are like store credit "
    "you can spend in future years). Never refer to 'the tool', 'the results show', or "
    "'the analysis' — just say it. "
    "DO NOT list the forms to file — the app already shows them separately. "
    "Reference citations by their source names. Keep it under 180 words. "
    "Formatting: you may bold the key dollar figures with **double asterisks**; no other "
    "markdown, no headers, no bullet lists."
)


ASK_SYSTEM_PROMPT = (
    "You are the Q&A layer of Longhand, an auditable US expat tax assistant. "
    "The user has just read a plain-English explanation of their pre-computed tax "
    "result and is asking a follow-up question about it. "
    "STRICT RULES: Never perform arithmetic. Never introduce numbers, law "
    "references, or facts that are not in the provided explanation. If the "
    "question cannot be answered from the explanation, say so plainly and point "
    "out what the explanation does cover. Never give personalised tax advice "
    "beyond restating what the result says. "
    "VOICE: everyday words, short sentences, 2-4 of them, like a friendly adviser. "
    "Translate any jargon in a phrase. You may bold key dollar figures with "
    "**double asterisks**; no other markdown."
)


async def _chat(url: str, api_key: str, model: str, messages: list) -> str:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": 2000, "temperature": 0.3},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def answer_question(question: str, explanation: str, history: list) -> tuple[str, str]:
    """Answer a follow-up question grounded ONLY in the already-generated
    explanation. Returns (answer, provider). Never raises."""
    messages = [
        {"role": "system", "content": ASK_SYSTEM_PROMPT},
        {"role": "user", "content": "Here is the explanation of my result:\n\n" + explanation},
        {"role": "assistant", "content": "Understood — ask me anything about this result."},
        *[{"role": m["role"], "content": m["content"]} for m in history[-6:]],
        {"role": "user", "content": question},
    ]
    if AMD_API_KEY and AMD_MODEL_ENDPOINT:
        try:
            return await _chat(AMD_MODEL_ENDPOINT, AMD_API_KEY, AMD_MODEL, messages), "amd"
        except Exception as exc:
            logger.warning("AMD Q&A call failed, falling back to Fireworks: %s", exc)
    if FIREWORKS_API_KEY:
        try:
            return await _chat(FIREWORKS_ENDPOINT, FIREWORKS_API_KEY, FIREWORKS_MODEL, messages), "fireworks"
        except Exception as exc:
            logger.warning("Fireworks Q&A call failed: %s", exc)
    return (
        "Q&A is unavailable — no LLM API key is configured. The explanation above "
        "and the calculation traces contain everything the engine computed.",
        "deterministic-fallback",
    )


def _build_user_prompt(result: dict) -> str:
    lines = [
        "Explain this pre-computed result to the taxpayer.",
        "",
        f"Recommended route: {result['recommended_route']}",
        f"Reason: {result['recommendation_reason']}",
        f"Estimated US tax owed: ${result['us_tax_impact']:,.2f}",
        "",
        f"FEIE route: eligible={result['feie']['eligible']}, US tax ${result['feie']['us_tax_owed']:,.2f} — {result['feie']['detail']}",
        f"FTC route: eligible={result['ftc']['eligible']}, US tax ${result['ftc']['us_tax_owed']:,.2f} — {result['ftc']['detail']}",
        "",
        "Filing flags:",
    ]
    for f in result["filing_flags"]:
        lines.append(f"- {f['form']}: {'REQUIRED' if f['required'] else 'not required'} — {f['reason']}")
    lines.append("")
    lines.append("Citations you may reference (do not add others):")
    for c in result["citations"]:
        lines.append(f"- [{c['source']}] {c['reference']}: {c['text']}")
    return "\n".join(lines)


async def _call_openai_compatible(url: str, api_key: str, model: str, user_prompt: str) -> str:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                # generous: reasoning models (gpt-oss) spend tokens thinking
                # before writing, and a truncated explanation reads as broken
                "max_tokens": 2500,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def _deterministic_fallback(result: dict) -> str:
    """No-keys degradation: readable summary assembled purely from engine output."""
    parts = [
        f"Recommended route: {result['recommended_route']}. {result['recommendation_reason']}",
        f"Estimated US tax owed: ${result['us_tax_impact']:,.2f}.",
        f"FEIE route: {result['feie']['detail']}" if result["feie"]["eligible"]
        else f"FEIE route: {result['feie']['detail']}",
        f"FTC route: {result['ftc']['detail']}",
    ]
    required = [f["form"] for f in result["filing_flags"] if f["required"]]
    if required:
        parts.append("Forms to file: " + ", ".join(required) + ".")
    parts.append("(LLM explanation unavailable — no API keys configured; showing deterministic trace summary.)")
    return " ".join(parts)


async def explain(result: dict) -> tuple[str, str]:
    """Return (explanation, provider). Tries AMD, then Fireworks, then falls back
    to a deterministic summary. Never raises."""
    user_prompt = _build_user_prompt(result)

    if AMD_API_KEY and AMD_MODEL_ENDPOINT:
        try:
            text = await _call_openai_compatible(AMD_MODEL_ENDPOINT, AMD_API_KEY, AMD_MODEL, user_prompt)
            return text, "amd"
        except Exception as exc:
            logger.warning("AMD MI300X call failed, falling back to Fireworks: %s", exc)

    if FIREWORKS_API_KEY:
        try:
            text = await _call_openai_compatible(FIREWORKS_ENDPOINT, FIREWORKS_API_KEY, FIREWORKS_MODEL, user_prompt)
            return text, "fireworks"
        except Exception as exc:
            logger.warning("Fireworks call failed, degrading to deterministic summary: %s", exc)

    return _deterministic_fallback(result), "deterministic-fallback"

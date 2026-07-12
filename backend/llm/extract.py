"""Identity extraction from an ID document image via a vision LLM.

Provider chain mirrors the explanation layer: AMD MI300X first (when
AMD_API_KEY + AMD_MODEL_ENDPOINT + AMD_VISION_MODEL are set), Fireworks AI as
the fallback (FIREWORKS_API_KEY). Both are OpenAI-compatible /v1/chat/completions
endpoints, so the same multimodal message shape works for either.

This is OCR of identity text, not tax math — the architectural law holds: no
LLM ever computes a number, and every extracted value is shown to the user for
review before it reaches a form. The image is held in memory for the duration
of the request only.
"""
import base64
import io
import json
import logging
import os
import re
from typing import Optional

import httpx
from PIL import Image

logger = logging.getLogger("longhand.extract")

FIREWORKS_ENDPOINT = "https://api.fireworks.ai/inference/v1/chat/completions"

REQUEST_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

# Vision latency scales with image size: a full-resolution document photo can
# triple the model's read-and-reason time. Identity text survives downscaling
# to ~1100px fine, and JPEG is a fraction of PNG's bytes.
MAX_DIMENSION = 1100

FIELDS = [
    "first_name", "last_name", "street_address", "city", "state",
    "zip_code", "foreign_country", "foreign_province", "foreign_postal_code",
]

# Phrasing matters for latency here: instructions like "do not deliberate"
# made kimi-k2p6 spill its reasoning into the answer channel and ramble until
# the token cap (~40s). This short "reply with ONLY..." form keeps reasoning
# in its hidden channel and the answer to one JSON object (~6s).
PROMPT = (
    "Read the name and address printed on this document (passport, driving "
    "licence, residence permit, utility bill, or similar). Reply with ONLY a "
    f"JSON object with keys {', '.join(FIELDS)}. "
    "state and zip_code are for US addresses only; for an address outside the "
    "US put the postcode in foreign_postal_code and leave zip_code empty. "
    'Use "" for anything not printed on the document — never guess; passports '
    "typically show only names. No explanation."
)


def _shrink(image_bytes: bytes, mime: str) -> tuple[bytes, str]:
    """Downscale + JPEG-re-encode the upload for faster extraction.
    Falls back to the original bytes for formats Pillow can't open."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, mime


def _messages(data_url: str, prefill: bool) -> list:
    msgs = [{
        "role": "user",
        "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }]
    if prefill:
        # Prefilling the reply with the opening brace makes a reasoning model
        # continue the JSON directly instead of thinking first — measured
        # ~1.5s vs ~20-40s without it. Only used for Fireworks (kimi); AMD's
        # Llama vision models don't ramble and some servers reject a trailing
        # assistant message.
        msgs.append({"role": "assistant", "content": "{"})
    return msgs


async def _call_vision(url: str, api_key: str, model: str, data_url: str, prefill: bool) -> str:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 600,
                "temperature": 0,
                "messages": _messages(data_url, prefill),
            },
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    if prefill and not text.lstrip().startswith("{"):
        text = "{" + text  # restore the prefilled brace for the parser
    return text


async def extract_identity(image_bytes: bytes, mime: str) -> Optional[dict]:
    """Return the extracted identity fields, or None when no provider is
    configured (or every configured provider failed). Tries AMD MI300X first,
    then Fireworks."""
    small_bytes, small_mime = _shrink(image_bytes, mime)
    data_url = f"data:{small_mime};base64,{base64.b64encode(small_bytes).decode()}"

    amd_key = os.getenv("AMD_API_KEY", "")
    amd_endpoint = os.getenv("AMD_MODEL_ENDPOINT", "")
    # A vision-capable model must be named explicitly: the text AMD_MODEL
    # (e.g. Llama-3.1-70B-Instruct) can't accept images, so we don't inherit it.
    amd_model = os.getenv("AMD_VISION_MODEL", "")
    if amd_key and amd_endpoint and amd_model:
        try:
            text = await _call_vision(amd_endpoint, amd_key, amd_model, data_url, prefill=False)
            raw = _find_json(text)
            if raw is not None:
                logger.info("ID extraction via AMD MI300X")
                return _normalize(raw)
            logger.warning("AMD vision returned no parseable JSON, falling back to Fireworks")
        except Exception as exc:
            logger.warning("AMD vision extraction failed, falling back to Fireworks: %s", exc)

    fw_key = os.getenv("FIREWORKS_API_KEY", "")
    if fw_key:
        # Deliberately NOT falling back to FIREWORKS_MODEL: that variable selects
        # the text explanation model (gpt-oss), which cannot accept images —
        # inheriting it silently breaks extraction in deployments that set it.
        model = os.getenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/kimi-k2p6")
        try:
            text = await _call_vision(FIREWORKS_ENDPOINT, fw_key, model, data_url, prefill=True)
            logger.info("ID extraction via Fireworks")
            return _normalize(_find_json(text) or {})
        except Exception as exc:
            logger.warning("Fireworks vision extraction failed: %s", exc)

    return None


def _find_json(text: str) -> Optional[dict]:
    """Pull the answer JSON object out of the model reply, defensively.

    Reasoning models may narrate before answering, so prefer the LAST flat
    JSON object that carries any of our keys, falling back to a greedy match.
    Returns None when nothing parseable is found.
    """
    candidates = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    greedy = re.search(r"\{.*\}", text, re.DOTALL)
    if greedy:
        candidates.append(greedy.group(0))
    for block in reversed(candidates):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and any(k in parsed for k in FIELDS):
            return parsed
    return None


def _normalize(raw: dict) -> dict:
    """Coerce a parsed reply into the exact FIELDS shape, all strings, trimmed."""
    return {k: str(raw.get(k, "") or "").strip() for k in FIELDS}

"""Identity extraction from an ID document image via a vision LLM.

Sends the image to Fireworks (gemma-3 is multimodal) and asks for a strict
JSON identity block. This is OCR of identity text, not tax math — the
architectural law holds: no LLM ever computes a number, and every extracted
value is shown to the user for review before it reaches a form. The image is
held in memory for the duration of the request only.
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

# Vision latency scales with image size: a full-resolution document photo can
# triple the model's read-and-reason time. Identity text survives downscaling
# to ~1100px fine, and JPEG is a fraction of PNG's bytes.
MAX_DIMENSION = 1100


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

FIREWORKS_ENDPOINT = "https://api.fireworks.ai/inference/v1/chat/completions"

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


async def extract_identity(image_bytes: bytes, mime: str) -> Optional[dict]:
    """Returns the extracted identity fields, or None when no key is configured."""
    api_key = os.getenv("FIREWORKS_API_KEY", "")
    if not api_key:
        return None
    # Deliberately NOT falling back to FIREWORKS_MODEL: that variable selects
    # the text explanation model (gpt-oss), which cannot accept images —
    # inheriting it silently breaks extraction in deployments that set it.
    model = os.getenv("FIREWORKS_VISION_MODEL", "accounts/fireworks/models/kimi-k2p6")
    small_bytes, small_mime = _shrink(image_bytes, mime)
    data_url = f"data:{small_mime};base64,{base64.b64encode(small_bytes).decode()}"
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            FIREWORKS_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 600,
                "temperature": 0,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                    # Prefilling the reply with the opening brace makes the
                    # reasoning model continue the JSON directly instead of
                    # thinking first — measured ~1.5s vs ~20-40s without it.
                    {"role": "assistant", "content": "{"},
                ],
            },
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        if not text.lstrip().startswith("{"):
            text = "{" + text  # restore the prefilled brace for the parser
    return _parse_fields(text)


def _parse_fields(text: str) -> dict:
    """Pull the JSON object out of the model reply, defensively.

    Reasoning models may narrate before answering, so prefer the LAST flat
    JSON object in the reply (the answer), falling back to a greedy match.
    """
    raw: dict = {}
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
            raw = parsed
            break
    if not raw:
        logger.warning("Vision model returned no parseable JSON")
    return {k: str(raw.get(k, "") or "").strip() for k in FIELDS}

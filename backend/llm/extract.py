"""Identity extraction from an ID document image via a vision LLM.

Sends the image to Fireworks (gemma-3 is multimodal) and asks for a strict
JSON identity block. This is OCR of identity text, not tax math — the
architectural law holds: no LLM ever computes a number, and every extracted
value is shown to the user for review before it reaches a form. The image is
held in memory for the duration of the request only.
"""
import base64
import json
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger("longhand.extract")

FIREWORKS_ENDPOINT = "https://api.fireworks.ai/inference/v1/chat/completions"

FIELDS = [
    "first_name", "last_name", "street_address", "city", "state",
    "zip_code", "foreign_country", "foreign_province", "foreign_postal_code",
]

PROMPT = (
    "You are reading a photo of an identity document (passport, driving licence, "
    "residence permit, or similar). Extract only what is visibly printed on the "
    "document. Respond with a single JSON object and nothing else, using exactly "
    f"these keys: {', '.join(FIELDS)}. Use an empty string for anything not shown "
    "on the document. Do not guess or infer values that are not printed. "
    "Passports typically show only names — that is a correct extraction."
)


async def extract_identity(image_bytes: bytes, mime: str) -> Optional[dict]:
    """Returns the extracted identity fields, or None when no key is configured."""
    api_key = os.getenv("FIREWORKS_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv(
        "FIREWORKS_VISION_MODEL",
        os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/gemma-3-27b-it"),
    )
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            FIREWORKS_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 400,
                "temperature": 0,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }],
            },
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
    return _parse_fields(text)


def _parse_fields(text: str) -> dict:
    """Pull the JSON object out of the model reply, defensively."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    raw: dict = {}
    if match:
        try:
            raw = json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("Vision model returned unparseable JSON")
    return {k: str(raw.get(k, "") or "").strip() for k in FIELDS}

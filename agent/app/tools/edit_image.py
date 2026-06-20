"""AI image generation + editing via Google Gemini (gemini-2.5-flash-image).

Two modes:
- generate(prompt)               text -> image
- edit(image_bytes, instruction) image + instruction -> edited image  (img2img)

Used for the EDIT capability: "make the product photo cleaner / less hefty".
Edited assets are stored in-process and served by GET /assets/{id}; the tool
returns the URL + emits an artifact event so the channel/UI can render it.
"""

from __future__ import annotations

import base64
import hashlib
import time
from typing import Any

import httpx

from app.config import get_settings

from .registry import registry

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# id -> (mime, bytes). In-process asset store; served by /assets/{id}.
ASSETS: dict[str, tuple[str, bytes]] = {}
LAST_IMAGE: dict[str, str] = {}  # participant/brand -> last asset url


def is_configured() -> bool:
    return get_settings().has_gemini()


_ASSET_CAP = 60


def _store(mime: str, data: bytes) -> str:
    aid = hashlib.sha1(data[:2048] + str(time.time()).encode()).hexdigest()[:16]
    ASSETS[aid] = (mime, data)
    # keep memory bounded — drop oldest beyond the cap
    while len(ASSETS) > _ASSET_CAP:
        ASSETS.pop(next(iter(ASSETS)))
    ext = "png" if "png" in mime else ("jpg" if "jpeg" in mime else "img")
    return f"/assets/{aid}.{ext}"


def _extract_image(resp_json: dict[str, Any]) -> tuple[str, bytes] | None:
    for cand in resp_json.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                return mime, base64.b64decode(inline["data"])
    return None


async def _generate_content(parts: list[dict[str, Any]]) -> tuple[str, bytes]:
    s = get_settings()
    if not s.has_gemini():
        raise RuntimeError("GEMINI_API_KEY not set")
    url = f"{_BASE}/{s.gemini_image_model}:generateContent?key={s.gemini_api_key}"
    body = {
        "contents": [{"parts": parts}],
        # ensure the model returns an image (required by image-gen models)
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(url, json=body)
        r.raise_for_status()
        img = _extract_image(r.json())
    if not img:
        raise RuntimeError("Gemini returned no image")
    return img


async def generate(prompt: str) -> tuple[str, bytes]:
    return await _generate_content([{"text": prompt}])


async def edit(image_bytes: bytes, instruction: str,
               *, mime: str = "image/png") -> tuple[str, bytes]:
    b64 = base64.b64encode(image_bytes).decode()
    return await _generate_content([
        {"text": instruction},
        {"inlineData": {"mimeType": mime, "data": b64}},
    ])


async def _fetch(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.content, r.headers.get("content-type", "image/png")


@registry.tool(
    name="edit_product_image",
    description=(
        "Generate or edit a product image with AI. If image_url is given, edit "
        "that image per the instruction (e.g. 'make it cleaner, less hefty, "
        "better lighting'); otherwise generate a new product image from the "
        "instruction. Returns a URL to the result."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "instruction": {"type": "string",
                            "description": "What to make / how to edit it."},
            "image_url": {"type": "string",
                          "description": "Optional source image to edit."},
        },
        "required": ["instruction"],
    },
)
async def edit_product_image(instruction: str, image_url: str | None = None,
                             participant: str = "web") -> str:
    if not is_configured():
        return "Image editing unavailable: GEMINI_API_KEY not set."
    try:
        if image_url:
            src, mime = await _fetch(image_url)
            res_mime, data = await edit(src, instruction, mime=mime)
        else:
            res_mime, data = await generate(instruction)
    except Exception as exc:  # noqa: BLE001
        return f"Image edit failed: {exc}"
    url = _store(res_mime, data)
    LAST_IMAGE[participant] = url
    return f"Image ready: {url} ({len(data)} bytes) — {instruction}"

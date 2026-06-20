"""V1 EDIT — image (Gemini) + copy tools. Offline + live-skip."""

import base64
import os

import pytest

from app.tools import edit_copy  # noqa: F401 - registers edit_copy
from app.tools import edit_image
from app.tools.registry import registry

# 1x1 transparent PNG
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def test_tools_registered():
    assert "edit_product_image" in registry.names()
    assert "edit_copy" in registry.names()


def test_extract_image_parses_inline_data():
    b64 = base64.b64encode(_PNG).decode()
    resp = {"candidates": [{"content": {"parts": [
        {"text": "here"}, {"inlineData": {"mimeType": "image/png", "data": b64}}]}}]}
    out = edit_image._extract_image(resp)
    assert out and out[0] == "image/png" and out[1] == _PNG


def test_store_and_url():
    url = edit_image._store("image/png", _PNG)
    assert url.startswith("/assets/") and url.endswith(".png")
    aid = url.split("/assets/")[1].rsplit(".", 1)[0]
    assert edit_image.ASSETS[aid] == ("image/png", _PNG)


@pytest.mark.asyncio
async def test_edit_image_degrades_without_key():
    # conftest doesn't touch GEMINI; assert the no-key message when unset
    if edit_image.is_configured():
        pytest.skip("GEMINI configured — degrade path not applicable")
    out = await edit_image.edit_product_image("a clean studio photo of a flute")
    assert "GEMINI_API_KEY not set" in out


@pytest.mark.live
@pytest.mark.skipif(not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
                    reason="no Gemini key")
@pytest.mark.asyncio
async def test_gemini_generate_live():
    mime, data = await edit_image.generate(
        "A minimal, clean studio product photo of a silver concert flute on white.")
    assert data and len(data) > 1000 and mime.startswith("image/")


def test_asset_endpoint_serves():
    from fastapi.testclient import TestClient

    from app.main import app

    url = edit_image._store("image/png", _PNG)
    aid = url.split("/assets/")[1]
    r = TestClient(app).get(f"/assets/{aid}")
    assert r.status_code == 200 and r.content == _PNG

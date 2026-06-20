"""Real Browserbase integration: create a cloud browser session, drive it over
CDP with Playwright (no local Chromium needed — the browser runs on
Browserbase), and return page content. Used to fetch sources that block
plain HTTP clients (Reddit, X, LinkedIn).

No-op when keys are absent: callers fall back to keyless sources.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

import httpx

from app.config import get_settings

logger = logging.getLogger("twocustomer.browserbase")

_API = "https://api.browserbase.com/v1"


async def _post_session(api_key: str, body: dict) -> str | None:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{_API}/sessions",
            headers={"X-BB-API-Key": api_key, "Content-Type": "application/json"},
            json=body,
        )
        r.raise_for_status()
        return r.json().get("connectUrl")


async def _create_session() -> str | None:
    """Create a Browserbase session, return the CDP connect URL (or None).

    Tries residential proxies + captcha solving first (beats Reddit/X anti-bot
    walls). Those are paid features, so on 402 we fall back to a plain session,
    which still works for sources that don't block datacenter IPs (news, RSS).
    """
    s = get_settings()
    if not s.has_browserbase():
        return None
    pid = s.browserbase_project_id
    try:
        return await _post_session(
            s.browserbase_api_key,
            {"projectId": pid, "proxies": True,
             "browserSettings": {"solveCaptchas": True}},
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 402:
            logger.warning("browserbase session create failed: %s", exc)
            return None
        # Paid proxy not on this plan — retry with a plain session.
    except Exception as exc:  # noqa: BLE001
        logger.warning("browserbase session create failed: %s", exc)
        return None
    try:
        return await _post_session(s.browserbase_api_key, {"projectId": pid})
    except Exception as exc:  # noqa: BLE001
        logger.warning("browserbase plain session create failed: %s", exc)
        return None


@asynccontextmanager
async def _page(connect_url: str):
    """Connect Playwright to the remote Browserbase browser over CDP."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(connect_url)
        try:
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            yield page
        finally:
            await browser.close()


async def fetch_raw(url: str, *, timeout_ms: int = 25_000) -> str | None:
    """Navigate to ``url`` in a real Browserbase browser and return the RAW
    response body (un-rendered) — correct for JSON/XML/RSS endpoints.
    Returns None when Browserbase is unconfigured or the fetch fails."""
    connect = await _create_session()
    if not connect:
        return None
    try:
        async with _page(connect) as page:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if resp is None:
                return None
            return await resp.text()
    except Exception as exc:  # noqa: BLE001
        logger.warning("browserbase fetch failed for %s: %s", url, exc)
        return None


async def fetch_text(url: str, *, timeout_ms: int = 25_000) -> str | None:
    """Navigate to ``url`` and return rendered body text (for HTML pages /
    block-page detection)."""
    connect = await _create_session()
    if not connect:
        return None
    try:
        async with _page(connect) as page:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            return await page.inner_text("body")
    except Exception as exc:  # noqa: BLE001
        logger.warning("browserbase fetch failed for %s: %s", url, exc)
        return None


async def fetch_json(url: str, *, timeout_ms: int = 25_000) -> dict | list | None:
    """Fetch a JSON endpoint through Browserbase (for hosts that 403 plain
    clients but serve JSON to a real browser, e.g. Reddit)."""
    body = await fetch_raw(url, timeout_ms=timeout_ms)
    if not body:
        return None
    try:
        return json.loads(body)
    except (json.JSONDecodeError, ValueError):
        # The browser may wrap JSON in a <pre>; inner_text already strips tags,
        # but guard against leading/trailing noise.
        start = body.find("{")
        if start == -1:
            start = body.find("[")
        if start == -1:
            return None
        try:
            return json.loads(body[start:])
        except (json.JSONDecodeError, ValueError):
            return None

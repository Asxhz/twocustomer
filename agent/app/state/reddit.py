"""Reddit OAuth API client (app-only).

Reddit blocks all unauthenticated requests (403 + a challenge page) regardless
of IP or User-Agent, so the public ``.json`` endpoints can't be scraped
directly. The supported path is the OAuth API: exchange a free script app's
client id/secret for an app-only bearer token, then read ``oauth.reddit.com``
(which returns the same JSON shape as the public ``.json`` endpoints).

Create the app at https://www.reddit.com/prefs/apps (type "script") and set
REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET. No-op (returns None / []) without them.
"""

from __future__ import annotations

import logging
import time

import httpx

from app.config import get_settings

logger = logging.getLogger("twocustomer.reddit")

_UA = "twocustomer/0.1 (brand monitoring)"
_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_API = "https://oauth.reddit.com"

# Simple in-process token cache: (token, expires_epoch).
_token: tuple[str, float] | None = None


def is_configured() -> bool:
    s = get_settings()
    return bool(s.reddit_client_id and s.reddit_client_secret)


async def _get_token() -> str | None:
    """Fetch (and cache) an app-only OAuth token. None when unconfigured."""
    global _token
    if not is_configured():
        return None
    if _token and _token[1] > time.time() + 30:
        return _token[0]
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                _TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(s.reddit_client_id, s.reddit_client_secret),
                headers={"User-Agent": _UA},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("reddit token fetch failed: %s", exc)
        return None
    tok = data.get("access_token")
    if not tok:
        return None
    _token = (tok, time.time() + float(data.get("expires_in", 3600)))
    return tok


async def search(query: str, *, limit: int = 10, sort: str = "new") -> list[dict]:
    """Search Reddit via the OAuth API. Returns the raw post dicts (``t3``
    ``data`` objects). Empty list when unconfigured or on failure."""
    token = await _get_token()
    if not token:
        return []
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(
                f"{_API}/search",
                params={"q": query, "limit": limit, "sort": sort,
                        "type": "link", "raw_json": 1},
                headers={"Authorization": f"Bearer {token}", "User-Agent": _UA},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("reddit search failed: %s", exc)
        return []
    return [child.get("data", {})
            for child in data.get("data", {}).get("children", [])]

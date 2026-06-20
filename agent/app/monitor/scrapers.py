"""Lightweight scrapers. Reddit uses the public JSON API (no key, real signal);
X/LinkedIn/web go through the TwoCustomer engine's Browserbase scrapers when keys
are present. Each returns a list[Mention] in the common schema.
"""

from __future__ import annotations

import httpx

from .mention import Mention, normalize

_UA = "TwoCustomer/0.1 (+https://twocustomer.app)"


async def hn_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Search Hacker News via Algolia (public, keyless, reliable) — real signal
    for the keyless demo. Returns the common Mention schema (platform='hn')."""
    url = "https://hn.algolia.com/api/v1/search_by_date"
    params = {"query": query, "tags": "(story,comment)", "hitsPerPage": str(limit)}
    out: list[Mention] = []
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": _UA}) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return out
    for h in data.get("hits", []):
        text = (h.get("title") or h.get("comment_text") or h.get("story_text") or "")
        if not text.strip():
            continue
        oid = str(h.get("objectID", ""))
        out.append(
            normalize(
                "hn",
                external_id=oid,
                text=text.strip(),
                author=h.get("author", ""),
                url=f"https://news.ycombinator.com/item?id={oid}",
                ts=int(h.get("created_at_i", 0)) * 1000,
                engagement=float(h.get("points") or 0) + float(h.get("num_comments") or 0),
            )
        )
    return out


async def news_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Brand mentions from Google News, fetched through a real Browserbase
    browser (consistent egress, JS-capable). Parses the RSS feed. Returns []
    when Browserbase is unconfigured — never fabricated."""
    from urllib.parse import quote

    import defusedxml.ElementTree as ET  # XXE-safe parser for untrusted RSS

    from app.state.browserbase import fetch_raw

    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
    out: list[Mention] = []
    raw = await fetch_raw(url, timeout_ms=35_000)
    if not raw:
        return out
    try:
        root = ET.fromstring(raw)
    except Exception:  # noqa: BLE001 - malformed/blocked RSS
        return out
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        link = (item.findtext("link") or "").strip()
        source = ""
        src_el = item.find("source")
        if src_el is not None and src_el.text:
            source = src_el.text.strip()
        # RFC-822 pubDate → epoch ms (best-effort).
        ts = 0
        pub = item.findtext("pubDate")
        if pub:
            try:
                from email.utils import parsedate_to_datetime

                ts = int(parsedate_to_datetime(pub).timestamp() * 1000)
            except (TypeError, ValueError):
                ts = 0
        out.append(
            normalize(
                "news",
                external_id=link or title,
                text=title,
                author=source or "news",
                url=link,
                ts=ts,
                engagement=0.0,
            )
        )
        if len(out) >= limit:
            break
    return out


async def reddit_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Search Reddit. Reddit blocks unauthenticated HTTP clients (403), so this
    routes through a real Browserbase browser when keys are present. Without
    Browserbase configured it returns [] (no fake data) — HN carries the
    keyless demo."""
    from urllib.parse import urlencode

    from app.state.browserbase import fetch_json

    params = {"q": query, "limit": str(limit), "sort": "new", "raw_json": "1"}
    url = f"https://www.reddit.com/search.json?{urlencode(params)}"
    out: list[Mention] = []
    data = await fetch_json(url)
    if not isinstance(data, dict):
        return out
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        out.append(
            normalize(
                "reddit",
                external_id=d.get("id", ""),
                text=(d.get("title", "") + " " + d.get("selftext", "")).strip(),
                author=f"u/{d.get('author', '')}",
                url="https://reddit.com" + d.get("permalink", ""),
                ts=int(d.get("created_utc", 0)) * 1000,
                engagement=float(d.get("score", 0)) + float(d.get("num_comments", 0)),
            )
        )
    return out


# Default scrapers:
#   hn_search   — keyless, always live (Algolia)
#   news_search — live via Browserbase (Google News RSS); [] without keys
# reddit_search is intentionally NOT default: Reddit hard-blocks datacenter IPs,
# so it needs a Browserbase residential proxy (paid). It stays callable for
# deployments on that tier. Nothing is ever fabricated.
DEFAULT_SCRAPERS = [hn_search, news_search]

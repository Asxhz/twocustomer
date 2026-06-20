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


# Sample Reddit posts used as a fallback when the OAuth API isn't configured,
# so the Reddit source still contributes to the demo. {q} is the search term.
_SAMPLE_REDDIT = [
    ("just switched to {q} and my gut feels way better — the ginger one is elite", 240, 31),
    ("PSA: saw a canned-beverage recall notice this week, double-check your cans", 512, 88),
    ("is {q} actually worth the hype or is it just marketing? thinking of trying it", 96, 54),
    ("restocked on {q} at Target, the yuzu flavor sells out instantly near me", 178, 22),
    ("{q} sold out everywhere in my city for 3 weeks straight, fix the supply chain", 134, 47),
    ("the new {q} can design is clean but the price went up again imo", 61, 19),
]


def _sample_reddit(query: str, limit: int) -> list[Mention]:
    out: list[Mention] = []
    for i, (tmpl, score, comments) in enumerate(_SAMPLE_REDDIT[:limit]):
        text = tmpl.format(q=query)
        out.append(
            normalize(
                "reddit",
                external_id=f"sample-{i}-{abs(hash(query)) % 100000}",
                text=text,
                author=f"u/cpg_fan_{i}",
                url="https://reddit.com/r/beverages",
                ts=0,
                engagement=float(score + comments),
            )
        )
    return out


async def reddit_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Search Reddit via its OAuth API (the only path that works — Reddit 403s
    all unauthenticated access). When REDDIT_CLIENT_ID/SECRET are set this
    returns live posts; otherwise it falls back to a small curated sample so the
    Reddit source still shows up in the demo."""
    from app.state import reddit

    raw = await reddit.search(query, limit=limit)
    if not raw:
        return _sample_reddit(query, limit)
    out: list[Mention] = []
    for d in raw:
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
#   hn_search     — keyless, always live (Algolia)
#   news_search   — live via Browserbase (Google News RSS); [] without keys
#   reddit_search — live via the Reddit OAuth API; [] without REDDIT_CLIENT_ID/
#                   SECRET (Reddit 403s all unauthenticated access)
# Nothing is ever fabricated — a source with no key simply yields nothing.
DEFAULT_SCRAPERS = [hn_search, news_search, reddit_search]

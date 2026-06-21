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
    """Search Reddit via its OAuth API (the only path that works; Reddit 403s all
    unauthenticated access). Returns live posts when REDDIT_CLIENT_ID/SECRET are
    set, else nothing. Never fabricated."""
    from app.state import reddit

    raw = await reddit.search(query, limit=limit)
    if not raw:
        return []
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


async def _bb_text(url: str) -> str:
    """Fetch rendered page text through Browserbase. Empty string on any block."""
    try:
        from app.state.browserbase import fetch_text

        return (await fetch_text(url, timeout_ms=30_000)) or ""
    except Exception:  # noqa: BLE001
        return ""


async def x_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Real attempt at X/Twitter chatter via a public Nitter mirror over
    Browserbase. X blocks unauthenticated search, so this returns nothing when
    blocked. Never fabricated."""
    from urllib.parse import quote

    text = await _bb_text(f"https://nitter.net/search?q={quote(query)}&f=tweets")
    if not text or "Tweet" not in text and "tweet" not in text:
        return []
    out: list[Mention] = []
    for i, line in enumerate(t for t in text.splitlines() if query.lower() in t.lower()):
        clean = line.strip()
        if len(clean) < 20:
            continue
        out.append(normalize("x", external_id=f"x-{abs(hash(clean)) % 1000000}",
                             text=clean[:300], author="x", url="https://x.com",
                             ts=0, engagement=0.0))
        if len(out) >= limit:
            break
    return out


async def linkedin_search(query: str, *, limit: int = 10) -> list[Mention]:
    """Real attempt at LinkedIn posts via Browserbase. LinkedIn requires login,
    so this returns nothing when blocked. Never fabricated."""
    from urllib.parse import quote

    text = await _bb_text(f"https://www.linkedin.com/search/results/content/?keywords={quote(query)}")
    if not text or "linkedin.com/authwall" in text.lower() or "sign in" in text.lower():
        return []
    out: list[Mention] = []
    for line in (t for t in text.splitlines() if query.lower() in t.lower()):
        clean = line.strip()
        if len(clean) < 20:
            continue
        out.append(normalize("linkedin", external_id=f"li-{abs(hash(clean)) % 1000000}",
                             text=clean[:300], author="linkedin",
                             url="https://linkedin.com", ts=0, engagement=0.0))
        if len(out) >= limit:
            break
    return out


# Default scrapers. Each yields real signal or nothing; nothing is fabricated.
#   hn_search       keyless, always live (Algolia)
#   news_search     live via Browserbase (Google News RSS); [] without keys
#   reddit_search   live via the Reddit OAuth API; [] without REDDIT_CLIENT_ID/SECRET
#   x_search        real attempt via Browserbase/Nitter; [] when blocked
#   linkedin_search real attempt via Browserbase; [] when blocked (login wall)
DEFAULT_SCRAPERS = [hn_search, news_search, reddit_search, x_search, linkedin_search]

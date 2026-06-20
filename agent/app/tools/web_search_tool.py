"""web_search — let the agent research the open web.

Uses the already-configured Browserbase browser to fetch a DuckDuckGo HTML
results page and parse the top results (title, url, snippet). No extra API key.
Falls back to a plain HTTP fetch when Browserbase is unconfigured.
"""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.config import get_settings

from .registry import registry

_DDG = "https://html.duckduckgo.com/html/?q="
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

_RESULT = re.compile(
    r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
_SNIPPET = re.compile(
    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)


def _strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _clean_url(href: str) -> str:
    # DDG wraps results in /l/?uddg=<encoded-real-url>
    if "uddg=" in href:
        q = parse_qs(urlparse(href).query)
        if q.get("uddg"):
            return unquote(q["uddg"][0])
    return href if href.startswith("http") else "https:" + href


def parse_results(html_text: str, limit: int) -> list[dict[str, str]]:
    links = _RESULT.findall(html_text or "")
    snips = _SNIPPET.findall(html_text or "")
    out: list[dict[str, str]] = []
    for i, (href, title) in enumerate(links):
        if "y.js" in href or "ad_provider" in href or "ad_domain" in href:
            continue  # skip DDG ad results
        out.append({
            "title": _strip(title),
            "url": _clean_url(href),
            "snippet": _strip(snips[i]) if i < len(snips) else "",
        })
        if len(out) >= limit:
            break
    return out


async def _fetch(url: str) -> str | None:
    s = get_settings()
    if s.has_browserbase():
        from app.state.browserbase import fetch_raw

        body = await fetch_raw(url, timeout_ms=30_000)
        if body:
            return body
    # plain fallback
    try:
        async with httpx.AsyncClient(timeout=20, headers={"User-Agent": _UA},
                                     follow_redirects=True) as c:
            r = await c.get(url)
            return r.text if r.status_code == 200 else None
    except Exception:  # noqa: BLE001
        return None


@registry.tool(
    name="web_search",
    description=(
        "Search the open web and return the top results (title, url, snippet). "
        "Use this to research a brand, competitor, market, news, or a coding "
        "question before acting."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
            "num_results": {"type": "integer",
                            "description": "How many results (default 5)."},
        },
        "required": ["query"],
    },
)
async def web_search(query: str, num_results: int = 5) -> str:
    from urllib.parse import quote

    limit = max(1, min(int(num_results or 5), 8))
    body = await _fetch(_DDG + quote(query))
    results = parse_results(body or "", limit)
    if not results:
        return f"No web results for '{query}'."
    lines = [f"Web results for '{query}':"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']} — {r['url']}\n   {r['snippet'][:200]}")
    return "\n".join(lines)

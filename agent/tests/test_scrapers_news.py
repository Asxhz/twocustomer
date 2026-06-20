"""news_search RSS parsing (offline) + Browserbase-off safety."""

import app.state.browserbase as bb
from app.monitor import scrapers

_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>Aurora Drinks launches new flavor</title>
    <link>https://news.example/aurora-1</link>
    <pubDate>Mon, 02 Jun 2025 14:00:00 GMT</pubDate>
    <source url="https://nyt.com">The New York Times</source>
  </item>
  <item>
    <title>Aurora recall sparks refund demands</title>
    <link>https://news.example/aurora-2</link>
    <pubDate>not-a-date</pubDate>
  </item>
  <item><title></title><link>https://news.example/empty</link></item>
</channel></rss>"""


def test_news_search_parses_rss(monkeypatch):
    async def fake_fetch_raw(url, **kw):
        return _RSS

    monkeypatch.setattr(bb, "fetch_raw", fake_fetch_raw)
    import asyncio

    out = asyncio.run(scrapers.news_search("aurora", limit=10))
    assert len(out) == 2  # empty-title item skipped
    assert out[0].platform == "news"
    assert out[0].author == "The New York Times"
    assert out[0].url == "https://news.example/aurora-1"
    assert out[0].ts > 0
    assert out[1].ts == 0  # bad pubDate degrades to 0, not a crash


def test_news_search_empty_without_browserbase(monkeypatch):
    async def none_fetch(url, **kw):
        return None

    monkeypatch.setattr(bb, "fetch_raw", none_fetch)
    import asyncio

    assert asyncio.run(scrapers.news_search("aurora")) == []


def test_news_not_default_fabricated():
    # reddit is intentionally excluded from defaults; news + hn only.
    from app.monitor.scrapers import DEFAULT_SCRAPERS, hn_search, news_search

    assert DEFAULT_SCRAPERS == [hn_search, news_search]

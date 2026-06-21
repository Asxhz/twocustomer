"""Reddit OAuth scraper — parsing + graceful no-credentials behavior."""

import asyncio

from app.config import get_settings
from app.monitor import scrapers
from app.state import reddit

_SAMPLE = [
    {"id": "abc1", "title": "Olipop is my favorite prebiotic soda",
     "selftext": "tastes great", "author": "sodafan",
     "permalink": "/r/soda/comments/abc1/", "created_utc": 1_700_000_000,
     "score": 42, "num_comments": 8},
    {"id": "abc2", "title": "Anyone else see the recall?", "selftext": "",
     "author": "watcher", "permalink": "/r/cpg/comments/abc2/",
     "created_utc": 1_700_000_100, "score": 5, "num_comments": 2},
]


def test_reddit_search_parses(monkeypatch):
    async def fake_search(query, *, limit=10, sort="new"):
        return _SAMPLE

    monkeypatch.setattr(reddit, "search", fake_search)
    out = asyncio.run(scrapers.reddit_search("olipop", limit=5))
    assert len(out) == 2
    m = out[0]
    assert m.platform == "reddit"
    assert m.external_id == "abc1"
    assert m.author == "u/sodafan"
    assert m.url == "https://reddit.com/r/soda/comments/abc1/"
    assert m.ts == 1_700_000_000 * 1000
    assert m.engagement == 50.0  # score 42 + comments 8


def test_reddit_search_empty_without_creds(monkeypatch):
    monkeypatch.setattr(get_settings(), "reddit_client_id", "", raising=False)
    monkeypatch.setattr(get_settings(), "reddit_client_secret", "", raising=False)
    assert not reddit.is_configured()
    # No creds -> no live data -> empty. Never fabricated.
    out = asyncio.run(scrapers.reddit_search("prebiotic soda", limit=5))
    assert out == []


def test_reddit_default_scraper_present():
    from app.monitor.scrapers import DEFAULT_SCRAPERS, reddit_search

    assert reddit_search in DEFAULT_SCRAPERS

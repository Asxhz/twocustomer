"""web_search parse + fix_github tool guards (offline)."""

import asyncio

from app.tools import web_search_tool
from app.tools.github_tool import fix_github
from app.tools.registry import registry

_HTML = """
<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdrinkolipop.com%2F">OLIPOP Soda</a>
<a class="result__snippet">A prebiotic soda with fiber.</a>
<a class="result__a" href="https://duckduckgo.com/y.js?ad_provider=bingv7aa">AD: buy here</a>
<a class="result__snippet">sponsored</a>
<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Folipop">Olipop review</a>
<a class="result__snippet">an honest review</a>
"""


def test_parse_skips_ads_and_decodes():
    out = web_search_tool.parse_results(_HTML, 5)
    assert len(out) == 2  # ad skipped
    assert out[0]["url"] == "https://drinkolipop.com/"
    assert out[0]["title"] == "OLIPOP Soda"
    assert out[1]["url"] == "https://example.com/olipop"


def test_both_tools_registered():
    names = registry.names()
    assert "web_search" in names
    assert "fix_github" in names


def test_fix_github_needs_repo():
    out = asyncio.run(fix_github("the checkout is broken"))
    assert "No GitHub repo" in out

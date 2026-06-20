"""Scenarios for the fake brand "Lumen Flutes". The fake site serves one of
these at a time; switching scenarios = the site "changing its output"."""

from __future__ import annotations

from typing import Any

MSRP_CENTS = 4900  # $49.00 — the correct price


def default_product() -> dict[str, Any]:
    return {"name": "Lumen Concert Flute", "msrp_cents": MSRP_CENTS,
            "price_cents": MSRP_CENTS, "in_stock": True}


def _m(i, author, text, likes):
    return {"id": i, "author": author, "text": text, "likes": likes}


SCENARIOS: dict[str, dict[str, Any]] = {
    # 1) happy path — customers love the flute
    "happy_flute": {
        "mentions": [
            _m("h1", "@firstchair", "The Lumen flute sings — best tone I've owned.", 320),
            _m("h2", "u/fluteplayer", "Switched to Lumen, intonation is dead on.", 140),
            _m("h3", "@bandmom", "My daughter's Lumen flute survived a drop, still perfect.", 60),
        ],
        "product": default_product(),
    },
    # 2) stockout spike — selling out, customers can't buy
    "stockout": {
        "mentions": [
            _m("s1", "@needaflute", "Lumen flute SOLD OUT everywhere again, 3rd week.", 410),
            _m("s2", "u/cpg", "Can't find the Lumen concert flute in stock anywhere.", 220),
            _m("s3", "@teacher", "Whole studio wants Lumen flutes, all sold out.", 95),
        ],
        "product": {**default_product(), "in_stock": False},
    },
    # 3) PRICE BUG — site shows 100x price; customers notice
    "price_bug": {
        "mentions": [
            _m("p1", "@confused", "Why is the Lumen flute listed at $4900?? typo?", 280),
            _m("p2", "u/deals", "Lumen site pricing is broken, flute shows $4,900.", 150),
        ],
        "product": {**default_product(), "price_cents": MSRP_CENTS * 100},  # bug
    },
    # 4) negative quality spike
    "negative": {
        "mentions": [
            _m("n1", "@upset", "My Lumen flute keys stick after a month. disappointed.", 260),
            _m("n2", "u/repair", "Second Lumen flute with a cracked head joint. QC issue?", 190),
        ],
        "product": default_product(),
    },
    # 5) empty — nothing happening
    "empty": {"mentions": [], "product": default_product()},
    # 6) duplicates — same post repeated (dedup must catch)
    "dupes": {
        "mentions": [
            _m("d1", "@same", "Lumen flute sold out again", 200),
            _m("d1", "@same", "Lumen flute sold out again", 200),
            _m("d1", "@same", "Lumen flute sold out again", 200),
        ],
        "product": {**default_product(), "in_stock": False},
    },
    # 7) error — feed is down (site 500s)
    "error": {"mentions": [], "product": default_product(), "error": True},
}

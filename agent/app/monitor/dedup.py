"""Dedup mentions against a seen-id store so the brand is never alerted twice.

Pure helper over a set; the Convex `by_brand_external` index enforces the same
invariant in persistent state.
"""

from __future__ import annotations

from collections.abc import Iterable

from .mention import Mention


def seen_key(m: Mention) -> str:
    return f"{m.platform}:{m.external_id}"


def dedup(mentions: Iterable[Mention], seen: set[str]) -> list[Mention]:
    """Return only mentions whose key isn't already in `seen`; updates `seen`."""
    fresh: list[Mention] = []
    for m in mentions:
        key = seen_key(m)
        if key in seen:
            continue
        seen.add(key)
        fresh.append(m)
    return fresh

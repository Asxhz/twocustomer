"""Common mention model + normalizer shared across every scraper."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Mention:
    platform: str  # x | reddit | linkedin | web
    external_id: str  # stable dedup key (platform-scoped)
    text: str
    author: str = ""
    url: str = ""
    ts: int = 0  # epoch ms
    engagement: float = 0.0  # likes/upvotes/etc — drives scoring
    score: float = 0.0
    high_signal: bool = False

    def as_convex(self, brand_id: str) -> dict[str, Any]:
        return {
            "brandId": brand_id,
            "platform": self.platform,
            "externalId": self.external_id,
            "author": self.author or None,
            "text": self.text,
            "url": self.url or None,
            "score": self.score,
            "highSignal": self.high_signal,
            "ts": self.ts,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize(
    platform: str,
    *,
    text: str,
    external_id: str | None = None,
    author: str = "",
    url: str = "",
    ts: int = 0,
    engagement: float = 0.0,
) -> Mention:
    """Build a Mention with a stable external_id (hash of url+text if absent)."""
    text = (text or "").strip()
    if not external_id:
        h = hashlib.sha1(f"{platform}|{url}|{text}".encode()).hexdigest()[:16]
        external_id = h
    return Mention(
        platform=platform,
        external_id=external_id,
        text=text,
        author=author or "",
        url=url or "",
        ts=int(ts or 0),
        engagement=float(engagement or 0.0),
    )

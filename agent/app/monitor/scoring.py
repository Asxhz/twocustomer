"""Adaptive per-platform signal scoring (ported from TwoCustomer's social_pulse idea).

Each platform keeps a rolling engagement baseline. A mention's score is its
engagement relative to that baseline, squashed to 0..1. High-signal when the
score clears a threshold. Pure + deterministic → unit-testable offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .mention import Mention


@dataclass
class Baseline:
    """Exponential moving average of engagement per platform."""

    alpha: float = 0.3
    values: dict[str, float] = field(default_factory=dict)

    def update(self, platform: str, engagement: float) -> None:
        prev = self.values.get(platform)
        self.values[platform] = (
            engagement if prev is None
            else self.alpha * engagement + (1 - self.alpha) * prev
        )

    def get(self, platform: str) -> float:
        return self.values.get(platform, 0.0)


# Content salience: words that make a mention actionable regardless of
# engagement. Risk terms (a recall article is high-signal even with 0 upvotes)
# outweigh opportunity/buzz terms.
_RISK = ("recall", "recalled", "refund", "lawsuit", "sued", "outage", "broke",
         "broken", "sold out", "stockout", "complaint", "boycott", "cancel",
         "defect", "contamin")
_OPP = ("launch", "viral", "best seller", "bestseller", "expansion",
        "partnership", "award", "raises", "funding", "breakout", "trending")


def content_signal(text: str) -> float:
    """0..1 importance from the text itself. Risk language scores highest."""
    t = text.lower()
    if any(w in t for w in _RISK):
        return 0.85
    if any(w in t for w in _OPP):
        return 0.72
    return 0.0


def score_mention(m: Mention, baseline: Baseline, *, threshold: float = 0.7) -> Mention:
    """Score a mention; mark high-signal. Blends engagement-vs-baseline with
    content salience so newswire/no-engagement sources still surface real
    risk/opportunity. Mutates + returns."""
    base = max(baseline.get(m.platform), 1.0)
    ratio = m.engagement / base
    # squash: 0 engagement -> 0, == baseline -> 0.5, >> baseline -> ~1
    engagement_score = ratio / (1.0 + ratio)
    m.score = round(max(engagement_score, content_signal(m.text)), 4)
    m.high_signal = m.score >= threshold
    baseline.update(m.platform, m.engagement)
    return m


def score_batch(mentions: list[Mention], baseline: Baseline,
                *, threshold: float = 0.7) -> list[Mention]:
    return [score_mention(m, baseline, threshold=threshold) for m in mentions]

"""Monitor run orchestrator: scrape → dedup → score → persist → alert.

Scrapers are injected (a callable taking a query → list[Mention]) so the run is
testable offline and pluggable (Reddit JSON now; Browserbase X/LinkedIn when
keyed). High-signal mentions fire an alert callback (Slack-bound in main).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .dedup import dedup
from .mention import Mention
from .scoring import Baseline, score_batch

Scraper = Callable[[str], Awaitable[list[Mention]]]
AlertFn = Callable[[Mention], Awaitable[None]]


@dataclass
class MonitorState:
    seen: set[str] = field(default_factory=set)
    baseline: Baseline = field(default_factory=Baseline)


@dataclass
class MonitorResult:
    fresh: list[Mention]
    high_signal: list[Mention]


async def run_monitor(
    *,
    terms: list[str],
    scrapers: list[Scraper],
    state: MonitorState,
    threshold: float = 0.7,
    on_alert: AlertFn | None = None,
) -> MonitorResult:
    raw: list[Mention] = []
    for term in terms:
        for scrape in scrapers:
            raw.extend(await scrape(term))

    fresh = dedup(raw, state.seen)
    scored = score_batch(fresh, state.baseline, threshold=threshold)
    high = [m for m in scored if m.high_signal]

    if on_alert:
        for m in high:
            await on_alert(m)

    return MonitorResult(fresh=scored, high_signal=high)

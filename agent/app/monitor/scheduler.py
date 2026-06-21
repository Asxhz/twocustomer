"""Background monitor scheduler.

An APScheduler interval job periodically runs every enabled monitor config:
scrape → dedup → score → synth insight → alert. Per-brand MonitorState is kept
in-process; persistent dedup lives in Convex.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .insight import synth_insight
from .mention import Mention
from .runner import MonitorState, run_monitor
from .scrapers import DEFAULT_SCRAPERS

logger = logging.getLogger("twocustomer.scheduler")

# slug -> MonitorState
_STATES: dict[str, MonitorState] = {}
# slug -> MonitorConfig dict (registered configs the tick iterates)
REGISTERED: dict[str, dict] = {}


async def persist_mentions(slug: str, mentions: list[Mention]) -> int:
    """Write scored mentions to Convex (idempotent on (brand, externalId)).
    No-op when Convex is unconfigured. Returns # newly inserted."""
    from app.state.convex_client import get_convex

    cx = get_convex()
    if not cx.enabled or not mentions:
        return 0
    inserted = 0
    for m in mentions:
        try:
            if await cx.mutation("mentions:insertMention", **m.as_convex(slug)):
                inserted += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("persist mention failed for %s: %s", slug, exc)
    return inserted


async def tick() -> int:
    """Run one pass over all enabled configs. Returns # of insights produced."""
    produced = 0
    for slug, cfg in list(REGISTERED.items()):
        if not cfg.get("enabled", True):
            continue
        from app.state.limits import acquire_lock, release_lock

        if not await acquire_lock(f"monitor:{slug}", ttl_s=cfg.get("interval_minutes", 30) * 60):
            continue  # a run for this brand is already in flight
        state = _STATES.setdefault(slug, MonitorState())
        try:
            async def _alert(m):
                from app.channels.alerts import dispatch

                await dispatch(f"[{m.platform}] {m.text[:200]}",
                               title=f"High-signal mention · {slug}", severity="risk",
                               brand_slug=slug)

            res = await run_monitor(
                terms=cfg.get("terms", [slug]), scrapers=DEFAULT_SCRAPERS,
                state=state, threshold=cfg.get("threshold", 0.7),
                on_alert=_alert,
            )
            await persist_mentions(slug, res.fresh)  # durable feed + dedup
            if res.high_signal:
                if await synth_insight(slug, res.high_signal):
                    produced += 1
                    from app.channels.alerts import notify
                    await notify("insight", f"New insight · {slug}",
                                 body="The analyst formed a new insight from fresh signal.",
                                 brand_slug=slug, href="/admin/insights")
        except Exception as exc:  # noqa: BLE001
            logger.warning("monitor tick failed for %s: %s", slug, exc)
        finally:
            await release_lock(f"monitor:{slug}")
    return produced


def build_scheduler(*, minutes: int = 30) -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    sched.add_job(tick, IntervalTrigger(minutes=minutes), id="monitor_tick",
                  replace_existing=True)
    return sched

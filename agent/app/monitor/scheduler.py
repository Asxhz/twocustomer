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


async def _github_token_for_brand(slug: str) -> str:
    """Resolve a brand's company GitHub token (decrypted) for autonomous fixes.
    Returns '' when unavailable — the FDE then returns a diff without opening a PR."""
    from app.state.convex_client import get_convex
    from app.state.crypto import decrypt_secret

    cx = get_convex()
    if not cx.enabled:
        return ""
    try:
        brand = await cx.query("brands:getBySlug", slug=slug)
        owner = (brand or {}).get("ownerEmail")
        if not owner:
            return ""
        company = await cx.query("companies:getByOwner", ownerEmail=owner)
        return decrypt_secret((company or {}).get("githubTokenEnc", "") or "") or ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("token lookup failed for %s: %s", slug, exc)
        return ""


async def _auto_fix(slug: str, cfg: dict, insight: dict) -> None:
    """Autonomous CMO→FDE: a connected repo + a risk insight → open a fix (PR +
    preview) and notify the founder. No-ops safely without a connected repo, and a
    per-brand cooldown lock keeps it from shipping on every tick."""
    repo_url = cfg.get("repo_url")
    if not repo_url:
        return
    from app.state.limits import acquire_lock

    # Acquire-and-hold (never released): the lock expires after the cooldown so we
    # ship at most one auto-fix per brand per window, not one per monitor tick.
    if not await acquire_lock(f"autofix:{slug}", ttl_s=6 * 3600):
        return
    token = await _github_token_for_brand(slug)
    from app.channels.alerts import notify
    from app.fde.repo_sandbox import fix_connected_repo

    symptom = f"{insight['title']} — {insight['body']}"
    try:
        res = await fix_connected_repo(repo_url, symptom, token=token)
    except Exception as exc:  # noqa: BLE001
        logger.warning("auto-fix failed for %s: %s", slug, exc)
        return
    if res.get("error"):
        logger.info("auto-fix skipped for %s: %s", slug, res["error"])
        return
    href = res.get("pr_url") or res.get("preview_url") or "/admin"
    await notify("fix", f"Auto-fix shipped · {slug}",
                 body=f"{insight['title']} → {res.get('file', 'patched')}",
                 brand_slug=slug, href=href)


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
                insight = await synth_insight(slug, res.high_signal)
                if insight:
                    produced += 1
                    from app.channels.alerts import notify
                    await notify("insight", f"New insight · {slug}",
                                 body="The analyst formed a new insight from fresh signal.",
                                 brand_slug=slug, href="/admin/insights")
                    # Autonomous CMO→FDE: ship a fix for connected-repo risks.
                    if cfg.get("auto_fix") and insight.get("severity") == "risk":
                        await _auto_fix(slug, cfg, insight)
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

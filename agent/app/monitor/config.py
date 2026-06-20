"""Monitor configuration model + store.

A brand's monitor config (terms, cadence, signal threshold). Persisted to Redis
when configured, in-memory otherwise — so CRUD works offline and survives
restarts in prod.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.state.redis_client import get_redis


class MonitorConfig(BaseModel):
    brand_slug: str
    terms: list[str] = Field(default_factory=list)
    interval_minutes: int = Field(default=30, ge=1, le=1440)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enabled: bool = True


def _key(slug: str) -> str:
    return f"monitor:config:{slug}"


_MEM: dict[str, dict] = {}


_SLUGS_KEY = "monitor:brands"


async def save_config(cfg: MonitorConfig) -> MonitorConfig:
    _MEM[cfg.brand_slug] = cfg.model_dump()
    r = get_redis()
    if r.enabled:
        await r.set_json(_key(cfg.brand_slug), cfg.model_dump())
        slugs = await r.get_json(_SLUGS_KEY) or []
        if cfg.brand_slug not in slugs:
            slugs.append(cfg.brand_slug)
            await r.set_json(_SLUGS_KEY, slugs)
    return cfg


async def all_configs() -> list[MonitorConfig]:
    """Every saved monitor config — used to repopulate the scheduler on restart."""
    r = get_redis()
    slugs = (await r.get_json(_SLUGS_KEY) or []) if r.enabled else list(_MEM)
    out: list[MonitorConfig] = []
    for slug in slugs:
        cfg = await get_config(slug)
        if cfg:
            out.append(cfg)
    return out


async def get_config(slug: str) -> MonitorConfig | None:
    r = get_redis()
    if r.enabled:
        data = await r.get_json(_key(slug))
        if data:
            return MonitorConfig(**data)
    data = _MEM.get(slug)
    return MonitorConfig(**data) if data else None

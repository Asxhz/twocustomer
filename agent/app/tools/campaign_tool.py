"""create_campaign — draft a marketing campaign brief and persist it.

Turns a product brief into a structured campaign (name, concept, hooks,
channels, creators, metrics) the team can run. Persists to Convex `campaigns`
(no-op offline); stashes LAST_CAMPAIGN for the UI.
"""

from __future__ import annotations

import time
from typing import Any

from app.state.convex_client import get_convex

from .registry import registry

LAST_CAMPAIGN: dict[str, dict[str, Any]] = {}


def _draft(brand: str, brief: str) -> dict[str, Any]:
    name = (brief.strip().split(".")[0][:48] or "New campaign").title()
    body = (
        f"# {name}\n\n"
        f"**Brief:** {brief.strip()}\n\n"
        "## Concept\nLean into the breakout angle from current signal.\n\n"
        "## Hooks\n- Social-proof the sellout moment\n- Spotlight the top SKU\n\n"
        "## Channels\nUGC creators on TikTok + paid social retargeting.\n\n"
        "## Success metrics\nCAC, ROAS, repeat-purchase rate."
    )
    return {"brand": brand, "name": name, "brief": brief.strip(),
            "body": body, "status": "ready", "createdAt": int(time.time() * 1000)}


@registry.tool(
    name="create_campaign",
    description=(
        "Draft a marketing campaign for the brand from a product brief: concept, "
        "hooks, channel strategy, and success metrics. Use when asked to build / "
        "plan / launch a campaign."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "brand": {"type": "string"},
            "brief": {"type": "string", "description": "What to promote."},
        },
        "required": ["brand", "brief"],
    },
)
async def create_campaign(brand: str, brief: str) -> str:
    c = _draft(brand, brief)
    LAST_CAMPAIGN[brand] = c
    cx = get_convex()
    if cx.enabled:
        try:
            await cx.mutation("campaigns:add", brandId=brand, brief=c["brief"],
                              body=c["body"], status=c["status"])
        except Exception:  # noqa: BLE001
            pass
    return f"Campaign ready: {c['name']}\n\n{c['body']}"

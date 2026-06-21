"""Channel-agnostic alert fan-out. High-signal mentions go to Discord and the
in-dashboard notification bell. No-ops cleanly when nothing is configured."""

from __future__ import annotations

from . import discord


async def notify(kind: str, title: str, *, body: str = "", brand_slug: str = "",
                 href: str = "") -> None:
    """Write an in-dashboard notification (Convex). No-op when Convex is off."""
    try:
        from app.state.convex_client import get_convex

        cx = get_convex()
        if not cx.enabled:
            return
        args: dict[str, str] = {"kind": kind, "title": title, "body": body, "href": href}
        if brand_slug:
            args["brandId"] = brand_slug
        await cx.mutation("notifications:add", **args)
    except Exception:  # noqa: BLE001 - notifications must never break the caller
        pass


async def dispatch(text: str, *, title: str = "High-signal mention",
                   severity: str = "info", brand_slug: str = "") -> list[str]:
    sent: list[str] = []
    try:
        if await discord.alert(text, title=title, severity=severity):
            sent.append("discord")
    except Exception:  # noqa: BLE001
        pass
    # Always surface in the dashboard bell, even when no chat channel is wired.
    await notify("alert", title, body=text[:200], brand_slug=brand_slug, href="/monitor")
    return sent

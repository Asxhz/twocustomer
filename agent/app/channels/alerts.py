"""Channel-agnostic alert fan-out. High-signal mentions go to every configured
channel (Slack and/or Discord). No-ops cleanly when none are configured."""

from __future__ import annotations

from . import discord, slack


async def dispatch(text: str, *, title: str = "High-signal mention",
                   severity: str = "info") -> list[str]:
    sent: list[str] = []
    try:
        if await slack.alert(text, title=title, severity=severity):
            sent.append("slack")
    except Exception:  # noqa: BLE001
        pass
    try:
        if await discord.alert(text, title=title, severity=severity):
            sent.append("discord")
    except Exception:  # noqa: BLE001
        pass
    return sent

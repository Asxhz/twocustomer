"""request_call — escalate a text chat to a live video call.

When the user wants to change something visual ("the hero looks off", "fix the
layout", "make the page cleaner") the agent should call this so the UI can offer
a Join-call button. On the call the user shares their screen / shows the issue,
then the agent builds a sandbox preview of the fix. Returns a marker the chat
handler turns into a `call_invite` artifact.
"""

from __future__ import annotations

from .registry import registry


@registry.tool(
    name="request_call",
    description=(
        "Offer the user a live video call when visual context would help — e.g. "
        "site/layout/design changes, or anything easier to show than describe. "
        "Pass a short reason. The user joins, shares their screen, and you then "
        "build a sandbox preview of the change."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why a call helps, phrased to the user.",
            }
        },
        "required": ["reason"],
    },
)
async def request_call(reason: str) -> str:
    return f"CALL_INVITE: {reason}"

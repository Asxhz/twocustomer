"""start_video_session — spin up a Daily video room (with screen share) for a
live customer interview / working session, and return the join link."""

from __future__ import annotations

from app.channels.daily import create_room

from .registry import registry

LAST_ROOM: dict[str, dict] = {}


@registry.tool(
    name="start_video_session",
    description=(
        "Start a live video + screen-share session with a customer (they can "
        "show their screen / broken site while you interview them). Returns a "
        "join link to send them."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "customer": {"type": "string", "description": "Who you're meeting."},
        },
        "required": [],
    },
)
async def start_video_session(customer: str = "customer") -> str:
    room = await create_room()
    if not room:
        return "Video unavailable: DAILY_API_KEY not set."
    LAST_ROOM["last"] = room
    return (f"Live video room ready (screen share enabled): {room['url']}\n"
            f"Send this link to {customer}; both join, they share their screen.")

"""Intent parsing for the TwoCustomer uAgent.

Pure, dependency-free, and unit-testable without the uagents runtime. Maps a
natural-language ASI:One message to a TwoCustomer action + args, which the agent
then forwards to the control plane.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Intent:
    action: str  # monitor | campaign | interview | insights | status | help
    arg: str = ""


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("fix", re.compile(r"\b(fix|broken|bug|repair|garbled|not working)\b", re.I)),
    ("edit", re.compile(r"\b(edit|generate|make).{0,20}\b(image|photo|picture|render|product)\b|less hefty|cleaner photo", re.I)),
    ("video", re.compile(r"\b(video call|screen ?share|live session|hop on a call|jump on)\b", re.I)),
    ("monitor", re.compile(r"\b(monitor|track|watch|keep tabs on|listen for)\b", re.I)),
    ("campaign", re.compile(r"\b(campaign|go.?to.?market|launch plan|promote)\b", re.I)),
    ("interview", re.compile(r"\b(interview|talk to|survey|ask)\b.*\b(customer|user|buyer)s?\b", re.I)),
    ("insights", re.compile(r"\b(insight|what did you find|findings|anomal|opportunit|leak)\b", re.I)),
    ("status", re.compile(r"\b(status|how's it going|what are you doing|whats running)\b", re.I)),
]


def _strip_keyword(text: str, action: str) -> str:
    """Best-effort extraction of the argument (brand / brief / customer)."""
    t = text.strip()
    # drop a leading verb + filler so "monitor Aurora Drinks" -> "Aurora Drinks"
    t = re.sub(r"^(please\s+)?(monitor|track|watch|build( me)?|make( me)?|create|"
               r"plan|run|start|interview|survey)\s+(a\s+)?(campaign\s+(for\s+)?)?",
               "", t, flags=re.I).strip()
    t = re.sub(r"^(for|on|about)\s+", "", t, flags=re.I).strip()
    return t


def parse_intent(text: str) -> Intent:
    text = (text or "").strip()
    if not text:
        return Intent(action="help")
    for action, pat in _PATTERNS:
        if pat.search(text):
            return Intent(action=action, arg=_strip_keyword(text, action))
    # default: treat as an analyst question → insights/chat
    return Intent(action="insights", arg=text)

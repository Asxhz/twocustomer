"""Robust JSON extraction from model output.

Claude sometimes wraps JSON in prose or ```json fences, or emits a trailing
comma. The old `re.search(r"\\{.*\\}")` + bare `json.loads` crashed with
"Expecting property name enclosed in double quotes" on any of these. This module
strips fences, finds the first balanced object, and parses defensively, and
offers a one-retry helper that nudges the model to return JSON only.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _strip_fences(text: str) -> str:
    t = text.strip()
    # ```json ... ```  or  ``` ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else t


def _first_balanced_object(text: str) -> str | None:
    """Return the first balanced {...} span, respecting strings/escapes."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from arbitrary model text."""
    if not text:
        return None
    candidate = _first_balanced_object(_strip_fences(text))
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # tolerate trailing commas
        cleaned = re.sub(r",(\s*[}\]])", r"\1", candidate)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


async def diagnose_json(llm: Any, *, system: str, messages: list[dict[str, Any]],
                        retries: int = 1) -> dict[str, Any]:
    """Call the model and parse a JSON object, retrying once with a JSON-only nudge.

    Raises RuntimeError with a clear message if the model never returns parseable
    JSON (caller turns this into a friendly error, never a crash).
    """
    msgs = list(messages)
    for attempt in range(retries + 1):
        resp = await llm.complete(system=system, messages=msgs)
        data = extract_json(resp.text)
        if data is not None:
            return data
        if attempt < retries:
            msgs = msgs + [
                {"role": "assistant", "content": resp.text[:500]},
                {"role": "user", "content": "Return ONLY a valid JSON object, no prose, no code fences."},
            ]
    raise RuntimeError("model did not return parseable JSON")

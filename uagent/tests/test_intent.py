"""P5.12/P5.13 — intent parsing (pure, no uagents runtime needed)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intent import parse_intent  # noqa: E402


def test_monitor():
    i = parse_intent("monitor Aurora Drinks")
    assert i.action == "monitor"
    assert "Aurora Drinks" in i.arg


def test_campaign():
    i = parse_intent("build me a campaign for the yuzu SKU")
    assert i.action == "campaign"
    assert "yuzu" in i.arg


def test_interview():
    i = parse_intent("interview our customers about packaging")
    assert i.action == "interview"


def test_status():
    assert parse_intent("status").action == "status"


def test_insights_default():
    assert parse_intent("what's leaking revenue?").action == "insights"


def test_empty_is_help():
    assert parse_intent("").action == "help"


def test_fix():
    assert parse_intent("fix the broken site, it renders hi hi my my").action == "fix"


def test_edit():
    assert parse_intent("make the product photo cleaner and less hefty").action == "edit"


def test_video():
    assert parse_intent("can we hop on a video call and screen share").action == "video"

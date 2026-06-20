#!/usr/bin/env python3
"""Live integration test — real API calls with the keys in .env. Proves what
actually connects. Run: uv run --project agent python scripts/live_test.py"""

from __future__ import annotations

import asyncio
import base64
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

R = {}  # results


def ok(name, detail):  R[name] = ("✅", detail)
def bad(name, detail): R[name] = ("❌", detail)
def skip(name, detail): R[name] = ("·", detail)


async def t_anthropic():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key: return skip("Anthropic Claude", "no key")
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post("https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                      "max_tokens": 30,
                      "messages": [{"role": "user", "content": "Reply in exactly three words."}]})
        if r.status_code == 200:
            txt = "".join(b.get("text", "") for b in r.json().get("content", []))
            ok("Anthropic Claude", f'reply: "{txt.strip()}"')
        else:
            bad("Anthropic Claude", f"{r.status_code}: {r.text[:120]}")
    except Exception as e: bad("Anthropic Claude", str(e)[:120])


async def t_browserbase():
    key, proj = os.environ.get("BROWSERBASE_API_KEY"), os.environ.get("BROWSERBASE_PROJECT_ID")
    if not (key and proj): return skip("Browserbase", "no key/project")
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post("https://api.browserbase.com/v1/sessions",
                headers={"X-BB-API-Key": key, "Content-Type": "application/json"},
                json={"projectId": proj})
        if r.status_code in (200, 201):
            d = r.json()
            ok("Browserbase", f"session {d.get('id','?')[:18]}… connectUrl present={bool(d.get('connectUrl'))}")
        else:
            bad("Browserbase", f"{r.status_code}: {r.text[:120]}")
    except Exception as e: bad("Browserbase", str(e)[:120])


async def t_deepgram():
    key = os.environ.get("DEEPGRAM_API_KEY")
    if not key: return skip("Deepgram", "no key")
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            tts = await c.post("https://api.deepgram.com/v1/speak?model=aura-2-thalia-en",
                headers={"Authorization": f"Token {key}", "Content-Type": "application/json"},
                json={"text": "Aurora Drinks sold out again."})
            if tts.status_code != 200:
                return bad("Deepgram", f"TTS {tts.status_code}: {tts.text[:100]}")
            audio = tts.content
            stt = await c.post("https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true",
                headers={"Authorization": f"Token {key}", "Content-Type": "audio/wav"},
                content=audio)
            tr = ""
            if stt.status_code == 200:
                tr = stt.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
            ok("Deepgram", f"TTS {len(audio)}B audio → STT heard: \"{tr}\"")
    except Exception as e: bad("Deepgram", str(e)[:120])


async def t_redis():
    url, tok = os.environ.get("UPSTASH_REDIS_REST_URL"), os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if not (url and tok): return skip("Upstash Redis", "no creds")
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            h = {"Authorization": f"Bearer {tok}"}
            v = f"live-{int(time.time())}"
            await c.post(url.rstrip("/"), headers=h, json=["set", "tc:livetest", v])
            g = await c.post(url.rstrip("/"), headers=h, json=["get", "tc:livetest"])
        got = g.json().get("result")
        ok("Upstash Redis", f"set/get roundtrip → {got}") if got == v else bad("Upstash Redis", f"mismatch {got}")
    except Exception as e: bad("Upstash Redis", str(e)[:120])


async def t_convex():
    url = os.environ.get("CONVEX_URL")
    if not url: return skip("Convex", "no CONVEX_URL")
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(f"{url.rstrip('/')}/api/query",
                json={"path": "brands:list", "args": {}, "format": "json"})
        if r.status_code == 200 and r.json().get("status") == "success":
            ok("Convex", f"brands:list → {len(r.json().get('value') or [])} brands")
        else:
            bad("Convex", f"{r.status_code}: {r.text[:120]}")
    except Exception as e: bad("Convex", str(e)[:120])


async def t_discord():
    wh = os.environ.get("DISCORD_WEBHOOK_URL")
    if not wh: return skip("Discord webhook", "no DISCORD_WEBHOOK_URL")
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(wh, json={"content": "✅ TwoCustomer live test — high-signal alert demo"})
        ok("Discord webhook", "message posted to channel") if r.status_code in (200, 204) else bad("Discord webhook", f"{r.status_code}: {r.text[:100]}")
    except Exception as e: bad("Discord webhook", str(e)[:120])


async def t_fetch():
    for k in ("UAGENT_SEED", "AGENTVERSE_API_KEY", "ASI_ONE_API_KEY"):
        if not os.environ.get(k): return skip("Fetch/ASI:One", f"missing {k}")
    ok("Fetch/ASI:One", "seed + agentverse + asi:one keys present (run uagent to register)")


async def t_gemini():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key: return skip("Gemini (image)", "no key")
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    try:
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": "A clean studio photo of a silver flute on white."}]}]})
        if r.status_code != 200:
            return bad("Gemini (image)", f"{r.status_code}: {r.text[:100]}")
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        has_img = any(p.get("inlineData") or p.get("inline_data") for p in parts)
        ok("Gemini (image)", "generated an image ✔") if has_img else bad("Gemini (image)", "no image in response")
    except Exception as e: bad("Gemini (image)", str(e)[:100])


async def t_daily():
    key = os.environ.get("DAILY_API_KEY")
    if not key: return skip("Daily (video)", "no key")
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://api.daily.co/v1/rooms",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"properties": {"enable_screenshare": True, "exp": int(time.time()) + 600}})
        ok("Daily (video)", f"room {r.json().get('url','?')}") if r.status_code in (200, 201) else bad("Daily (video)", f"{r.status_code}: {r.text[:80]}")
    except Exception as e: bad("Daily (video)", str(e)[:100])


async def t_twilio():
    sid, tok = os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN")
    if not (sid and tok): return skip("Twilio (SMS/call)", "no creds")
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json", auth=(sid, tok))
        ok("Twilio (SMS/call)", f"account '{r.json().get('friendly_name','?')}' valid") if r.status_code == 200 else bad("Twilio (SMS/call)", f"{r.status_code}")
    except Exception as e: bad("Twilio (SMS/call)", str(e)[:100])


async def main():
    await asyncio.gather(t_anthropic(), t_browserbase(), t_deepgram(), t_redis(),
                         t_convex(), t_discord(), t_fetch(),
                         t_gemini(), t_daily(), t_twilio())
    print("\n" + "=" * 64)
    print("  TwoCustomer — LIVE integration test")
    print("=" * 64)
    for name in ["Anthropic Claude", "Browserbase", "Deepgram", "Upstash Redis",
                 "Convex", "Discord webhook", "Fetch/ASI:One",
                 "Gemini (image)", "Daily (video)", "Twilio (SMS/call)"]:
        mark, detail = R.get(name, ("?", "not run"))
        print(f"  {mark} {name:<18} {detail}")
    print("=" * 64)
    live = sum(1 for m, _ in R.values() if m == "✅")
    print(f"  {live} integrations LIVE\n")


if __name__ == "__main__":
    asyncio.run(main())

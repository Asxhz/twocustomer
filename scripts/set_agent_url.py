#!/usr/bin/env python
"""Point the deployed web app at a new agent URL and redeploy.

Updates the Vercel `AGENT_BASE_URL` env on the web project to the given URL
(all targets) and triggers a production redeploy. Used by demo_up.sh after the
Cloudflare tunnel URL changes.

    python scripts/set_agent_url.py https://xyz.trycloudflare.com
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
# Vercel team/scope for the web project. Read from env (VERCEL_SCOPE) so this
# isn't tied to one account; falls back to .env if not exported.
SCOPE = os.environ.get("VERCEL_SCOPE") or dotenv_values(ROOT / ".env").get("VERCEL_SCOPE", "")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: set_agent_url.py <agent-url>", file=sys.stderr)
        return 1
    url = sys.argv[1].rstrip("/")
    env = dotenv_values(ROOT / ".env")
    vtok = env.get("VERCEL_TOKEN")
    if not vtok:
        print("VERCEL_TOKEN missing in .env", file=sys.stderr)
        return 1
    proj = json.loads((ROOT / "web" / ".vercel" / "project.json").read_text())
    pid = proj["projectId"]
    h = {"Authorization": f"Bearer {vtok}"}

    # remove existing AGENT_BASE_URL, then set the new value for all targets
    cur = httpx.get(f"https://api.vercel.com/v9/projects/{pid}/env?teamId={SCOPE}",
                    headers=h, timeout=20).json().get("envs", [])
    for e in cur:
        if e["key"] == "AGENT_BASE_URL":
            httpx.delete(
                f"https://api.vercel.com/v9/projects/{pid}/env/{e['id']}?teamId={SCOPE}",
                headers=h, timeout=20)
    for tgt in ("production", "preview", "development"):
        httpx.post(f"https://api.vercel.com/v10/projects/{pid}/env?teamId={SCOPE}",
                   headers=h, json={"key": "AGENT_BASE_URL", "value": url,
                                    "type": "encrypted", "target": [tgt]}, timeout=20)
    print(f"  AGENT_BASE_URL -> {url}")

    # Re-point the Twilio number's webhooks at the new tunnel URL (else inbound
    # SMS/voice breaks when the tunnel changes).
    sid = (env.get("TWILIO_ACCOUNT_SID") or "").strip()
    atok = (env.get("TWILIO_AUTH_TOKEN") or "").strip()
    if sid and atok:
        try:
            nums = httpx.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json",
                auth=(sid, atok), timeout=20).json().get("incoming_phone_numbers", [])
            for n in nums:
                httpx.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers/{n['sid']}.json",
                    auth=(sid, atok),
                    data={"SmsUrl": f"{url}/twilio/sms", "SmsMethod": "POST",
                          "VoiceUrl": f"{url}/twilio/voice", "VoiceMethod": "POST"},
                    timeout=20)
            if nums:
                print(f"  Twilio webhooks -> {url}/twilio/*")
        except Exception as exc:  # noqa: BLE001
            print(f"  (twilio webhook update skipped: {exc})")

    subprocess.run(
        ["npx", "--yes", "vercel@latest", "deploy", "--prod", "--yes",
         "--token", vtok, "--scope", SCOPE],
        cwd=str(ROOT / "web"), check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

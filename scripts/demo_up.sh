#!/usr/bin/env bash
# Bring the live demo up: run the agent locally (all features work — chat, FDE
# clone/build, image, video, webhooks) and expose it on a public HTTPS URL via a
# Cloudflare quick tunnel. Then point the deployed web app at that URL.
#
#   ./scripts/demo_up.sh
#
# Keep this running during the demo. The tunnel URL changes each run, so this
# script updates the Vercel web env + redeploys automatically.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/agent/.venv/bin/python"

echo "→ starting agent on :8000"
pkill -f "uvicorn app.main" 2>/dev/null
( cd "$ROOT/agent" && "$PY" -m uvicorn app.main:app --port 8000 --log-level warning >/tmp/tc-agent.log 2>&1 & )
for i in $(seq 1 30); do curl -s -m2 localhost:8000/health 2>/dev/null | grep -q ok && break; sleep 1; done
curl -s localhost:8000/health >/dev/null && echo "  agent up" || { echo "  agent failed — see /tmp/tc-agent.log"; exit 1; }

echo "→ opening Cloudflare tunnel"
pkill -f "cloudflared tunnel" 2>/dev/null
( cloudflared tunnel --url http://localhost:8000 >/tmp/tc-tunnel.log 2>&1 & )
URL=""
for i in $(seq 1 30); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/tc-tunnel.log | head -1)"
  [ -n "$URL" ] && break; sleep 1
done
[ -z "$URL" ] && { echo "  tunnel failed — see /tmp/tc-tunnel.log"; exit 1; }
echo "  tunnel: $URL"

echo "→ pointing the deployed web app at the tunnel + redeploying"
"$PY" "$ROOT/scripts/set_agent_url.py" "$URL" || { echo "  could not update Vercel env"; exit 1; }

echo
echo "✅ demo is live. Keep this terminal open."
echo "   agent : $URL/health"
echo "   web   : https://twocustomer-ashs-projects-548e0de1.vercel.app"
echo "   (Ctrl-C stops the agent + tunnel)"
wait

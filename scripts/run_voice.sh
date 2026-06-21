#!/usr/bin/env bash
# Run the local real-time processes that can't live on Vercel:
#   - voice control + Pipecat voice agent (port 8100) — joins Daily calls
#   - Discord gateway bot
# The agent (:8000) and web (:3000) run separately (scripts/dev.sh or deployed).
# Point VOICE_CONTROL_URL at this host so the agent can send the bot into calls.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=agent/.venv/bin/python

echo "Starting voice control on :8100 ..."
( cd agent && "../$PY" -m uvicorn voice_control:app --port 8100 --host 0.0.0.0 ) &
VOICE_PID=$!

echo "Starting Discord bot ..."
( cd agent && "../$PY" bot.py ) &
BOT_PID=$!

trap 'kill $VOICE_PID $BOT_PID 2>/dev/null || true' INT TERM
echo "Voice control pid=$VOICE_PID, bot pid=$BOT_PID. Ctrl-C to stop both."
wait

#!/usr/bin/env bash
# Boot the agent, hit /chat over SSE, assert the tool + token + message path.
# Works on the stub LLM (no Anthropic credits needed). Exit 0 on pass.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8077}"

# Force the deterministic stub LLM so the smoke passes without Anthropic credits.
export FORCE_STUB=1
( cd "$ROOT/agent" && FORCE_STUB=1 uv run uvicorn app.main:app --port "$PORT" --log-level warning ) &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT

# wait for /health
for i in $(seq 1 30); do
  curl -sf "localhost:$PORT/health" >/dev/null 2>&1 && break
  sleep 0.5
done

echo "== /health =="
curl -s "localhost:$PORT/health" | grep -Eq '"status": ?"ok"' || { echo "health FAIL"; exit 1; }

echo "== /chat (tool + stream) =="
OUT=$(curl -s -N -X POST "localhost:$PORT/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"please use echo on ping","participant":"smoke"}')

echo "$OUT" | grep -q 'event: tool_end'  || { echo "no tool_end"; exit 1; }
echo "$OUT" | grep -q 'event: token'     || { echo "no token stream"; exit 1; }
echo "$OUT" | grep -q 'event: message'   || { echo "no message"; exit 1; }
echo "$OUT" | grep -q 'echo'             || { echo "echo tool did not run"; exit 1; }

echo "SMOKE /chat PASS ✅"

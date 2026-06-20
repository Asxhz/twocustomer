#!/usr/bin/env bash
# Boot the full local stack: convex dev, agent (uvicorn), web (next dev).
# Ctrl-C stops all three.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pids=()
cleanup() { for p in "${pids[@]}"; do kill "$p" 2>/dev/null; done; }
trap cleanup EXIT INT TERM

if [ -d "$ROOT/convex" ] && [ -f "$ROOT/convex/package.json" ]; then
  # Push functions once and exit. `convex dev` (watch) loops forever here
  # because functions="." makes it watch its own .convex/ cache. The web reads
  # the deployed backend via CONVEX_URL, so a one-shot push is all we need.
  # Re-run `cd convex && npx convex dev --once` after editing convex/*.ts.
  echo "→ convex push (once)"
  ( cd "$ROOT/convex" && npx convex dev --once ) & pids+=($!)
fi

echo "→ agent :8000"
# Use the venv's python -m uvicorn (not `uv run uvicorn`, which can pick up a
# system uvicorn missing project deps like convex/playwright).
( cd "$ROOT/agent" && .venv/bin/python -m uvicorn app.main:app --reload --port 8000 ) & pids+=($!)

if [ -f "$ROOT/web/package.json" ]; then
  echo "→ web :3000"
  ( cd "$ROOT/web" && pnpm dev ) & pids+=($!)
fi

wait

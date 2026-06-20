#!/usr/bin/env bash
# Run every TwoCustomer test suite. Exit non-zero if any fails.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0

echo "== agent (pytest) =="
( cd "$ROOT/agent" && .venv/bin/python -m pytest -q ) || fail=1

echo "== uagent (intent) =="
( cd "$ROOT/uagent" && python3 -m pytest tests -q ) || fail=1

if [ -f "$ROOT/web/package.json" ]; then
  echo "== web (vitest) =="
  ( cd "$ROOT/web" && pnpm test ) || fail=1
fi

echo "== e2e smoke =="
( cd "$ROOT" && uv run --project agent python scripts/e2e_smoke.py ) || fail=1

if [ $fail -eq 0 ]; then echo "ALL SUITES PASS ✅"; else echo "SOME SUITES FAILED ❌"; fi
exit $fail

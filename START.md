# START

TwoCustomer = AI agent team for a brand. 3 servers: Convex (db) · Agent (:8000) · Web (:3000).

## 1. Keys (one time)

```bash
cp .env.example .env          # fill what you have (Anthropic min)
cp web/.env.example web/.env.local
```

Put the **same** `AGENT_SHARED_TOKEN` + `CONVEX_URL` in both files.
Empty keys = that feature politely turns off. Nothing crashes.

| Key | Turns on |
|-----|----------|
| `ANTHROPIC_API_KEY` | brain (chat, fix, insights) — **required** |
| `BROWSERBASE_API_KEY` + `_PROJECT_ID` | live news scraping |
| `CONVEX_URL` | dashboard shows live data (else mock) |
| `GEMINI_API_KEY` | image edit (Studio) |
| `DAILY_API_KEY` | video call |
| `TWILIO_*` | SMS / phone interview |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | login wall (else open) |

## 2. Run

```bash
./scripts/dev.sh        # boots all 3, Ctrl-C stops all
```

## 3. Open

- Web: http://localhost:3000
- Dashboard (live mentions): http://localhost:3000/monitor
- Onboarding: http://localhost:3000/admin/onboarding
- Agent health: http://localhost:8000/health

## Demo path (90 sec)

1. `/admin/onboarding` → type brand → **Arm monitors** (persists, real).
2. `/monitor` → live news mentions, risk-scored.
3. `/admin/fix` → fix a broken site: `hi hi my my` → `hi my name is` (real Claude patch + validate).
4. `/admin` chat → ask "latest risk signal?" → agent runs tools, answers.

## Test

```bash
cd agent && .venv/bin/python -m pytest -q     # 106 pass
cd web && pnpm build                          # green
```

## If something's off

- Agent down? `cd agent && .venv/bin/python -m uvicorn app.main:app --port 8000`
- Dashboard shows mock? `CONVEX_URL` missing from `web/.env.local`.
- 401 from agent? `AGENT_SHARED_TOKEN` must match in `.env` and `web/.env.local`.

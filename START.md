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

Login is email-only (cookie) — no key, just enter an email.

## 2. Run

**Local dev** (everything on localhost):
```bash
./scripts/dev.sh        # convex + agent + web, Ctrl-C stops all
```

**Live demo** (deployed web → your local agent via a public tunnel):
```bash
./scripts/demo_up.sh    # agent + Cloudflare tunnel + rewires the deployed site
```
Keep that terminal open. It prints the live web URL. The deployed serverless
agent can't run long chats / FDE clones, so the demo runs the real agent locally
and tunnels to it.

## 3. Open

- Live web: https://twocustomer-ashs-projects-548e0de1.vercel.app
- Local web: http://localhost:3000
- Status board (all integrations): `/status`
- Agent health: http://localhost:8000/health

## Demo path (2 min)

1. **Sign in** (any email) → dashboard.
2. **Onboarding** → brand + terms + **GitHub repo** → Arm. (repo prefills the Fix page.)
3. **/monitor** → live news + Reddit mentions, risk-scored, auto-refreshing.
4. **/admin chat** → "build a campaign for <brand>" → watch tools run live → campaign.
5. **/admin/fix → GitHub repo** → paste a repo → clone → diagnose → **PR / diff**.
6. **/admin/studio** → prompt → real Gemini image.
7. **/status** → every integration green.

## Test

```bash
cd agent && .venv/bin/python -m pytest -q     # 106 pass
cd web && pnpm build                          # green
```

## If something's off

- Agent down? `cd agent && .venv/bin/python -m uvicorn app.main:app --port 8000`
- Dashboard shows mock? `CONVEX_URL` missing from `web/.env.local`.
- 401 from agent? `AGENT_SHARED_TOKEN` must match in `.env` and `web/.env.local`.

# Deploy — always-on

Architecture (chosen): **agent + uAgent on Render** (long-lived; chat/FDE/monitor
need a real process), **web on Vercel**, **Convex** in the cloud. No tunnel.

```
Browser ──> Vercel (web, Next.js) ──server-side──> Render (agent, FastAPI :health)
                     │                                   │
                     └──> Convex (data)  <───────────────┘
                                         Render (uAgent) ──> Agentverse / ASI:One
```

## 1. Convex (data) — already live
Deployment is `CONVEX_URL` (compassionate-frog-665). After editing `convex/*.ts`:
```sh
cd convex && CONVEX_DEPLOY_KEY=<key> npx convex deploy -y
```
Seed example data: `agent/.venv/bin/python scripts/seed.py`.

## 2. Agent + uAgent on Render
`render.yaml` (Blueprint) defines both services. In Render: **New → Blueprint**,
point at this repo, then fill the `sync:false` env vars per service (Environment tab).

- **twocustomer-agent** (web service, Docker `agent/Dockerfile`): set `ANTHROPIC_API_KEY`,
  `AGENT_SHARED_TOKEN`, `CONVEX_URL`, `BROWSERBASE_*`, `GEMINI_API_KEY`, `DAILY_API_KEY`,
  `DEEPGRAM_API_KEY`, `DISCORD_*`, `TWILIO_*`, `UPSTASH_REDIS_REST_*`, `GITHUB_TOKEN`
  (fallback), `SENTRY_DSN`. Health check `/health`.
- **twocustomer-uagent** (worker): set `UAGENT_SEED`, `AGENTVERSE_API_KEY`,
  `ASI_ONE_API_KEY`, `AGENT_SHARED_TOKEN`, and `AGENT_BASE_URL` = the agent service's
  https URL (e.g. `https://twocustomer-agent.onrender.com`).

Verify: `curl https://<agent>.onrender.com/health` → integrations `true`.

## 3. Web on Vercel
Root dir = `web/`.
```sh
cd web && vercel link --project twocustomer
for k in CONVEX_URL AGENT_SHARED_TOKEN AGENT_BASE_URL SESSION_SECRET \
         UPSTASH_REDIS_REST_URL UPSTASH_REDIS_REST_TOKEN WEB_BASE_URL \
         GITHUB_CLIENT_ID GITHUB_CLIENT_SECRET; do vercel env add "$k" production; done
vercel deploy --prod
```
- `AGENT_BASE_URL` = the Render agent URL.
- `AGENT_SHARED_TOKEN` = **same value** as the agent.
- `SESSION_SECRET` = long random string (signs session cookies).
- `UPSTASH_REDIS_REST_*` = same Upstash creds as the agent (session store + revocation).
- `WEB_BASE_URL` = the deployed web URL (used to build the GitHub OAuth callback).
- Turn off **Deployment Protection** so the site is public.

## 4. GitHub OAuth App (for Connect GitHub / FDE PRs)
1. github.com → Settings → Developer settings → **OAuth Apps → New**.
2. Homepage = your web URL. **Authorization callback URL** =
   `https://<your-web>/api/github/oauth/callback`.
3. Copy **Client ID** + generate a **Client Secret**.
4. Set `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` in the **web** (Vercel) env.
   Scopes requested: `repo read:org`. Until set, the setup wizard shows
   "GitHub OAuth not configured" and FDE falls back to the env `GITHUB_TOKEN`.

## Env reference
| Var | Where | Purpose |
|-----|-------|---------|
| `ANTHROPIC_API_KEY` | agent | Claude — required |
| `GEMINI_API_KEY` / `DAILY_API_KEY` / `DEEPGRAM_API_KEY` | agent | image / video / voice |
| `TWILIO_*` / `BROWSERBASE_*` | agent | SMS+call / scraping |
| `UPSTASH_REDIS_REST_*` | agent + web | memory/cache (agent) · sessions (web) |
| `AGENT_SHARED_TOKEN` | agent + web | bearer auth (same value both sides) |
| `CONVEX_URL` | agent + web | realtime data |
| `AGENT_BASE_URL` | web + uAgent | the agent's https URL |
| `SESSION_SECRET` | web | signs session cookies |
| `WEB_BASE_URL` | web | builds the GitHub OAuth callback |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | web | Connect GitHub (OAuth) |
| `GITHUB_TOKEN` | agent | FDE PR fallback when no company token |
| `UAGENT_SEED` / `AGENTVERSE_API_KEY` / `ASI_ONE_API_KEY` | uAgent | Fetch.ai identity + discovery |

## Local dev
`./scripts/dev.sh` runs Convex + agent (:8000) + web (:3000). `DEMO_MODE=1` in
`web/.env.local` shows sample data when Convex is unreachable; leave it unset in
production so the UI never fabricates data.
```

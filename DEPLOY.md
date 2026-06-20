# Deploy (Vercel)

Two Vercel projects: **web** (Next.js front end) and **twocustomer-agent**
(FastAPI control plane). The web app proxies AI calls to the agent.

Live now:
- Web: https://twocustomer-ashs-projects-548e0de1.vercel.app
- Agent: https://twocustomer-agent-ashs-projects-548e0de1.vercel.app

## Prereqs

```sh
npm i -g vercel        # or use npx vercel@latest
vercel login           # or pass --token <VERCEL_TOKEN> --scope <team>
```

## 1. Agent project (FastAPI)

Root directory = `agent/`. Vercel serves `agent/api/index.py` (ASGI). The
background monitor scheduler is skipped on serverless automatically.

```sh
cd agent
vercel link --project twocustomer-agent
# set every key the agent needs (Production):
for k in ANTHROPIC_API_KEY GEMINI_API_KEY DAILY_API_KEY DEEPGRAM_API_KEY \
  BROWSERBASE_API_KEY BROWSERBASE_PROJECT_ID DISCORD_BOT_TOKEN DISCORD_PUBLIC_KEY \
  TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN TWILIO_FROM_NUMBER SENTRY_DSN \
  AGENT_SHARED_TOKEN CONVEX_URL UPSTASH_REDIS_REST_URL UPSTASH_REDIS_REST_TOKEN; do
  vercel env add "$k" production
done
vercel deploy --prod
```

Then make it publicly reachable (web calls it server-side):
turn off **Deployment Protection** in the project's Settings → Deployment
Protection (or `ssoProtection: null` via the API).

Verify: `curl https://<agent-url>/health` → every integration `true`.

## 2. Web project (Next.js)

Root directory = `web/`. Set:

```sh
cd web
vercel link --project twocustomer
vercel env add CONVEX_URL production          # dashboard live data
vercel env add AGENT_SHARED_TOKEN production   # must match the agent
vercel env add AGENT_BASE_URL production        # the agent's https URL
# optional:
vercel env add NEXT_PUBLIC_DISCORD_CLIENT_ID production
vercel deploy --prod
```

Also turn off Deployment Protection so the site is public.

## 3. Convex (database)

Functions are already deployed to the cloud deployment in `CONVEX_URL`. After
editing `convex/*.ts`:

```sh
cd convex && npx convex deploy
```

## Env reference

| Var | Project | Purpose |
|-----|---------|---------|
| `ANTHROPIC_API_KEY` | agent | Claude (chat, fix, insights) — required |
| `GEMINI_API_KEY` | agent | image edit |
| `DAILY_API_KEY` | agent | video |
| `DEEPGRAM_API_KEY` | agent | voice |
| `TWILIO_*` | agent | SMS / call |
| `BROWSERBASE_*` | agent | web scraping |
| `UPSTASH_REDIS_REST_*` | agent | memory / cache |
| `SENTRY_DSN` | agent | errors |
| `AGENT_SHARED_TOKEN` | agent + web | bearer auth between web and agent (same value) |
| `CONVEX_URL` | agent + web | realtime data |
| `AGENT_BASE_URL` | web | the agent's https URL |

## Redeploy

```sh
cd agent && vercel deploy --prod    # agent
cd web   && vercel deploy --prod    # web
```

## Notes (serverless)

- The monitor scheduler does **not** run on Vercel (serverless has no
  always-on process). Run the monitor cadence from a long-lived host, or
  trigger `/monitor` runs on demand. Data already in Convex still renders.
- FDE preview deploys (`npx vercel deploy` inside the fix loop) run best on a
  long-lived host; on serverless the patch + validation still work, the
  preview URL step may not.

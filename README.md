# TwoCustomer

**The AI forward-deployed agent team for consumer brands.**

A brand connects its data sources and channels. TwoCustomer runs as a fleet of
agents that **listen** to every signal surface (web, news, social), **talk** to
the brand's own customers (voice / SMS / chat / video), **fix** broken
experiences in a safe sandbox, and **edit** creative (product imagery + copy) —
then ships campaigns, founder packets, and bounded fixes.

Two customers, one product: the **brand (admin)** and the **brand's customers (users)**.

## Stack

| Layer | Tech |
|---|---|
| Brain | Anthropic Claude (`claude-sonnet-4-6`) tool-calling loop |
| Web monitoring | Browserbase (remote Chrome over CDP) |
| Agent discovery | Fetch AI uAgent on ASI:One |
| Voice | Deepgram STT/TTS |
| Image edit | Google Gemini (`gemini-2.5-flash-image`) |
| Video | Daily (rooms + screenshare) |
| SMS / phone | Twilio |
| Memory / cache | Upstash Redis |
| Realtime state | Convex |
| Web | Next.js 16 (App Router, React 19, Tailwind 4) on Vercel |
| Auth | Lightweight email sign-in (cookie-based, no external provider) |
| Channels | Web · Discord · Voice · SMS · Video |

## Layout

```
agent/         Python FastAPI control plane — Claude loop, tools, monitor, FDE
web/           Next.js app — brand dashboard + customer surface
uagent/        Fetch AI uAgent (ASI:One)
convex/        Realtime schema + functions
sandbox-site/  Demo broken site the FDE loop fixes
scripts/       dev / seed / test / e2e
```

## Run (local)

```sh
cp .env.example .env            # fill in keys (Anthropic required)
cp web/.env.example web/.env.local
./scripts/dev.sh                # boots convex push + agent + web
```

Open http://localhost:3000 — see `START.md` for the 90-second demo path.

## Three loops + edit

- **Listen** — Browserbase scrapes Google News + HN for brand mentions, scores
  them (engagement + content salience), persists to Convex, synthesizes
  Claude insights, alerts high-signal.
- **Talk** — live customer interviews over Discord, Deepgram voice, Twilio
  SMS/call, or Daily video + screenshare.
- **Fix** — the FDE diagnoses a broken site in an isolated sandbox, patches it
  with Claude, and validates the fix (never touches prod).
- **Edit** — generate / edit product imagery with Gemini and rewrite copy.

## Sponsor tracks

| Track | Where |
|---|---|
| Anthropic | `claude-sonnet-4-6` agent brain (`agent/app/llm/claude.py`) |
| Browserbase | remote-Chrome web monitoring (`agent/app/state/browserbase.py`) |
| Fetch AI | discoverable ASI:One uAgent (`uagent/`) |
| Deepgram | voice customer interviews (`agent/app/channels/deepgram.py`) |
| Gemini | product image edit (`agent/app/tools/edit_image.py`) |
| Daily | video + screenshare sessions (`agent/app/channels/daily.py`) |
| Twilio | SMS + phone interviews (`agent/app/channels/twilio.py`) |
| Redis | agent memory + recall + cache (`agent/app/state/memory.py`) |
| Convex | realtime state + live monitor feed (`convex/`) |

## Docs
- `START.md` — quick start + demo path
- `docs/ARCHITECTURE.md` — system diagram + data flow
- `docs/DEMO.md` — demo script

## Tests
```sh
cd agent && .venv/bin/python -m pytest -q   # control plane
cd web && pnpm build                        # web routes
cd uagent && python3 -m pytest tests        # intent parser
```

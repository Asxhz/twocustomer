# TwoCustomer — Devpost Writeup

## Inspiration
Consumer brands drown in data across 20+ tools and fly blind on what matters
*right now*. Hiring analysts, BI devs, and engineers gets expensive fast. We
wanted one AI team that watches everything, talks to the brand's own customers,
and ships the fix.

## What it does
TwoCustomer is the AI forward-deployed agent team for consumer brands. A brand
connects its data and channels; TwoCustomer runs 24/7 to:
- **Monitor** every signal surface (web, social, support, Slack),
- **Interview** the brand's customers by voice or chat,
- **Act** — surface revenue opportunities / cost leaks / anomalies, build
  campaigns, and produce founder/CMO **packets** (evidence → action → shippable
  PR/ticket).

Two customers, one product: the brand (admin) and the brand's customers (users).

## How we built it
- **Brain:** Anthropic Claude (`claude-sonnet-4-6`) tool-calling loop, provider-agnostic.
- **Monitoring:** Browserbase-hosted Chrome (CDP) + browser-use, plus Reddit JSON;
  dedup + adaptive per-platform signal scoring.
- **Discovery + action:** a Fetch AI uAgent on ASI:One (Chat Protocol) routes
  intents into the same engine.
- **Voice:** Deepgram STT/TTS for customer interviews.
- **Memory:** Upstash Redis — recall past insights ("beyond caching") + cache.
- **Alerts:** Slack (block-kit) + `/twocustomer` slash command.
- **State/UI:** Convex realtime + Next.js 16 (Vercel), two-tier brand/customer surface.

The engine, channels, web surface, and uAgent were all built at the event around
the Claude tool-calling loop, with each sponsor platform wired in as a first-class
capability.

## Sponsor tracks
| Track | What we did |
|---|---|
| Best Use of Anthropic | `claude-sonnet-4-6` drives the whole agent + packet engine |
| Best Use of Browserbase | hosted-Chrome web monitoring via CDP |
| Best Use of Fetch AI | discoverable, action-taking ASI:One uAgent |
| Best Use of Deepgram | voice customer-interview channel |
| Redis: Beyond Caching | agent memory + semantic recall + cache |
| Slack | brand alerts + slash command |

## Challenges
Wiring six sponsor platforms into one coherent Claude-first stack across four
packages (agent, engine, web, uAgent), keeping them all green, and making every
integration degrade gracefully so the demo runs even without every key.

## What's next
Live Agentverse publish, embedding-based memory recall, deeper packet→PR
automation, and per-brand learning loops.

## Try it
`./scripts/dev.sh` → `python scripts/seed.py` → open `/admin`. See `docs/DEMO.md`.

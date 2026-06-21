# TwoCustomer — Architecture

```
  CHANNELS                 ┌────────────────────────────────────────┐
  ─ web chat  ─────────────┤              web/  (Next.js 16)         │
  ─ Discord ────┐          │  Vercel · landing · /admin (brand) ·    │
  ─ voice (DG) ─┤          │  /u (customer) · packets · sessions ·   │
  ─ SMS (Twilio)┤          │  studio · integrations                  │
  ─ video (Daily)          └───────────────┬────────────────────────┘
                │                           │ /api/* (SSE proxy, token-auth)
  ASI:One ──────┴──────────▶┌──────────────▼─────────────────────────┐
  (uagent/, Fetch AI)       │   agent/  (FastAPI) — Claude tool loop  │
                            │   /chat /monitor /fde/fix /edit/image   │
                            │   /interview /session/video /discord/*  │
                            └──┬───────────┬───────────┬──────────────┘
                               │           │           │
        ┌──────────────────────┘           │           └──────────────┐
        ▼                                   ▼                          ▼
  Browserbase                       Redis (Upstash)             Convex
  remote Chrome (CDP):                memory + recall + cache     realtime feed,
  Google News / HN scrape,                                        brands/mentions/
  score → Convex                                                  insights/packets/
                                                                  sessions/messages
```

## Components

| Path | Role |
|---|---|
| `web/` | Next.js 16 (App Router, Tailwind 4) on Vercel. Two-tier surface: brand-admin (`/admin/*`) + customer (`/u/*`), packets, sessions, studio, integrations. Proxies to the agent via token-authenticated SSE. Email sign-in gates the brand console. |
| `agent/` | FastAPI control plane. Claude tool loop (`claude-sonnet-4-6`), the monitor scheduler, the FDE sandbox fix loop, channel routes (Discord, Deepgram voice, Twilio, Daily), Redis memory, Convex client. The web app and uAgent both call it. |
| `agent/app/monitor/` | Listen loop: scrapers (HN keyless + Google News via Browserbase) → dedup → score → Convex mentions → Claude insight. |
| `agent/app/fde/` | Fix loop: copy a site into an isolated sandbox, let Claude diagnose + patch, validate, optional Vercel preview. Never touches prod. |
| `uagent/` | **Fetch AI** uAgent — Chat Protocol, discoverable on ASI:One, parses intent and drives the control plane. |
| `convex/` | Realtime schema + functions (brands, mentions, insights, campaigns, packets, sessions, messages). |
| `sandbox-site/` | A deliberately broken demo site (`hi hi my my`) the FDE loop fixes. |

## Integrations
- **Anthropic** — `claude-sonnet-4-6` is the brain everywhere.
- **Browserbase** — remote Chrome over CDP for web monitoring.
- **Fetch AI / ASI:One** — discoverable, action-taking uAgent.
- **Deepgram** — STT/TTS for customer voice interviews.
- **Gemini** — product image generation + edit.
- **Daily** — video rooms + screenshare.
- **Twilio** — SMS + phone interviews.
- **Redis (Upstash)** — agent memory, recall, response cache.
- **Convex** — realtime state + live monitor feed.

## Data flow (listen → act)
1. The monitor scheduler scrapes brand mentions (HN + Google News via Browserbase).
2. Dedup + score (engagement + content salience) → write to Convex `mentions`;
   high-signal → channel alert.
3. Claude synthesizes an **insight**; stores it in Redis memory + Convex.
4. Insight → **packet** (evidence → action → artifact) in `/admin`.
5. Customer voice / chat / SMS / video **sessions** feed validated insight back in.
6. All reachable from web, Discord, voice, or ASI:One — same control plane.

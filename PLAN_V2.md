# TwoCustomer v2 — Build Plan (FDE + CMO + Live Research)

## The product, sharpened
TwoCustomer is a **forward-deployed AI teammate for consumer brands**. Three loops + one capability:

1. **LISTEN (CMO)** — monitor every signal surface → insights → **marketing recommendations grounded in real customer feedback**. *(built, live)*
2. **TALK (Research)** — run **live customer interviews** across Discord / browser voice / SMS / phone call → validated insight that feeds the CMO loop. *(FSM + Discord/Deepgram built; SMS/call to add)*
3. **FIX (FDE)** — a bug ("site renders `hi hi my my`") → agent patches it in a **safe Vercel sandbox / preview branch** (no access to confidential/prod) → user sees the fixed preview → validate. *(loop proven in `agent/sim`; real sandbox to add)*
4. **EDIT (capability)** — voice/text: *"make the product image less hefty, cleaner"* → AI edits the **image / copy / format**. Works from the site, Discord, or Snap Spectacles (Spectacles = just the mic). *(to add)*

## What exists vs what to build
| Capability | State |
|---|---|
| Claude (Sonnet 4.6) tool-loop, SSE streaming | ✅ live |
| Monitor → score → insight → packet (CMO + FDE detect) | ✅ live (real HN scrape) |
| Discord (slash + Ed25519 + webhook alerts) | ✅ live |
| Deepgram voice (STT/TTS) | ✅ live |
| Redis memory/cache/locks · Convex realtime · Sentry | ✅ live |
| Multi-agent fix loop (Monitor→Analyst→Fixer→Validator) | ✅ proven in `agent/sim` |
| Customer-interview FSM + `/interview` API | ✅ built (text); voice/SMS to wire |
| **Twilio SMS** | ❌ build |
| **Twilio phone call** (agent calls the customer) | ❌ build |
| **AI image/copy editing** ("make it less hefty") | ❌ build |
| **Real Vercel sandbox FDE** (fix a site on a preview branch) | ❌ build |
| **New beautiful UI from scratch** | ❌ build |
| Snap Spectacles surface | ➖ framed as a voice mic into EDIT |

## Architecture additions
- `agent/app/channels/twilio.py` — SMS webhook + send; Voice via TwiML `<Connect><Stream>` → WS bridge → Deepgram STT → Claude → Deepgram TTS back. Signature-verified.
- `agent/app/tools/edit_image.py` — image generate + **img2img edit** (provider-pluggable: **fal / Replicate** for flux img2img; **Pika**/**Midjourney** for the sponsor tracks). Returns a new asset URL; persisted to Convex.
- `agent/app/tools/edit_copy.py` — Claude rewrites product copy/format to a target (shorter, cleaner, on-brand).
- `agent/app/fde/sandbox.py` — **Vercel Sandbox** (GA): clone a *demo/sandbox* repo, Claude locates the bug, writes a patch, sandbox builds + deploys a **preview URL** the user opens. Hard allowlist of editable files; never touches prod/secrets.
- `web/` — redesigned surface (research-driven, `frontend-design` skill): marketing landing + brand console + customer surface, with a **call button** (Discord/phone) and live edit/interview panels.

## How the pieces work (the things you asked)
**Commands** — natural language routed by Claude to tools, *plus* explicit ones everywhere:
`/monitor <brand>` · `/interview <customer|all>` · `/fix <bug url|desc>` · `/edit <asset> "<instruction>"` · `/campaign <brief>` · `/insights` · `/call <customer>`.
Same command set in Discord, web chat, SMS, and voice.

**Interviews** — admin starts an interview for their brand → TwoCustomer reaches the customer on their channel (Discord DM, SMS thread, web link, or **places a phone call**). The interview FSM drives Q&A; text channels exchange messages, voice channels stream Deepgram STT/TTS. Transcript → Claude → validated insight → auto-feeds marketing recs.

**Storage** — Convex tables: `brands, mentions, insights, campaigns, packets, sessions(interviews), edits(image/copy), fixes(PRs), calls`. Redis: agent memory, response cache, rate-limits, per-session interview/call state.

**Logic** — one Claude tool-loop is the orchestrator; tools do the work; the multi-agent fix swarm (`sim/agents.py` pattern) handles detect→fix→validate; channels are thin adapters in/out.

**EDIT / Spectacles** — voice command ("make it less hefty, cleaner") → `edit_image` (img2img) → returns the new product render → shown back in the channel (or the Spectacles lens). Spectacles is the mic + display; the brain is the same.

## Protections (real)
- **FDE sandbox**: edits only a forked/preview branch in **Vercel Sandbox**; file allowlist; no env/secret access; every change is a reviewable diff before deploy; nothing hits prod.
- **Channel auth**: Discord Ed25519, Twilio signature, Slack HMAC (done).
- **Rate limits + locks** on every action (done); secrets only in gitignored `.env`.
- **Human gate**: destructive/marketing actions return a proposal the admin approves.

## Phased build (prioritized for the hackathon)
- **P1 — EDIT tool** (image gen + img2img + copy) — highest "wow", sponsor-aligned (Pika/Midjourney). ~½ day.
- **P2 — Twilio SMS + phone-call interview** (SMS first, then `<Stream>`→Deepgram voice). ~1 day.
- **P3 — Vercel Sandbox FDE** — fix a real broken demo site on a preview branch, validate. ~1 day.
- **P4 — New UI from scratch** — landing + console + customer + call/edit/interview panels. ~1 day.
- **P5 — Wire it all into Discord + site + voice; polish; protections; demo script.**

## Recommended demo (judge-facing)
1. Brand console: TwoCustomer surfaces a real insight from live chatter → recommends a campaign.
2. **Live interview**: it **calls a "customer"** (Twilio) / Discord voice → asks, transcribes, extracts insight on screen.
3. **EDIT**: *"make the product photo cleaner and less hefty"* → new render appears.
4. **FDE**: the brand's site shows `hi hi my my` → agent diagnoses, patches on a **sandbox preview branch**, opens the fixed URL, validates. No prod touched.
5. Show it all reachable from **Discord** and the **site**.

## Risks / cuts
- Twilio voice `<Stream>` is the trickiest; SMS + Deepgram browser-voice are the safe live-call story if time is short.
- Full Spectacles Lens = out; the voice→edit capability stands on its own.
- Vercel Sandbox needs a token; fallback = patch a local repo + Vercel preview deploy.

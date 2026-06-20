# TwoCustomer — Demo Script (v2)

**Pitch (15s):** TwoCustomer is a forward-deployed AI teammate for consumer brands.
It **listens** to every signal, **talks** to your customers (Discord, voice, SMS,
phone, video), **fixes** bugs on your site in a safe sandbox, and **edits** your
images and copy — all from one Claude brain, reachable on the web, Discord, or ASI:One.

## Pre-flight
```sh
uv run --project agent python scripts/live_test.py   # show which integrations are LIVE
./scripts/dev.sh                                     # web :3000 + agent :8000 + convex
```

## Flow (≈4 min)

**1. LISTEN — insight + marketing (40s)** — `/admin`
- Chat: *"Monitor my brand right now, give me the top finding, propose one action."*
- Claude calls `monitor_brand` (live scrape) → picks the highest-signal item →
  `propose_fix` → a founder/CMO packet with evidence + a shippable action.
- `/monitor` shows the live feed (Convex badge), `/admin/insights` the insight.

**2. TALK — live interview (50s)** — pick the channel that's keyed:
- **Video + screen share** (`/session/live/video`): customer joins, shares their
  screen (their broken site!), the agent interviews + watches. *(Daily)*
- **Phone call**: `POST /twilio/call {to}` → the agent calls the customer and runs
  the interview by voice. *(Twilio)*  · **SMS**: text the Twilio number.
- **Discord**: `/twocustomer interview a customer about packaging`.
- Transcript → validated insight in `/sessions` → feeds the marketing loop.

**3. FIX — forward-deployed (45s)** — `/admin/fix`
- The brand's site renders `hi hi my my`. Enter the symptom → **Diagnose & fix**.
- Claude reads the code, finds the bug, patches a **sandbox copy** (never prod),
  validates by running it → before `hi hi my my` / after `hi my name is` → ✅ resolved.
- With `VERCEL_TOKEN`, it opens a live preview URL.

**4. EDIT — make it better (35s)** — `/admin/studio`
- *"Make a clean studio photo of the flute, less hefty, better lighting."*
- Gemini generates/edits the image → shown in the panel. Same by voice ("Spectacles").

**5. EVERYWHERE (20s)** — `/integrations`
- Same commands on **Discord**, the **site**, **voice/SMS/phone**, **video**, and
  **ASI:One** (the Fetch uAgent: message *"monitor Aurora Drinks"* / *"fix the site"*).

## Protections (say this)
- The FDE only edits an **isolated sandbox copy** — file allowlist, no `.env`/prod access.
- Every channel is **auth-verified** (Discord Ed25519, Twilio + Slack signatures).
- Rate limits + locks on every action; secrets only in gitignored `.env`.
- Marketing/destructive actions return a **proposal the admin approves**.

## Sponsor map
Anthropic (brain + FDE) · Browserbase (monitoring) · Fetch AI (ASI:One agent) ·
Deepgram (voice) · Redis (memory) · Discord · Gemini (image edit) · Daily (video) ·
Twilio (SMS/call) · Sentry (observability).

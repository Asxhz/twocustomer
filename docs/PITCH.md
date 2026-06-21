# TwoCustomer — Pitch & Presentation Guide

## The one-liner

**TwoCustomer is an AI Forward-Deployment Engineer that's also your CMO — it watches the web for your brand, talks to your customers, and ships fixes to your product, on its own.**

---

## The 60-second pitch (spoken)

> Every consumer brand has two customers it has to keep happy: the people who buy
> the product, and the founder who has to grow it. Today that takes a whole team —
> a support engineer to fix what breaks, a marketer to watch what people are
> saying, an analyst to turn it into action.
>
> TwoCustomer is that whole team, as one always-on AI.
>
> It does two jobs. First, it's a **Forward-Deployment Engineer**: when a customer
> hits a bug, they type `/report`, hop on a call, share their screen — and the
> agent *watches*, diagnoses the actual code, fixes it in a safe sandbox, and ships
> a live preview of the fix in under a minute. No ticket, no waiting on a dev.
>
> Second, it's a **CMO**: every hour it scans the open web — news, Reddit, Hacker
> News, X — for what people are saying about your product, dedupes the noise into
> ranked insights, and when it finds a real problem in your code, it opens the fix
> *itself* and tells you what it did.
>
> One product, two customers, zero headcount. That's TwoCustomer.

---

## The problem → solution → wow

- **Problem:** A small brand can't afford a forward-deployed engineer *and* a CMO.
  Bugs sit in a queue; signal on the web goes unseen until it's a crisis.
- **Insight:** Both jobs are the same loop — *listen → understand → act* — and an
  agent with the right tools can run it end to end.
- **Solution:** An agent team that listens (web + voice + chat), understands
  (Claude), and acts (writes code, deploys previews, opens PRs, drafts campaigns).
- **Wow moment:** A non-technical person reports a bug on a video call, and 45
  seconds later there's a working, deployed preview of the fixed site.

---

## What's real (not slideware)

Everything below runs on live APIs — there's a `/status` page that shows them green:

| Capability | Powered by |
|---|---|
| The brain (chat, diagnosis, insights) | Anthropic **Claude** (Haiku/Sonnet/Opus, routed by task) |
| Live web monitoring (hourly, deduped) | **Browserbase** + HN/Reddit/News/X |
| Fix → live preview deploy | **Vercel** |
| Open PRs on the brand's repo | **GitHub** |
| Realtime dashboard state | **Convex** |
| Memory, dedup, rate-limits | **Upstash Redis** |
| Video call + screen share | **Daily** |
| Voice interviews | **Deepgram** |
| Product image edits | **Gemini** |
| SMS / phone | **Twilio** |
| Agent discovery | **Fetch AI / ASI:One** |

---

## Differentiators (say these if asked "why is this hard / different")

1. **It writes and ships real code**, not just chat — sandboxed diagnosis →
   validated patch → live preview, with prod never touched.
2. **Human-in-the-loop *and* autonomous** — `/report` is interactive (a person
   shows the bug); the CMO loop runs unattended and only auto-fixes when a founder
   opts in (gated, with a cooldown — it won't spam).
3. **Two surfaces, one brain** — the same agent serves the brand (admin) and the
   brand's customers (users), with role-gating so customers can never touch code.
4. **Graceful everywhere** — every integration degrades cleanly if a key is
   missing; nothing hard-crashes.

---

## Demo script — the golden path (≈3 min)

> Run it locally for the live demo — the full FDE (real Claude fix + real Vercel
> preview) is verified working on the local stack.

**Setup (before you present):**
1. `./scripts/dev.sh` → boots Convex push, agent (:8000), web (:3000).
2. Open `http://localhost:3000`, confirm `/status` is green, and have the
   `demo-broken-site` ready as the thing that "breaks."
3. Sign up once so you land on the dashboard (skip onboarding live if you can).

**On stage:**
1. **(20s) Land on the start page.** "This is TwoCustomer." Toggle light/dark to
   show polish. One line on the two-customer idea.
2. **(30s) Frame it.** "Two customers: the brand, and the brand's customers. One
   AI does the FDE *and* the CMO job."
3. **(75s) THE MONEY SHOT — `/report`.** In the admin chat, type `/report the
   homepage hero shows the wrong text`. Agent offers a call → click **Join**,
   share your screen → click **"I'm sharing my screen"** → agent says *"I can see
   your screen — building a fixed preview…"* → **open the live preview** showing
   the corrected site. Say: *"A customer just got a deployed fix in under a minute,
   no developer in the loop."*
4. **(30s) The CMO half.** Open `/monitor` (live mentions) and `/admin/insights`.
   "Every hour it scans the web, dedupes, and ranks what matters — and on a
   connected repo it can open the fix itself."
5. **(15s) `/status`.** "All of this is real — here's every live integration."
6. **Close** with the one-liner.

---

## If something fails (fallbacks)

- **Agent unreachable / call button dead:** you're on the deployed site behind
  Vercel protection or pointing at localhost. Switch to the **local** stack
  (`./scripts/dev.sh`) — that's the demo-ready path.
- **Live fix is slow:** it's a real Claude call + real deploy (~30–45s). Narrate
  the tool chips ("diagnosing… patching… deploying…") so the wait sells the work.
- **Preview asks for a Vercel login:** that's Deployment Protection — open it in a
  browser already signed in to Vercel, or have a screenshot ready.
- **No network:** keep a 30-second screen recording of the `/report` flow as backup.

---

## Q&A cheat sheet

- *"Does it really change code?"* Yes — sandboxed copy, Claude patches the file,
  we run it to validate the bug is gone, then deploy a preview. Prod is never
  touched; interactive fixes never open a PR.
- *"What stops it from breaking things autonomously?"* The auto-fix is opt-in
  per brand, only fires on high-signal *risk* findings, has a cooldown, and opens
  a PR for review rather than merging.
- *"Why two customers?"* Because a brand's success depends on both the buyer's
  experience and the founder's leverage — we serve both from one agent.
- *"What's the moat?"* The end-to-end loop (listen→understand→act) wired across
  ten real services, with the safety rails to let an agent actually ship.

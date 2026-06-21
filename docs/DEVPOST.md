# Two Customer — Devpost

## Inspiration

Every consumer brand has to keep **two customers** happy: the people who buy the product, and the founder trying to grow it. Serving both normally takes a team you can't afford early on — a forward-deployed engineer to fix what breaks, and a CMO to watch the market and act on it. We noticed both jobs are really the *same loop*: **listen → understand → act.** If an agent had the right tools — eyes on the web, a voice to talk to customers, and hands to write and ship code — it could run that loop end to end. That's the idea behind **TwoCustomer**: one AI that is both your forward-deployed engineer *and* your CMO.

## What it does

TwoCustomer is an always-on AI agent team for a consumer brand, serving two surfaces from one brain:

- **Forward-Deployment Engineer (interactive).** A customer types `/report`, hops on a video call, and shares their screen. The agent acknowledges what it sees, diagnoses the *actual code* in an isolated sandbox, patches it, validates the bug is gone, and ships a **live preview deployment** of the fix — in under a minute, with production never touched and no developer in the loop.
- **CMO (autonomous).** Every hour it scans the open web — news, Reddit, Hacker News, X, LinkedIn — for what people are saying about the brand, **deduplicates** so it never re-surfaces the same finding, and synthesizes the signal into ranked insights. On a connected repo (opt-in), it can open the fix itself and notify the founder.
- **Talks to customers anywhere** — chat, **voice** interviews, **video** + screenshare, and **SMS/phone** — and turns those conversations into structured signal.
- **Two customers, one product** — role-gating means the brand (admin) gets the dashboard, FDE, and CMO, while the brand's own customers get a safe surface to report issues and talk to the agent, and can never touch code.

It's all real: a `/status` page shows every live integration green.

## How we built it

A **Next.js 16** web app (brand dashboard + customer surface) talking to a **FastAPI** agent control plane that runs a **Claude tool-calling loop**, with **Convex** as the realtime backbone. Each integration maps to a stage of the listen→understand→act loop:

| Integration | What it does | Where |
|---|---|---|
| **Anthropic Claude** | The agent brain — Sonnet 4.6 for routine reasoning, Opus 4.8 for the hard work (diagnosing, planning, building). Orchestrates the tool-calling loop, reasons over signal, drafts deliverables. | `agent/app/llm/claude.py` |
| **Browserbase** | The always-on eyes — remote-Chrome sessions to read social/web/reviews/news at scale, beyond plain HTTP. | `agent/app/state/browserbase.py` |
| **Fetch AI** | Discoverability — published as a uAgent on ASI:One so anyone can find and invoke TwoCustomer as a real autonomous agent. | `uagent/` |
| **Deepgram** | Voice customer interviews (speech-to-text + text-to-speech). | `agent/app/channels/deepgram.py` |
| **Gemini** | The creative arm — generates and edits product imagery. | `agent/app/tools/edit_image.py` |
| **Daily** | Video + screenshare sessions so the agent can see exactly what's being discussed. | `agent/app/channels/daily.py` |
| **Twilio** | SMS + phone interviews — reach customers wherever they are. | `agent/app/channels/twilio.py` |
| **Redis (Upstash)** | Agent memory + recall + cache — gets smarter about a brand over time and avoids repeating work. | `agent/app/state/memory.py` |
| **Convex** | Realtime state + live monitor feed streamed to the operator's UI. | `convex/` |
| **Vercel + GitHub** | The hands — the FDE deploys live preview fixes (Vercel) and opens PRs on the brand's repo (GitHub). | `agent/app/fde/` |

Together: **Convex/Redis** hold state and memory, **Browserbase** feeds the monitor, **Deepgram/Twilio/Daily** run the customer conversations, **Claude** reasons and decides, and **Gemini + the FDE/codegen path** execute the work — exposed both as a web app and as a Fetch AI discoverable agent.

## Challenges we ran into

- **Letting an agent ship real code safely.** The FDE copies the site into an isolated sandbox, lets Claude patch a single file, *runs it to validate the bug is actually gone*, and only then deploys a preview — prod is never touched and interactive fixes open no PR. Getting those rails right was the core of the project.
- **The autonomous/interactive split.** The CMO can act on its own, so we gated auto-fix per brand, fired it only on high-signal *risk* findings, and added a cooldown so it can't spam PRs.
- **Theming the whole app two ways.** With hundreds of hardcoded dark-mode utilities, we made light/dark work app-wide by remapping Tailwind's white/black to semantic "ink"/"surface" variables and flipping them per theme — instead of rewriting every component.
- **Real deployment is hard.** We hit Vercel deployment protection, serverless limits on the FDE, missing production env vars, and a mismatched git connection — and learned to diagnose all of it from the outside.
- **Graceful degradation.** Every integration had to turn off cleanly when a key is missing, so the app never hard-crashes during a demo.

## Accomplishments that we're proud of

- **A real, end-to-end fix → live deploy** driven by a non-technical user on a video call — verified working, not mocked.
- **Ten+ live integrations** working together in one coherent loop, all visible green on a status page.
- **A genuine two-customer architecture** with role-gating, so the same brain safely serves both the brand and its customers.
- **An autonomous CMO with real safety rails** — it acts, but only within bounds a founder controls.
- A **polished product**, down to a typewriter landing page and a clean light/dark theme.

## What we learned

- **Tool design is the product.** An agent is only as good as the tools and guardrails you give it; the magic is in the sandbox-validate-deploy loop, not the prompt.
- **Autonomy needs brakes.** Opt-in gating, cooldowns, dedup, and PR-for-review are what make an acting agent trustworthy.
- **Ship-readiness ≠ demo-readiness.** Production deployment (protection, env, serverless constraints, hosting) is its own hard problem distinct from making the feature work.
- **Design systems pay off.** A small abstraction (semantic color tokens) turned an impossible-looking theming task into a few lines.

## What's next for Two Customer

- **Full autonomous CMO on a long-lived host** so the hourly monitor → auto-fix → founder-notification loop runs 24/7 (beyond serverless limits).
- **Real screen vision** on calls so the agent literally sees the bug instead of being shown it.
- **Deeper FDE** — multi-file fixes, test generation, and richer PRs.
- **More channels and deeper memory** — every customer conversation compounding into sharper brand insight.
- **Agent-economy presence** — leaning into the Fetch AI/ASI:One listing so other agents and people can discover and hire TwoCustomer.

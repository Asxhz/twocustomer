# How TwoCustomer works

**TwoCustomer is an AI Forward-Deployment Engineer that is also your CMO.**

A consumer brand connects its repo and channels. From then on, one always-on agent
team does two jobs a startup usually hires two people for:

- **The Forward-Deployment Engineer (FDE).** When something is broken or could be
  better, it gets on a call with the person who noticed, watches them show the
  problem, fixes the code in an isolated sandbox, and ships a *private preview* of
  the fix — without touching production.
- **The CMO.** It watches the open web every hour (news, Reddit, HN, X, LinkedIn),
  turns the noise into ranked insights, and — when a finding is a real risk on a
  connected repo — opens the fix itself and tells the founder what it did.

There are **two customers** in the product, which is where the name comes from:

| Customer | Who | What they get |
|---|---|---|
| **Admin** | the brand / founder | dashboard, insights, campaigns, the FDE, the autonomous CMO |
| **User** | the brand's own customers | a place to report problems and talk to the agent (chat / voice / video) |

---

## The two flows

### 1. Interactive: `/report` → call → screen-share → live preview fix

This is the human-in-the-loop FDE. In the admin chat (and over Discord), a user types:

```
/report   (also /idea, /recommend, /rec)
```

1. The agent offers a **video call** and asks the user to **share their screen**.
2. Once sharing, the agent acknowledges it can see the screen and asks them to show
   the issue.
3. The agent runs the real FDE loop on the demo/connected site: copy into an
   isolated sandbox → Claude diagnoses the bug → patch the sandbox → run it to
   validate the symptom is gone.
4. It deploys a **private Vercel preview** and shows the user a before→after plus a
   link. **Nothing is pushed to production and no PR is opened** — the preview is
   gated to the Vercel account owner, so it's "viewable to the user," not the world.

Code: `web/components/ChatThread.tsx` (slash commands + flow), `web/app/api/fix`
→ agent `POST /fde/fix` → `agent/app/fde/sandbox.py` (`fix_site` → `vercel_deploy`).
The demo target is `demo-broken-site/` (override with the `FDE_DEMO_SITE` env var).

### 2. Autonomous: hourly monitor → insight → auto-fix → founder notification

This is the CMO running on its own.

1. An APScheduler job ticks on a per-brand cadence (default 30 min, adjustable
   1–1440). `agent/app/monitor/scheduler.py`.
2. It scrapes the web for the brand's terms via Browserbase + public APIs, then
   **deduplicates** so it never re-surfaces something it has already seen
   (in-process set + Convex `by_brand_external` index). `agent/app/monitor/`.
3. Fresh, high-signal mentions are synthesized into an **insight** (Claude), stored,
   and the founder is notified. `agent/app/monitor/insight.py`.
4. If the brand has a **connected repo** and opted in (`auto_fix`), a *risk* insight
   triggers the FDE automatically — open a **PR + preview** — and posts an
   "Auto-fix shipped" notification to the founder's dashboard. A 6-hour per-brand
   cooldown keeps it from shipping on every tick. `scheduler.py:_auto_fix`.

The difference between the flows is deliberate: the **interactive** fix is
preview-only (a human is watching), the **autonomous** fix opens a PR (the team
reviews before merge).

---

## How each API is used

Every key is optional — if it's missing, that capability degrades gracefully and
nothing crashes (`scripts/check_env.py` reports what's set).

| API / Service | Env keys | What it does here | Where |
|---|---|---|---|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | The brain. Tool-calling chat loop; FDE bug diagnosis; insight synthesis; copy editing; research synthesis. Routed by task: **Haiku** for chat/classify/monitor, **Sonnet** for diagnose/research/campaign, **Opus** for planning. | `agent/app/llm/`, `app/core/loop.py`, `app/llm/router.py` |
| **Vercel** | `VERCEL_TOKEN`, `VERCEL_SCOPE` | Deploys the fixed site as a **preview URL** (interactive) or PR-preview (autonomous). Scope = your team (`dhruv-bhadauriyas-projects`). | `app/fde/sandbox.py`, `app/fde/repo_sandbox.py` |
| **GitHub** | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | OAuth App so a brand connects its repo; the agent reads the repo and opens PRs under the brand's identity. | `web/app/api/github/oauth/*`, `app/fde/github.py` |
| **Browserbase** | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` | Remote Chrome over CDP to scrape rendered pages / RSS for monitoring (news, X via Nitter, LinkedIn). HN uses public Algolia (keyless); Reddit uses its OAuth API. | `app/state/browserbase.py`, `app/monitor/scrapers.py` |
| **Convex** | `CONVEX_URL`, `CONVEX_DEPLOY_KEY` | Realtime store: `mentions`, `insights`, `campaigns`, `packets`, `brands`, `notifications`, `sessions`, `invites`. Powers the live dashboard and persistent dedup. | `convex/`, `app/state/convex_client.py` |
| **Upstash Redis** | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Memory/cache, monitor-config persistence, rate limits, and the locks behind monitor dedup + the auto-fix cooldown. | `app/state/redis_client.py`, `app/state/limits.py` |
| **Daily** | `DAILY_API_KEY`, `DAILY_DOMAIN` | Video rooms with **screen share** for the `/report` call. | `app/tools/video_tool.py`, `web/app/session/[id]/video` |
| **Deepgram** | `DEEPGRAM_API_KEY` | Speech-to-text / text-to-speech for voice customer interviews. | `app/main.py` (`/voice/*`) |
| **Google Gemini** | `GEMINI_API_KEY`, `GEMINI_IMAGE_MODEL` | Product image generation / editing in the Studio. | `app/tools/edit_image.py` |
| **Twilio** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` | SMS + phone interviews and notifications. | `app/main.py` (`/twilio/*`) |
| **Fetch AI / ASI:One / Agentverse** | `ASI_ONE_API_KEY`, `AGENTVERSE_API_KEY`, `UAGENT_SEED` | uAgent registration + discovery on ASI:One. | `uagent/` |
| **Discord** | `DISCORD_BOT_TOKEN`, `DISCORD_PUBLIC_KEY`, `DISCORD_APP_ID`, … | `/report` `/setup` `/rec` `/idea` slash commands and pulling channel context into a fix. | `app/main.py` (`/discord/*`) |
| **Sentry** | `SENTRY_DSN` | Error capture. | `app/obs/` |
| **Arize** | `ARIZE_API_KEY`, `ARIZE_SPACE_ID` | Agent run tracing / observability. | `app/obs/` |

---

## Account configuration (yours vs. a fresh deploy)

The system is no longer hardcoded to one account. To run it on your own stack:

- **Vercel**: set `VERCEL_TOKEN` + `VERCEL_SCOPE` in `.env`. The FDE deploys there;
  `scripts/set_agent_url.py` reads the scope from env (no baked-in team id).
- **GitHub**: register an OAuth App, set `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`,
  callback `<WEB_BASE_URL>/api/github/oauth/callback`.
- **Demo site**: `FDE_DEMO_SITE` selects which folder the interactive fix targets
  (default `demo-broken-site`).
- **Discord `/setup`**: links to the email the founder signed up with (admin-gated).
  `DEMO_FOUNDER_EMAIL` can override this for a scripted demo, but it's unset by default.

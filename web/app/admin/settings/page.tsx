import Nav from "@/components/Nav";
import CompanyNameForm from "@/components/CompanyNameForm";
import GithubTokenForm from "@/components/GithubTokenForm";
import { getSession } from "@/lib/session";
import { convexQuery } from "@/lib/convexApi";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

interface Company {
  name: string;
  githubLogin?: string;
  discordGuild?: string;
}

// Each platform connector + the /health key that proves it's configured.
const CONNECTORS: { name: string; key: string; note: string }[] = [
  { name: "Anthropic Claude", key: "llm", note: "Agent brain. required (ANTHROPIC_API_KEY)" },
  { name: "Convex", key: "convex", note: "Realtime data (CONVEX_URL)" },
  { name: "Redis (Upstash)", key: "redis", note: "Sessions + memory (UPSTASH_REDIS_REST_*)" },
  { name: "Browserbase", key: "browserbase", note: "Web monitoring (BROWSERBASE_API_KEY)" },
  { name: "Gemini", key: "gemini", note: "Image edit (GEMINI_API_KEY)" },
  { name: "Daily", key: "daily", note: "Video calls (DAILY_API_KEY)" },
  { name: "Deepgram", key: "deepgram", note: "Voice STT/TTS (DEEPGRAM_API_KEY)" },
  { name: "Fetch.ai", key: "fetch", note: "Discoverable uAgent (ASI_ONE / AGENTVERSE)" },
];

async function getCompany(companyId?: string): Promise<Company | null> {
  if (!companyId) return null;
  return convexQuery<Company | null>("companies:get", { id: companyId });
}

async function getHealth(): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(`${AGENT_BASE_URL}/health`, { headers: agentHeaders(), cache: "no-store" });
    return r.ok ? await r.json() : null;
  } catch {
    return null;
  }
}

function live(health: Record<string, unknown> | null, key: string): boolean {
  if (!health) return false;
  if (key === "llm") return health.llm === "claude";
  return Boolean(health[key]);
}

export default async function Settings({
  searchParams,
}: {
  searchParams: Promise<{ github?: string; discord?: string }>;
}) {
  const { github, discord } = await searchParams;
  const session = await getSession();
  const [company, health] = await Promise.all([getCompany(session?.companyId), getHealth()]);
  const agentUp = health !== null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mb-6 text-sm text-white/50">
          Your company, connections, and live connector status.
        </p>

        {!agentUp && (
          <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            Agent unreachable. connector status can&apos;t be read. Check the agent deployment / AGENT_BASE_URL.
          </div>
        )}

        {/* Company profile */}
        <section className="mb-6 rounded-xl border border-white/10 bg-white/[0.02] p-5">
          <h2 className="mb-3 text-sm font-medium text-white/70">Company</h2>
          <CompanyNameForm initial={company?.name ?? ""} />
        </section>

        {/* OAuth connectors */}
        <section className="mb-6 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <h3 className="font-medium">GitHub</h3>
            <p className="mt-1 text-xs text-white/50">Read repos, build sandbox previews, open PRs.</p>
            {company?.githubLogin ? (
              <p className="mt-3 text-sm text-accent-soft">✓ Connected as @{company.githubLogin}</p>
            ) : (
              <GithubTokenForm connected={false} primary />
            )}
            {/* OAuth is optional and only shown when an OAuth app is configured. */}
            {!company?.githubLogin && process.env.GITHUB_CLIENT_ID && (
              <a href="/api/github/oauth" className="mt-2 inline-block text-xs text-white/50 underline hover:text-white/80">
                or connect via OAuth
              </a>
            )}
            {github === "error" && <p className="mt-2 text-xs text-red-300">OAuth connect failed. paste a token instead.</p>}
            {company?.githubLogin && <GithubTokenForm connected />}
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <h3 className="font-medium">Discord</h3>
            <p className="mt-1 text-xs text-white/50">Pull customer chatter + post alerts.</p>
            {company?.discordGuild ? (
              <p className="mt-3 text-sm text-accent-soft">✓ Connected · {company.discordGuild}</p>
            ) : discord === "unconfigured" ? (
              <p className="mt-3 text-xs text-amber-300">Set DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET.</p>
            ) : (
              <a href="/api/discord/oauth" className="mt-3 inline-block rounded-lg border border-white/15 px-4 py-2 text-sm hover:border-accent/50">
                Connect Discord →
              </a>
            )}
            {discord === "error" && <p className="mt-2 text-xs text-red-300">Connect failed. retry.</p>}
          </div>
        </section>

        {/* AI usage + research depth */}
        {health && (
          <section className="mb-6 rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <h2 className="mb-3 text-sm font-medium text-white/70">AI &amp; research</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="mb-1 text-xs uppercase text-white/40">Models (efficient tiering)</div>
                <ul className="text-sm text-white/70">
                  {Object.entries((health.models as Record<string, string>) || {}).map(([task, model]) => (
                    <li key={task} className="flex justify-between gap-2">
                      <span className="text-white/50">{task}</span>
                      <span className="font-mono text-xs">{String(model).replace("claude-", "")}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="mb-1 text-xs uppercase text-white/40">Live signal sources</div>
                <div className="flex flex-wrap gap-1.5">
                  {((health.sources as string[]) || []).map((s) => (
                    <span key={s} className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-white/60">{s}</span>
                  ))}
                </div>
                <p className="mt-2 text-xs text-white/40">
                  Browserbase {health.browserbase ? "powers" : "would power"} X/LinkedIn/news scraping.
                  Sources with no key return nothing (never faked).
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Live connector matrix */}
        <section className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
          <h2 className="mb-3 text-sm font-medium text-white/70">Platform connectors (live status)</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {CONNECTORS.map((c) => {
              const ok = live(health, c.key);
              return (
                <div key={c.name} className="flex items-start gap-2 rounded-lg border border-white/10 px-3 py-2">
                  <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${ok ? "bg-accent" : "bg-white/25"}`} />
                  <div>
                    <div className="text-sm">{c.name}</div>
                    <div className="text-xs text-white/45">{ok ? "configured" : c.note}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>
    </>
  );
}

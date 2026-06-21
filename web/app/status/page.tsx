import Nav from "@/components/Nav";
import { AGENT_BASE_URL, agentHeaders } from "@/lib/api";

export const dynamic = "force-dynamic";

type Health = Record<string, unknown> & { status?: string; llm?: string };

const LABELS: Record<string, string> = {
  llm: "Anthropic Claude",
  convex: "Convex",
  redis: "Redis (Upstash)",
  browserbase: "Browserbase",
  gemini: "Gemini (image)",
  daily: "Daily (video)",
  deepgram: "Deepgram (voice)",
  discord: "Discord",
  twilio: "Twilio (SMS/call)",
};

async function getHealth(): Promise<Health | null> {
  try {
    const r = await fetch(`${AGENT_BASE_URL}/health`, {
      headers: agentHeaders(),
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()) as Health;
  } catch {
    return null;
  }
}

export default async function StatusPage() {
  const h = await getHealth();
  const up = !!h && h.status === "ok";

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-6 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">System status</h1>
          <span
            className={
              "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs " +
              (up
                ? "border-accent/30 bg-accent/10 text-accent-soft"
                : "border-red-400/30 bg-red-400/10 text-red-300")
            }
          >
            <span className={"h-1.5 w-1.5 rounded-full " + (up ? "bg-accent animate-pulse" : "bg-red-400")} />
            {up ? "Agent online" : "Agent unreachable"}
          </span>
        </div>

        {!h ? (
          <p className="text-sm text-white/50">
            Can&apos;t reach the agent control plane. Check <code>AGENT_BASE_URL</code> +{" "}
            <code>AGENT_SHARED_TOKEN</code>.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(LABELS).map(([key, label]) => {
              const on = key === "llm" ? h.llm === "claude" : h[key] === true;
              return (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3"
                >
                  <span className="text-sm">{label}</span>
                  <span
                    className={
                      "inline-flex items-center gap-1.5 text-xs " +
                      (on ? "text-accent-soft" : "text-white/35")
                    }
                  >
                    <span className={"h-1.5 w-1.5 rounded-full " + (on ? "bg-accent" : "bg-white/25")} />
                    {on ? "live" : "off"}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {h?.tools != null && Array.isArray(h.tools) && (
          <p className="mt-6 text-xs text-white/40">
            Agent tools: {(h.tools as string[]).join(" · ")}
          </p>
        )}
      </main>
    </>
  );
}

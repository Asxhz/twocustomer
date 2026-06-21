import Nav from "@/components/Nav";
import LiveBadge from "@/components/LiveBadge";
import { listCampaigns } from "@/lib/convexHttp";

export const dynamic = "force-dynamic";

export default async function Campaigns() {
  const { rows, source } = await listCampaigns();
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-1 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Campaigns</h1>
          <LiveBadge source={source} />
        </header>
        <p className="mb-6 text-sm text-white/50">
          Campaign briefs grounded in real signal.
        </p>
        {rows.length === 0 ? (
          <p className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/50">
            No campaigns yet. Run a signal search on a project, then ask the analyst to draft one.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {rows.map((c, i) => (
              <article key={c._id ?? i} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{c.brief}</h3>
                  <span
                    className={
                      c.status === "ready"
                        ? "rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft"
                        : "rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/60"
                    }
                  >
                    {c.status}
                  </span>
                </div>
                {c.body && <p className="mt-1 text-sm text-white/55">{c.body}</p>}
              </article>
            ))}
          </div>
        )}
      </main>
    </>
  );
}

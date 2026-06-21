import Link from "next/link";
import Nav from "@/components/Nav";
import ChatThread from "@/components/ChatThread";
import LiveBadge from "@/components/LiveBadge";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import { analyticsSummary, listInsights } from "@/lib/convexHttp";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs text-white/50">{label}</div>
    </div>
  );
}

interface InsightRow {
  _id?: string;
  id?: string;
  title: string;
  body: string;
  severity?: string;
}

export default async function AdminDashboard() {
  const [{ data, source }, insights] = await Promise.all([
    analyticsSummary(),
    listInsights(),
  ]);
  const t = data?.totals;
  const latest = (insights.rows as unknown as InsightRow[]).slice(0, 2);

  return (
    <>
      <Nav />
      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1fr_360px]">
        <section className="flex flex-col gap-6">
          <header className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Dashboard</h1>
              <p className="text-sm text-white/50">
                Your 24/7 AI analyst. monitoring, surfacing, and acting.
              </p>
            </div>
            <LiveBadge source={source} />
          </header>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Open insights" value={t?.insights ?? 0} />
            <Stat label="Campaigns" value={t?.campaigns ?? 0} />
            <Stat label="Packets" value={t?.packets ?? 0} />
            <Stat label="Mentions" value={t?.mentions ?? 0} />
          </div>

          {data && (data.totals.mentions + data.totals.insights + data.totals.sessions) > 0 ? (
            <AnalyticsCharts data={data} />
          ) : (
            <p className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm text-white/50">
              No analytics yet. Add a project and run a signal search to populate charts.
            </p>
          )}

          <div>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-sm font-medium text-white/70">Latest insights</h2>
              <Link href="/admin/insights" className="text-xs text-accent-soft">
                View all
              </Link>
            </div>
            {latest.length === 0 ? (
              <p className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm text-white/50">
                No insights yet. ask the analyst to monitor your brand.
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {latest.map((it) => (
                  <article key={it._id ?? it.id} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                    <span
                      className={
                        it.severity === "risk"
                          ? "rounded-full bg-red-500/15 px-2 py-0.5 text-xs text-red-300"
                          : "rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft"
                      }
                    >
                      {it.severity ?? "info"}
                    </span>
                    <h3 className="mt-2 font-medium">{it.title}</h3>
                    <p className="mt-1 text-sm text-white/60">{it.body}</p>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-white/70">Ask your analyst</h2>
          <ChatThread />
        </aside>
      </main>
    </>
  );
}

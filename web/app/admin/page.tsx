import Link from "next/link";
import Nav from "@/components/Nav";
import ChatThread from "@/components/ChatThread";
import LiveBadge from "@/components/LiveBadge";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import { Card, Stat, Badge } from "@/components/ui";
import { analyticsSummary, listInsights } from "@/lib/convexHttp";

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
  const latest = (insights.rows as unknown as InsightRow[]).slice(0, 3);
  const hasData =
    data && data.totals.mentions + data.totals.insights + data.totals.sessions > 0;

  return (
    <>
      <Nav />
      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1fr_380px]">
        <section className="flex flex-col gap-6">
          <header className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
              <p className="mt-1 text-sm text-white/55">
                Your always-on AI team. It monitors signal, surfaces insights, and ships fixes.
              </p>
            </div>
            <LiveBadge source={source} />
          </header>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Card className="!p-4"><Stat label="Open insights" value={t?.insights ?? 0} /></Card>
            <Card className="!p-4"><Stat label="Campaigns" value={t?.campaigns ?? 0} /></Card>
            <Card className="!p-4"><Stat label="Packets" value={t?.packets ?? 0} /></Card>
            <Card className="!p-4"><Stat label="Mentions" value={t?.mentions ?? 0} /></Card>
          </div>

          {hasData ? (
            <AnalyticsCharts data={data} />
          ) : (
            <Card>
              <p className="text-sm text-white/55">
                No analytics yet. Connect a project and run a signal search to populate
                your charts.
              </p>
              <Link
                href="/admin/projects"
                className="mt-3 inline-block rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110"
              >
                Add a project
              </Link>
            </Card>
          )}

          <div>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white/70">Latest insights</h2>
              <Link href="/admin/insights" className="text-xs font-medium text-accent hover:underline">
                View all
              </Link>
            </div>
            {latest.length === 0 ? (
              <Card>
                <p className="text-sm text-white/55">
                  No insights yet. Ask your analyst to monitor your brand and the first
                  ones will land here.
                </p>
              </Card>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {latest.map((it) => (
                  <Card key={it._id ?? it.id}>
                    <Badge tone={it.severity === "risk" ? "bad" : it.severity === "opportunity" ? "good" : "accent"}>
                      {it.severity ?? "info"}
                    </Badge>
                    <h3 className="mt-2 font-medium">{it.title}</h3>
                    <p className="mt-1 text-sm text-white/60">{it.body}</p>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="flex flex-col gap-3">
          <div>
            <h2 className="text-sm font-semibold text-white/70">Ask your team</h2>
            <p className="text-xs text-white/45">
              Monitor a brand, build a campaign, or fix the site. It confirms before it ships.
            </p>
          </div>
          <ChatThread />
        </aside>
      </main>
    </>
  );
}

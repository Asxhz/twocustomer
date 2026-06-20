import Nav from "@/components/Nav";
import { listCampaigns } from "@/lib/convexHttp";

export const dynamic = "force-dynamic";

export default async function Campaigns() {
  const { rows, live } = await listCampaigns();
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-1 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Campaigns</h1>
          <span
            className={
              "rounded-full px-2 py-0.5 text-xs " +
              (live ? "bg-emerald-500/15 text-emerald-300" : "bg-white/10 text-white/50")
            }
          >
            {live ? "● live" : "○ demo"}
          </span>
        </header>
        <p className="mb-6 text-sm text-white/50">
          Multi-agent campaign briefs — competitor intel, hooks, creator outreach.
        </p>
        <div className="flex flex-col gap-3">
          {rows.map((c, i) => (
            <article key={i} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <div>
                <h3 className="font-medium">
                  {("name" in c && c.name) || c.brief}
                </h3>
                <p className="text-sm text-white/55">{c.brief}</p>
              </div>
              <span
                className={
                  c.status === "ready"
                    ? "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300"
                    : "rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/60"
                }
              >
                {c.status}
              </span>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}

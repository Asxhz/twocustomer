import Nav from "@/components/Nav";
import { listInsights } from "@/lib/convexHttp";

export const dynamic = "force-dynamic";

function Badge({ live }: { live: boolean }) {
  return (
    <span
      className={
        "rounded-full px-2 py-0.5 text-xs " +
        (live ? "bg-emerald-500/15 text-emerald-300" : "bg-white/10 text-white/50")
      }
    >
      {live ? "● live" : "○ demo"}
    </span>
  );
}

export default async function Insights() {
  const { rows, live } = await listInsights();
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-1 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Insights</h1>
          <Badge live={live} />
        </header>
        <p className="mb-6 text-sm text-white/50">
          Revenue opportunities, cost leaks, trends, and anomalies — found 24/7.
        </p>
        <div className="flex flex-col gap-3">
          {rows.map((it, i) => (
            <article key={i} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <div className="flex items-center gap-2">
                <span
                  className={
                    it.severity === "risk"
                      ? "rounded-full bg-red-500/15 px-2 py-0.5 text-xs text-red-300"
                      : "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300"
                  }
                >
                  {it.severity ?? "info"}
                </span>
                <h3 className="font-medium">{it.title}</h3>
              </div>
              <p className="mt-2 text-sm text-white/60">{it.body}</p>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}

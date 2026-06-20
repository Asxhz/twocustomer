import ChatThread from "@/components/ChatThread";

// Mock data until Convex live queries land (P3/P7).
const INSIGHTS = [
  {
    title: "Stockouts costing ~10% of revenue",
    body: "Aurora Drinks sold out at 3 retail accounts for the 3rd straight week. Recommend reorder + allocation fix.",
    severity: "risk",
  },
  {
    title: "Yuzu is the breakout SKU",
    body: "Web + Reddit chatter points to yuzu outperforming. Lean campaign spend here.",
    severity: "opportunity",
  },
];

export default function Dashboard() {
  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-6 py-10 lg:grid-cols-[1fr_380px]">
      <section className="flex flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold">Aurora Drinks</h1>
          <p className="text-sm text-white/50">Your 24/7 AI analyst — live.</p>
        </header>
        <div className="grid gap-4 sm:grid-cols-2">
          {INSIGHTS.map((it) => (
            <article
              key={it.title}
              className="rounded-xl border border-white/10 bg-white/[0.02] p-4"
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={
                    it.severity === "risk"
                      ? "rounded-full bg-red-500/15 px-2 py-0.5 text-xs text-red-300"
                      : "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300"
                  }
                >
                  {it.severity}
                </span>
              </div>
              <h3 className="font-medium">{it.title}</h3>
              <p className="mt-1 text-sm text-white/60">{it.body}</p>
            </article>
          ))}
        </div>
      </section>
      <aside className="flex flex-col gap-3">
        <h2 className="text-sm font-medium text-white/70">Ask your analyst</h2>
        <ChatThread />
      </aside>
    </main>
  );
}

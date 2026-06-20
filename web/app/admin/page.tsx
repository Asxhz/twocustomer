import Link from "next/link";
import Nav from "@/components/Nav";
import ChatThread from "@/components/ChatThread";
import { BRAND, INSIGHTS, CAMPAIGNS, PACKETS } from "@/lib/mock";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs text-white/50">{label}</div>
    </div>
  );
}

export default function AdminDashboard() {
  return (
    <>
      <Nav />
      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[1fr_360px]">
        <section className="flex flex-col gap-6">
          <header>
            <h1 className="text-2xl font-semibold">{BRAND.name}</h1>
            <p className="text-sm text-white/50">
              Your 24/7 AI analyst — monitoring, surfacing, and acting.
            </p>
          </header>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Open insights" value={String(INSIGHTS.length)} />
            <Stat label="Campaigns" value={String(CAMPAIGNS.length)} />
            <Stat label="Packets" value={String(PACKETS.length)} />
            <Stat label="Monitors live" value="4" />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-sm font-medium text-white/70">Latest insights</h2>
              <Link href="/admin/insights" className="text-xs text-emerald-400">
                View all
              </Link>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {INSIGHTS.slice(0, 2).map((it) => (
                <article key={it.id} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <span
                    className={
                      it.severity === "risk"
                        ? "rounded-full bg-red-500/15 px-2 py-0.5 text-xs text-red-300"
                        : "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300"
                    }
                  >
                    {it.severity}
                  </span>
                  <h3 className="mt-2 font-medium">{it.title}</h3>
                  <p className="mt-1 text-sm text-white/60">{it.body}</p>
                </article>
              ))}
            </div>
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

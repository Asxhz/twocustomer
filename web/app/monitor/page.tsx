import Nav from "@/components/Nav";
import AutoRefresh from "@/components/AutoRefresh";
import { listMentions } from "@/lib/convexHttp";

export const dynamic = "force-dynamic";

export default async function Monitor() {
  const { rows, live } = await listMentions();
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Live monitor</h1>
            <p className="text-sm text-white/50">
              Agents watching news · Reddit · web — scored for risk + opportunity.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <AutoRefresh seconds={12} />
            <span
              className={
                "rounded-full px-2 py-0.5 text-xs " +
                (live
                  ? "bg-emerald-500/15 text-emerald-300"
                  : "bg-white/10 text-white/50")
              }
            >
              {live ? "● live (Convex)" : "○ demo data"}
            </span>
          </div>
        </header>
        <ul className="flex flex-col gap-3">
          {rows.map((m, i) => (
            <li
              key={i}
              className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4"
            >
              <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs uppercase">
                {m.platform}
              </span>
              <div className="flex-1">
                <p className="text-sm">{m.text}</p>
                <p className="mt-1 text-xs text-white/40">{m.author}</p>
              </div>
              {m.highSignal && (
                <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-xs text-amber-200">
                  high signal
                </span>
              )}
            </li>
          ))}
        </ul>
      </main>
    </>
  );
}

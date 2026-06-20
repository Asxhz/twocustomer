import Nav from "@/components/Nav";
import { INTEGRATIONS } from "@/lib/mock";

export default function Integrations() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="mb-1 text-2xl font-semibold">Integrations</h1>
        <p className="mb-6 text-sm text-white/50">
          The platforms powering TwoCustomer — and the hackathon tracks they map to.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {INTEGRATIONS.map((it) => (
            <article key={it.name} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{it.name}</h3>
                <span className="h-2 w-2 rounded-full bg-emerald-400" title="wired" />
              </div>
              <p className="mt-1 text-sm text-white/60">{it.role}</p>
              {it.track !== "—" && (
                <p className="mt-2 text-xs text-amber-300/80">🏆 {it.track}</p>
              )}
            </article>
          ))}
        </div>
      </main>
    </>
  );
}

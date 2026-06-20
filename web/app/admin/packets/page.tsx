import Link from "next/link";
import Nav from "@/components/Nav";
import { listPackets } from "@/lib/convexHttp";

export const dynamic = "force-dynamic";

export default async function Packets() {
  const { rows, live } = await listPackets();
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-1 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Founder / CMO packets</h1>
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
          Insight → evidence → recommended action → shippable PR/ticket.
        </p>
        <div className="flex flex-col gap-3">
          {rows.map((p, i) => {
            const id = ("id" in p && p.id) || ("_id" in p && (p as { _id: string })._id) || String(i);
            return (
              <Link
                key={i}
                href={`/founder-packets/${id}`}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:border-emerald-400/40"
              >
                <h3 className="font-medium">{p.title}</h3>
                <p className="mt-1 text-sm text-white/60">{p.summary}</p>
                <span className="mt-2 inline-block text-xs text-emerald-400">Open packet →</span>
              </Link>
            );
          })}
        </div>
      </main>
    </>
  );
}

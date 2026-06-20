import Link from "next/link";
import Nav from "@/components/Nav";
import { PACKETS } from "@/lib/mock";

export default async function FounderPacket({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const packet = PACKETS.find((p) => p.id === id) ?? PACKETS[0];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-8">
        <Link href="/admin/packets" className="text-xs text-white/50 hover:text-white">
          ← Packets
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">{packet.title}</h1>
        <p className="mt-1 text-white/60">{packet.summary}</p>

        <section className="mt-6">
          <h2 className="text-sm font-medium text-white/70">Evidence</h2>
          <ul className="mt-2 flex flex-col gap-2">
            {packet.evidence.map((e, i) => (
              <li key={i} className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-white/70">
                {e}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-6 rounded-xl border border-emerald-400/30 bg-emerald-400/[0.04] p-4">
          <h2 className="text-sm font-medium text-emerald-300">Recommended action</h2>
          <p className="mt-1 text-sm text-white/80">{packet.recommendedAction}</p>
        </section>

        <section className="mt-6">
          <h2 className="text-sm font-medium text-white/70">Shippable artifact</h2>
          <pre className="mt-2 overflow-x-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs text-amber-200">
            {packet.artifact}
          </pre>
        </section>
      </main>
    </>
  );
}

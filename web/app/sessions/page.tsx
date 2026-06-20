import Link from "next/link";
import Nav from "@/components/Nav";
import { SESSIONS } from "@/lib/mock";

export default function Sessions() {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="mb-1 text-2xl font-semibold">Customer sessions</h1>
        <p className="mb-6 text-sm text-white/50">
          Voice + chat interviews with the brand&apos;s customers → validated insight.
        </p>
        <div className="flex flex-col gap-3">
          {SESSIONS.map((s) => (
            <Link
              key={s.id}
              href={`/sessions/${s.id}`}
              className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:border-emerald-400/40"
            >
              <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs uppercase">{s.channel}</span>
              <div className="flex-1">
                <h3 className="text-sm font-medium">{s.customer}</h3>
                <p className="text-sm text-white/55">{s.insight}</p>
              </div>
              <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">{s.status}</span>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}

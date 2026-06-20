import Link from "next/link";
import Nav from "@/components/Nav";
import { SESSIONS } from "@/lib/mock";

export default async function SessionDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = SESSIONS.find((s) => s.id === id) ?? SESSIONS[0];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-2xl px-6 py-8">
        <Link href="/sessions" className="text-xs text-white/50 hover:text-white">
          ← Sessions
        </Link>
        <div className="mt-2 flex items-center gap-2">
          <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs uppercase">
            {session.channel}
          </span>
          <h1 className="text-xl font-semibold">{session.customer}</h1>
        </div>

        <section className="mt-5 flex flex-col gap-2">
          {session.transcript.map((t, i) => (
            <div
              key={i}
              className={
                t.role === "agent"
                  ? "self-start max-w-[85%] rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100"
                  : "self-end max-w-[85%] rounded-2xl bg-white/10 px-4 py-2 text-sm"
              }
            >
              {t.text}
            </div>
          ))}
        </section>

        <section className="mt-6 rounded-xl border border-emerald-400/30 bg-emerald-400/[0.04] p-4">
          <h2 className="text-sm font-medium text-emerald-300">Validated insight</h2>
          <p className="mt-1 text-sm text-white/80">{session.insight}</p>
        </section>
      </main>
    </>
  );
}

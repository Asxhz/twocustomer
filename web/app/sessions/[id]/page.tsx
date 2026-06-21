import Link from "next/link";
import Nav from "@/components/Nav";
import { getSessionById } from "@/lib/convexHttp";

interface SessionDoc {
  customer: string;
  channel: string;
  status: string;
  transcript: { role: string; text: string }[];
}

export default async function SessionDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = (await getSessionById(id)) as SessionDoc | null;

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-2xl px-6 py-8">
          <Link href="/sessions" className="text-xs text-white/50 hover:text-white">
            ← Sessions
          </Link>
          <p className="mt-6 rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/50">
            Session not found, or data is unavailable.
          </p>
        </main>
      </>
    );
  }

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
          <span className="rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft">
            {session.status}
          </span>
        </div>

        <section className="mt-5 flex flex-col gap-2">
          {session.transcript.map((t, i) => (
            <div
              key={i}
              className={
                t.role === "agent"
                  ? "self-start max-w-[85%] rounded-2xl bg-accent/10 px-4 py-2 text-sm text-accent-soft"
                  : "self-end max-w-[85%] rounded-2xl bg-white/10 px-4 py-2 text-sm"
              }
            >
              {t.text}
            </div>
          ))}
        </section>
      </main>
    </>
  );
}

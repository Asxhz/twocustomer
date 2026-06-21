import Link from "next/link";
import Nav from "@/components/Nav";
import LiveBadge from "@/components/LiveBadge";
import { listSessions } from "@/lib/convexHttp";

interface SessionRow {
  _id?: string;
  id?: string;
  customer: string;
  channel: string;
  status: string;
  transcript?: { role: string; text: string }[];
}

export default async function Sessions() {
  const { rows, source } = await listSessions();
  const sessions = rows as unknown as SessionRow[];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-1 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Customer sessions</h1>
          <LiveBadge source={source} />
        </div>
        <p className="mb-6 text-sm text-white/50">
          Voice + chat interviews with the brand&apos;s customers → validated insight.
        </p>
        {sessions.length === 0 ? (
          <p className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-sm text-white/50">
            No interviews yet. Start one from the dashboard chat or invite a customer.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {sessions.map((s) => {
              const id = s._id ?? s.id ?? "";
              const last = s.transcript?.[s.transcript.length - 1]?.text ?? "";
              return (
                <Link
                  key={id}
                  href={`/sessions/${id}`}
                  className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:border-accent/40"
                >
                  <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs uppercase">{s.channel}</span>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium">{s.customer}</h3>
                    <p className="line-clamp-1 text-sm text-white/55">{last}</p>
                  </div>
                  <span className="rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft">{s.status}</span>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </>
  );
}

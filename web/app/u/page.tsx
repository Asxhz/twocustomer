import Link from "next/link";
import { activeBrandName } from "@/lib/convexHttp";

// Customer-facing surface. The brand's customers land here from an invite.
export default async function CustomerHome() {
  const brand = await activeBrandName();
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-6 px-6 text-center">
      <span className="rounded-full border border-white/15 px-3 py-1 text-xs font-medium uppercase tracking-widest text-white/50">
        {brand} × TwoCustomer
      </span>
      <h1 className="text-balance text-4xl font-semibold tracking-tight">
        Help shape what we build next.
      </h1>
      <p className="max-w-md text-white/60">
        Give us three minutes. Talk to our AI by voice or chat about what you love,
        what bugs you, and what you wish existed. Your answers go straight to the
        team as real product work.
      </p>
      <div className="flex gap-3">
        <Link
          href="/u/session"
          className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white shadow-[0_1px_2px_rgba(0,0,0,0.08)] hover:brightness-110"
        >
          Start by voice
        </Link>
        <Link
          href="/u/session?mode=chat"
          className="rounded-lg border border-white/15 px-5 py-2.5 text-sm font-medium hover:bg-white/[0.04]"
        >
          Prefer to type
        </Link>
      </div>
      <p className="text-xs text-white/40">Earn rewards for completed interviews.</p>
    </main>
  );
}

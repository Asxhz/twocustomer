import Link from "next/link";
import { REWARDS } from "@/lib/mock";

export default function Rewards() {
  const total = REWARDS.filter((r) => r.status === "earned").reduce((a, r) => a + r.points, 0);
  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <Link href="/u" className="text-xs text-white/50 hover:text-white">
        ← Back
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Your rewards</h1>
      <p className="mt-1 text-sm text-white/50">
        Thanks for helping shape Aurora Drinks.
      </p>
      <div className="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/[0.04] p-5">
        <div className="text-3xl font-semibold text-emerald-300">{total} pts</div>
        <div className="text-xs text-white/50">earned</div>
      </div>
      <ul className="mt-5 flex flex-col gap-2">
        {REWARDS.map((r) => (
          <li key={r.id} className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3">
            <span className="text-sm">{r.label}</span>
            <span className="flex items-center gap-2">
              <span className="text-sm text-white/60">{r.points} pts</span>
              <span
                className={
                  r.status === "earned"
                    ? "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300"
                    : r.status === "redeemable"
                      ? "rounded-full bg-amber-400/15 px-2 py-0.5 text-xs text-amber-200"
                      : "rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/50"
                }
              >
                {r.status}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </main>
  );
}

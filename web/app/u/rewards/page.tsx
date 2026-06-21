import Link from "next/link";
import LiveBadge from "@/components/LiveBadge";
import { getSession } from "@/lib/session";
import { listRewardsByCustomer } from "@/lib/convexHttp";

interface RewardRow {
  _id?: string;
  id?: string;
  label: string;
  points: number;
  status: string;
}

export default async function Rewards() {
  const sess = await getSession();
  // Customers see their own ledger; an admin previewing /u sees a seeded customer.
  const customer =
    sess && sess.role === "customer" ? sess.email : "rosie@wholesale.co";
  const { rows, source } = await listRewardsByCustomer(customer);
  const rewards = rows as unknown as RewardRow[];
  const total = rewards
    .filter((r) => r.status === "earned")
    .reduce((a, r) => a + r.points, 0);

  return (
    <main className="mx-auto max-w-md px-6 py-12">
      <Link href="/u" className="text-xs text-white/50 hover:text-white">
        ← Back
      </Link>
      <div className="mt-2 flex items-center gap-2">
        <h1 className="text-2xl font-semibold">Your rewards</h1>
        <LiveBadge source={source} />
      </div>
      <p className="mt-1 text-sm text-white/50">Thanks for helping shape the product.</p>
      <div className="mt-4 rounded-xl border border-accent/30 bg-accent/[0.04] p-5">
        <div className="text-3xl font-semibold text-accent-soft">{total} pts</div>
        <div className="text-xs text-white/50">earned</div>
      </div>
      {rewards.length === 0 ? (
        <p className="mt-5 rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3 text-sm text-white/50">
          No rewards yet. complete an interview to earn your first points.
        </p>
      ) : (
        <ul className="mt-5 flex flex-col gap-2">
          {rewards.map((r) => (
            <li
              key={r._id ?? r.id}
              className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3"
            >
              <span className="text-sm">{r.label}</span>
              <span className="flex items-center gap-2">
                <span className="text-sm text-white/60">{r.points} pts</span>
                <span
                  className={
                    r.status === "earned"
                      ? "rounded-full bg-accent/15 px-2 py-0.5 text-xs text-accent-soft"
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
      )}
    </main>
  );
}

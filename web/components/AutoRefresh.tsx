"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

// Re-runs the server component's data fetch on an interval so dynamic pages
// (the live monitor feed) update without a manual reload.
export default function AutoRefresh({ seconds = 12 }: { seconds?: number }) {
  const router = useRouter();
  const [on, setOn] = useState(true);

  useEffect(() => {
    if (!on) return;
    const id = setInterval(() => router.refresh(), seconds * 1000);
    return () => clearInterval(id);
  }, [router, seconds, on]);

  return (
    <button
      onClick={() => setOn((v) => !v)}
      className="inline-flex items-center gap-1.5 text-xs text-white/45 hover:text-white/70"
      title={on ? "Live updates on. click to pause" : "Paused. click to resume"}
    >
      <span className={"h-1.5 w-1.5 rounded-full " + (on ? "bg-accent animate-pulse" : "bg-white/30")} />
      {on ? "Live" : "Paused"}
    </button>
  );
}

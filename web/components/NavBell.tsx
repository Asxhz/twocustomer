"use client";

import { useEffect, useState, useCallback } from "react";

interface Notif {
  _id: string;
  kind: string;
  title: string;
  body?: string;
  href?: string;
  read: boolean;
  ts: number;
}

const ICON: Record<string, string> = {
  alert: "🚨",
  insight: "💡",
  campaign: "📣",
  fix: "🔧",
  interview: "🎙",
};

export default function NavBell() {
  const [items, setItems] = useState<Notif[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/notifications", { cache: "no-store" });
      if (!r.ok) return;
      const d = await r.json();
      setItems(d.notifications ?? []);
      setUnread(d.unread ?? 0);
    } catch {
      /* offline. leave as is */
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 20_000);
    return () => clearInterval(t);
  }, [load]);

  async function markAll() {
    await fetch("/api/notifications", { method: "POST", body: "{}" });
    setUnread(0);
    setItems((xs) => xs.map((x) => ({ ...x, read: true })));
  }

  return (
    <div className="relative">
      <button
        onClick={() => {
          setOpen((o) => !o);
          if (!open && unread) markAll();
        }}
        className="relative rounded-md border border-white/15 px-2 py-1 text-xs text-white/70 hover:text-white"
        aria-label="Notifications"
      >
        🔔
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-semibold text-white">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-9 z-30 w-80 rounded-xl border border-white/10 bg-black/90 p-2 backdrop-blur">
          <div className="px-2 py-1 text-xs font-medium text-white/50">Notifications</div>
          {items.length === 0 ? (
            <p className="px-2 py-4 text-center text-xs text-white/40">Nothing yet.</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto">
              {items.map((n) => (
                <li key={n._id}>
                  <a
                    href={n.href ?? "#"}
                    className={`flex gap-2 rounded-lg px-2 py-2 text-sm hover:bg-white/5 ${n.read ? "opacity-60" : ""}`}
                  >
                    <span>{ICON[n.kind] ?? "•"}</span>
                    <span className="flex-1">
                      <span className="block font-medium text-white/90">{n.title}</span>
                      {n.body && <span className="block text-xs text-white/50">{n.body}</span>}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

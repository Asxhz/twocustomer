"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const TOOLS = [
  { href: "/admin/fix", label: "Fix (FDE)" },
  { href: "/admin/studio", label: "Studio" },
  { href: "/monitor", label: "Monitor" },
  { href: "/admin/graph", label: "Signal graph" },
  { href: "/sessions", label: "Sessions" },
  { href: "/integrations", label: "Integrations" },
  { href: "/status", label: "Status" },
];

export default function NavTools() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 hover:text-white"
      >
        Tools <span className="text-[10px]">▾</span>
      </button>
      {open && (
        <div className="absolute left-0 top-7 z-30 w-44 rounded-xl border border-white/10 bg-black/90 p-1 backdrop-blur">
          {TOOLS.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              onClick={() => setOpen(false)}
              className="block rounded-lg px-3 py-2 text-sm text-white/70 hover:bg-white/5 hover:text-white"
            >
              {t.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";

export default function CompanyNameForm({ initial }: { initial: string }) {
  const [name, setName] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    setBusy(true);
    setSaved(false);
    try {
      await fetch("/api/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-end gap-2">
      <div className="flex-1">
        <label className="text-xs text-white/50">Company name</label>
        <input
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setSaved(false);
          }}
          className="mt-1 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-accent/60"
        />
      </div>
      <button
        onClick={save}
        disabled={busy || !name.trim()}
        className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
      >
        {busy ? "Saving…" : saved ? "Saved ✓" : "Save"}
      </button>
    </div>
  );
}

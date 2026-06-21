"use client";

import { useState } from "react";

// "Add GitHub as a dev". paste a Personal Access Token (repo scope). No OAuth
// app needed. Stored encrypted; the FDE opens PRs with it.
export default function GithubTokenForm({ connected, primary = false }: { connected: boolean; primary?: boolean }) {
  const [open, setOpen] = useState(primary);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function save() {
    setBusy(true);
    setMsg("");
    try {
      const r = await fetch("/api/github/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      const d = await r.json();
      if (d.ok) {
        setMsg(`Connected as @${d.login}`);
        setToken("");
        setTimeout(() => location.reload(), 800);
      } else {
        setMsg(d.error || "Failed.");
      }
    } catch {
      setMsg("Failed. try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-2">
      {primary ? (
        <p className="text-sm font-medium text-white/80">Connect GitHub (paste a token)</p>
      ) : (
        <button
          onClick={() => setOpen((o) => !o)}
          className="text-xs text-white/50 underline hover:text-white/80"
        >
          {connected ? "Replace with a token" : "or paste a token (no OAuth app)"}
        </button>
      )}
      {open && (
        <div className="mt-2 flex flex-col gap-2">
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="ghp_… (Personal Access Token, repo scope)"
            className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-accent/60"
          />
          <button
            onClick={save}
            disabled={busy || !token.trim()}
            className="self-start rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
          >
            {busy ? "Saving…" : "Save token"}
          </button>
          {msg && <p className="text-xs text-white/60">{msg}</p>}
          <p className="text-xs text-white/35">
            Create one at github.com/settings/tokens (classic, scope: repo).
          </p>
        </div>
      )}
    </div>
  );
}

"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";

function AuthForm() {
  const params = useSearchParams();
  const next = params.get("next") || "/admin";
  const invite = params.get("invite") || "";
  const brand = params.get("brand") || "";
  const [mode, setMode] = useState<"signup" | "login">(invite ? "signup" : "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) {
        setErr(d.error || "Something went wrong.");
        setBusy(false);
        return;
      }
      window.location.assign(next);
    } catch {
      setErr("Network error. Try again.");
      setBusy(false);
    }
  }

  async function guest() {
    setBusy(true);
    setErr("");
    try {
      const r = await fetch("/api/auth/guest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand, invite }),
      });
      if (!r.ok) throw new Error();
      window.location.assign("/u");
    } catch {
      setErr("Could not continue as guest.");
      setBusy(false);
    }
  }

  const input =
    "mt-3 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-accent/60";

  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-6">
      <form onSubmit={submit} className="w-full max-w-sm rounded-2xl border border-white/10 bg-white/[0.02] p-7">
        <h1 className="text-xl font-semibold">
          Two<span className="text-accent-soft">Customer</span>
        </h1>
        <p className="mt-1 text-sm text-white/50">
          {mode === "signup" ? "Create your account." : "Log in to your workspace."}
        </p>
        <input autoFocus type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@brand.com" className={input} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password (8+ characters)" className={input} />
        <button type="submit" disabled={busy} className="mt-3 w-full rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50">
          {busy ? "Working" : mode === "signup" ? "Create account" : "Log in"}
        </button>
        {err && <p className="mt-2 text-center text-xs text-red-400">{err}</p>}
        <button type="button" onClick={() => { setMode(mode === "signup" ? "login" : "signup"); setErr(""); }} className="mt-3 w-full text-center text-xs text-white/50 hover:text-white">
          {mode === "signup" ? "Have an account? Log in" : "New here? Create an account"}
        </button>
        {(invite || brand) && (
          <button type="button" onClick={guest} disabled={busy} className="mt-2 w-full rounded-lg border border-white/15 px-4 py-2 text-xs text-white/70 hover:text-white">
            Continue as guest
          </button>
        )}
      </form>
    </main>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <AuthForm />
    </Suspense>
  );
}

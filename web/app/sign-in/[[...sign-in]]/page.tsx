"use client";

import { Suspense, useRef, useState } from "react";
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
  const emailRef = useRef<HTMLInputElement>(null);

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
        setErr(d.error || "Something went wrong. Try again.");
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
      window.location.assign(invite ? "/u/session" : "/u");
    } catch {
      setErr("Could not continue as guest.");
      setBusy(false);
    }
  }

  const field =
    "w-full rounded-lg border border-white/15 bg-surface px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-accent focus:ring-2 focus:ring-accent/20";

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="tc-fade-up w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-lg font-semibold tracking-tight">TwoCustomer</div>
          <p className="mt-2 text-sm text-white/55">
            Growth, on autopilot. We watch your signal, talk to your customers, and
            ship the fixes.
          </p>
        </div>

        <form
          onSubmit={submit}
          className="rounded-2xl border border-white/10 bg-surface p-6 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_8px_30px_-18px_rgba(0,0,0,0.25)]"
        >
          <h1 className="text-base font-semibold">
            {mode === "signup" ? "Create your account" : "Log in"}
          </h1>
          <p className="mt-1 text-sm text-white/55">
            {mode === "signup"
              ? "Set up your workspace in under a minute."
              : "Welcome back."}
          </p>

          <div className="mt-5 flex flex-col gap-3">
            <input
              ref={emailRef}
              autoFocus
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className={field}
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className={field}
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="mt-4 w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-50"
          >
            {busy ? "Working" : mode === "signup" ? "Create account" : "Log in"}
          </button>

          {err && <p className="mt-3 text-center text-xs text-red-500">{err}</p>}

          <button
            type="button"
            onClick={() => {
              setMode(mode === "signup" ? "login" : "signup");
              setErr("");
            }}
            className="mt-4 w-full text-center text-xs text-white/55 transition hover:text-white"
          >
            {mode === "signup" ? "Have an account? Log in" : "New here? Create an account"}
          </button>

          {(invite || brand) && (
            <button
              type="button"
              onClick={guest}
              disabled={busy}
              className="mt-2 w-full rounded-lg border border-white/15 px-4 py-2 text-xs text-white/70 transition hover:bg-white/[0.04] hover:text-white"
            >
              Continue as guest
            </button>
          )}
        </form>
      </div>
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

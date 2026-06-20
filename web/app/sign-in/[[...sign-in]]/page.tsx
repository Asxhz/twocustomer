"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";

function SignInForm() {
  const params = useSearchParams();
  const next = params.get("next") || "/admin";
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      const r = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() || "founder@twocustomer.app" }),
      });
      if (!r.ok) throw new Error("Sign-in failed");
      // Hard navigation so the browser sends the freshly-set cookie on the next
      // request — avoids a client-router race where the gate redirects back.
      window.location.assign(next);
    } catch {
      setErr("Sign-in failed — try again.");
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-6">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-2xl border border-white/10 bg-white/[0.02] p-7"
      >
        <h1 className="text-xl font-semibold">
          Two<span className="text-accent-soft">Customer</span>
        </h1>
        <p className="mt-1 text-sm text-white/50">Sign in to the brand console.</p>
        <input
          autoFocus
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@brand.com"
          className="mt-5 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
        />
        <button
          type="submit"
          disabled={busy}
          className="mt-3 w-full rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Continue"}
        </button>
        {err && <p className="mt-2 text-center text-xs text-red-400">{err}</p>}
        <p className="mt-3 text-center text-xs text-white/30">
          We&apos;ll set up your brand workspace on first sign-in.
        </p>
      </form>
    </main>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInForm />
    </Suspense>
  );
}

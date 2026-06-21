"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import ThemeToggle from "@/components/ThemeToggle";

const TAGLINES = [
  "Growth at the pace of your customers.",
  "Less friction. More shipped.",
  "Your forward-deployed engineer. And your CMO.",
  "Monitors your signal 24/7 — then fixes what's broken.",
];

// Types a phrase out, holds, backspaces, then moves to the next — forever.
function Typewriter() {
  const [text, setText] = useState("");
  const [idx, setIdx] = useState(0);
  const [phase, setPhase] = useState<"typing" | "holding" | "deleting">("typing");

  useEffect(() => {
    const full = TAGLINES[idx];
    let t: ReturnType<typeof setTimeout>;
    if (phase === "typing") {
      if (text.length < full.length) {
        t = setTimeout(() => setText(full.slice(0, text.length + 1)), 45);
      } else {
        t = setTimeout(() => setPhase("holding"), 1700);
      }
    } else if (phase === "holding") {
      t = setTimeout(() => setPhase("deleting"), 400);
    } else {
      if (text.length > 0) {
        t = setTimeout(() => setText(full.slice(0, text.length - 1)), 28);
      } else {
        setIdx((i) => (i + 1) % TAGLINES.length);
        setPhase("typing");
      }
    }
    return () => clearTimeout(t);
  }, [text, phase, idx]);

  return (
    <p className="h-6 text-sm text-white/55 sm:text-base">
      {text}
      <span className="tc-caret ml-0.5 inline-block w-px align-middle text-accent-soft">
        |
      </span>
    </p>
  );
}

// The two-people "soft rounded duo" mark, in the accent gradient.
function DuoLogo() {
  return (
    <svg
      width="160"
      height="160"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="relative drop-shadow-[0_12px_40px_rgba(63,114,239,0.45)]"
      aria-hidden
    >
      <defs>
        <linearGradient id="duo" x1="8" y1="6" x2="58" y2="60" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8ab0ff" />
          <stop offset="1" stopColor="#3f72ef" />
        </linearGradient>
      </defs>
      <circle cx="22" cy="23" r="8.5" fill="url(#duo)" opacity="0.5" />
      <path d="M7 50c0-8.5 6.7-14 15-14s15 5.5 15 14v3H7z" fill="url(#duo)" opacity="0.5" />
      <circle cx="42" cy="26" r="10" fill="url(#duo)" />
      <path d="M24 55c0-9.5 8-15.5 18-15.5S60 45.5 60 55v3H24z" fill="url(#duo)" />
    </svg>
  );
}

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
      // Invited from a report -> go straight into the voice interview.
      window.location.assign(invite ? "/u/session" : "/u");
    } catch {
      setErr("Could not continue as guest.");
      setBusy(false);
    }
  }

  // The floating CTA puts us in sign-up mode and drops focus into the form.
  function startSignup() {
    setMode("signup");
    setErr("");
    emailRef.current?.focus();
    emailRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  const input =
    "mt-3 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none transition focus:border-accent-soft/60 focus:ring-1 focus:ring-accent-soft/30";

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="absolute right-5 top-5">
        <ThemeToggle />
      </div>

      {/* Hero */}
      <div className="tc-fade-up flex flex-col items-center text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          Two<span className="text-accent-soft">Customer</span>
        </h1>
        <div className="mt-3 min-h-6">
          <Typewriter />
        </div>

        {/* Floating CTA above the logo */}
        <div className="relative mt-10 flex flex-col items-center">
          <button
            type="button"
            onClick={startSignup}
            className="tc-float relative z-10 rounded-full bg-accent px-6 py-2.5 text-sm font-semibold text-white shadow-[0_14px_40px_-10px_rgba(63,114,239,0.85)] hover:brightness-110"
          >
            Get started — it&apos;s free
          </button>
          {/* soft glow behind the logo */}
          <div className="pointer-events-none absolute left-1/2 top-16 -z-0 h-40 w-40 -translate-x-1/2 rounded-full bg-accent/25 blur-3xl tc-glow" />
          <div className="tc-float -mt-4">
            <DuoLogo />
          </div>
        </div>
      </div>

      {/* Auth card */}
      <form
        onSubmit={submit}
        className="tc-fade-up mt-8 w-full max-w-sm rounded-2xl border border-white/10 bg-white/[0.025] p-7 shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset,0_24px_60px_-30px_rgba(0,0,0,0.7)] backdrop-blur"
        style={{ animationDelay: "120ms" }}
      >
        <p className="text-sm text-white/55">
          {mode === "signup" ? "Create your account." : "Log in to your workspace."}
        </p>
        <input
          ref={emailRef}
          autoFocus
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@brand.com"
          className={input}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password (8+ characters)"
          className={input}
        />
        <button
          type="submit"
          disabled={busy}
          className="mt-3 w-full rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Working…" : mode === "signup" ? "Create account" : "Log in"}
        </button>
        {err && <p className="mt-2 text-center text-xs text-red-400">{err}</p>}
        <button
          type="button"
          onClick={() => {
            setMode(mode === "signup" ? "login" : "signup");
            setErr("");
          }}
          className="mt-3 w-full text-center text-xs text-white/55 hover:text-white"
        >
          {mode === "signup" ? "Have an account? Log in" : "New here? Create an account"}
        </button>
        {(invite || brand) && (
          <button
            type="button"
            onClick={guest}
            disabled={busy}
            className="mt-2 w-full rounded-lg border border-white/15 px-4 py-2 text-xs text-white/70 hover:border-accent/40 hover:text-white"
          >
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

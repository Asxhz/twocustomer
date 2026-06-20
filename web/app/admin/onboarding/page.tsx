"use client";

import { useState } from "react";
import Link from "next/link";
import Nav from "@/components/Nav";

const STEPS = ["Brand", "Web terms", "Social handles", "Connect Discord", "GitHub repo"] as const;

// Discord bot-invite (real OAuth2) — needs a public client id to be live.
const DISCORD_CLIENT_ID = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID || "";
const DISCORD_INVITE = DISCORD_CLIENT_ID
  ? `https://discord.com/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&scope=bot+applications.commands&permissions=274877975552`
  : "";

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [brand, setBrand] = useState("");
  const [terms, setTerms] = useState("");
  const [handles, setHandles] = useState("");
  const [repo, setRepo] = useState("");
  const [armed, setArmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [slug, setSlug] = useState("");

  const last = step === STEPS.length - 1;

  async function next() {
    if (!last) {
      setStep((s) => s + 1);
      return;
    }
    setSaving(true);
    setErr("");
    try {
      const r = await fetch("/api/monitor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand, terms, handles }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Failed to arm monitors");
      setSlug(data.slug || "");
      // Remember the repo so the Fix page prefills it (connects onboarding → FDE).
      if (repo.trim()) {
        try { window.localStorage.setItem("tc_repo", repo.trim()); } catch {}
      }
      setArmed(true);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (armed) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-lg px-6 py-16 text-center">
          <div className="text-4xl">✅</div>
          <h1 className="mt-3 text-2xl font-semibold">Monitors armed</h1>
          <p className="mt-2 text-white/60">
            TwoCustomer is now watching {brand || "your brand"} across the web,
            social, and Discord. First insights land within minutes.
          </p>
          {slug && (
            <p className="mt-1 text-xs text-white/30">
              monitor slug: <span className="font-mono text-accent-soft/70">{slug}</span>
            </p>
          )}
          <Link
            href="/admin"
            className="mt-6 inline-block rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:brightness-110"
          >
            Go to dashboard
          </Link>
        </main>
      </>
    );
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-lg px-6 py-10">
        <div className="mb-6 flex gap-1">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={
                "h-1 flex-1 rounded-full " +
                (i <= step ? "bg-accent" : "bg-white/10")
              }
            />
          ))}
        </div>
        <h1 className="text-xl font-semibold">{STEPS[step]}</h1>
        <p className="mb-4 text-sm text-white/50">
          Fast setup — connect your sources and go.
        </p>

        <div className="flex flex-col gap-3">
          {step === 0 && (
            <input
              autoFocus
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Brand name (e.g. Aurora Drinks)"
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
          )}
          {step === 1 && (
            <input
              autoFocus
              value={terms}
              onChange={(e) => setTerms(e.target.value)}
              placeholder="Search terms, comma-separated"
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
          )}
          {step === 2 && (
            <input
              autoFocus
              value={handles}
              onChange={(e) => setHandles(e.target.value)}
              placeholder="@x, r/subreddit, linkedin/company"
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
          )}
          {step === 4 && (
            <input
              autoFocus
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="https://github.com/owner/repo (the agent fixes this)"
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
          )}
          {step === 3 && (
            DISCORD_INVITE ? (
              <a
                href={DISCORD_INVITE}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-white/15 px-3 py-2 text-center text-sm hover:border-accent-soft/50"
              >
                Add TwoCustomer to Discord (OAuth) →
              </a>
            ) : (
              <div className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white/50">
                Set <span className="font-mono text-white/70">NEXT_PUBLIC_DISCORD_CLIENT_ID</span> to
                enable the Discord connector. You can arm monitors now and connect later.
              </div>
            )
          )}
        </div>

        {err && (
          <p className="mt-3 text-sm text-red-400">⚠ {err}</p>
        )}

        <div className="mt-6 flex justify-between">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="text-sm text-white/50 disabled:opacity-30"
          >
            ← Back
          </button>
          <button
            onClick={next}
            disabled={saving || (last && !brand.trim())}
            className="rounded-lg bg-accent px-5 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-40"
          >
            {saving ? "Arming…" : last ? "Arm monitors" : "Next"}
          </button>
        </div>
      </main>
    </>
  );
}

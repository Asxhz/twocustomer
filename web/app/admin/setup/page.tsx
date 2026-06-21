"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";
import GithubTokenForm from "@/components/GithubTokenForm";

function Step({ n, cur, label }: { n: number; cur: number; label: string }) {
  const done = cur > n;
  const active = cur === n;
  return (
    <div className="flex items-center gap-2">
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${
          done ? "bg-accent text-white" : active ? "border border-accent text-accent-soft" : "border border-white/20 text-white/40"
        }`}
      >
        {done ? "✓" : n}
      </span>
      <span className={active ? "text-sm text-white" : "text-sm text-white/40"}>{label}</span>
    </div>
  );
}

function Wizard() {
  const router = useRouter();
  const params = useSearchParams();
  const [step, setStep] = useState(1);
  const [company, setCompany] = useState("");
  const [discord, setDiscord] = useState("");
  const [githubLogin, setGithubLogin] = useState<string | null>(null);
  const [brand, setBrand] = useState("");
  const [brandType, setBrandType] = useState<"software" | "physical">("software");
  const [repo, setRepo] = useState("");
  const [terms, setTerms] = useState("");
  const [busy, setBusy] = useState(false);

  // Reflect GitHub connect status when we return from OAuth.
  useEffect(() => {
    fetch("/api/company")
      .then((r) => r.json())
      .then((d) => {
        if (d.company?.name) setCompany(d.company.name);
        if (d.company?.githubLogin) setGithubLogin(d.company.githubLogin);
        if (d.company?.discordGuild) setDiscord(d.company.discordGuild);
      })
      .catch(() => {});
    if (params.get("github") === "connected") setStep(2);
  }, [params]);

  async function saveCompany() {
    setBusy(true);
    await fetch("/api/company", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: company }),
    });
    setBusy(false);
    setStep(2);
  }

  async function saveConnections() {
    setBusy(true);
    await fetch("/api/company", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ discordGuild: discord }),
    });
    setBusy(false);
    setStep(3);
  }

  async function addBrand() {
    setBusy(true);
    await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: brand, type: brandType, repoUrl: repo, terms }),
    });
    setBusy(false);
    setStep(4);
  }

  async function finish() {
    setBusy(true);
    await fetch("/api/company", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ setupComplete: true }),
    });
    router.push("/admin");
  }

  const input =
    "mt-1 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-accent/60";
  const btn =
    "mt-4 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50";

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-xl px-6 py-8">
        <h1 className="text-2xl font-semibold">Set up your company</h1>
        <p className="mt-1 text-sm text-white/50">
          A few steps to arm TwoCustomer. You can change everything later.
        </p>

        <div className="mt-6 flex flex-wrap gap-4">
          <Step n={1} cur={step} label="Company" />
          <Step n={2} cur={step} label="Connect" />
          <Step n={3} cur={step} label="Brand" />
          <Step n={4} cur={step} label="Finish" />
        </div>

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          {step === 1 && (
            <div>
              <label className="text-sm text-white/70">Company name</label>
              <input className={input} value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Northstar Labs" />
              <button className={btn} disabled={busy || !company.trim()} onClick={saveCompany}>
                Continue
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-xs text-white/50">
                  Lets the FDE read your repo, build a safe sandbox preview, and open PRs.
                </p>
                {githubLogin ? (
                  <p className="mt-2 text-sm text-accent-soft">✓ Connected as @{githubLogin}</p>
                ) : (
                  <GithubTokenForm connected={false} primary />
                )}
              </div>
              <div>
                <label className="text-sm text-white/70">Discord guild ID (optional)</label>
                <input className={input} value={discord} onChange={(e) => setDiscord(e.target.value)} placeholder="123456789012345678" />
              </div>
              <button className={btn} disabled={busy} onClick={saveConnections}>
                Continue
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-sm text-white/70">First brand / product name</label>
                <input className={input} value={brand} onChange={(e) => setBrand(e.target.value)} placeholder="Lumina" />
              </div>
              <div className="flex gap-2">
                {(["software", "physical"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setBrandType(t)}
                    className={`rounded-lg px-3 py-1.5 text-sm ${brandType === t ? "bg-accent text-white" : "border border-white/15 text-white/60"}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              {brandType === "software" && (
                <div>
                  <label className="text-sm text-white/70">Repo URL</label>
                  <input className={input} value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="https://github.com/you/app" />
                </div>
              )}
              <div>
                <label className="text-sm text-white/70">Monitor terms (comma-separated)</label>
                <input className={input} value={terms} onChange={(e) => setTerms(e.target.value)} placeholder="Lumina app, Lumina bug" />
              </div>
              <button className={btn} disabled={busy || !brand.trim()} onClick={addBrand}>
                Add brand & arm monitor
              </button>
            </div>
          )}

          {step === 4 && (
            <div>
              <h3 className="text-sm font-medium text-white/80">You&apos;re set 🎉</h3>
              <p className="mt-1 text-sm text-white/60">
                Your company, connections, and first brand are live. The analyst is armed.
              </p>
              <button className={btn} disabled={busy} onClick={finish}>
                Go to dashboard
              </button>
            </div>
          )}
        </section>
      </main>
    </>
  );
}

export default function SetupPage() {
  return (
    <Suspense fallback={null}>
      <Wizard />
    </Suspense>
  );
}

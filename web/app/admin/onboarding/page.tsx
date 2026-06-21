"use client";

import { useState } from "react";
import Link from "next/link";
import Nav from "@/components/Nav";

type Kind = "software" | "physical";

export default function Onboarding() {
  const [kind, setKind] = useState<Kind | "">("");
  const [name, setName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [terms, setTerms] = useState("");
  const [discord, setDiscord] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<string>("");

  async function connect() {
    if (!name.trim() || !kind) return;
    setSaving(true);
    setErr("");
    try {
      const r = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name, type: kind, repoUrl, terms, discordChannel: discord,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || "Failed to connect");
      setDone(d.slug || "");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (done) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-lg px-6 py-16 text-center">
          <div className="text-4xl">✅</div>
          <h1 className="mt-3 text-2xl font-semibold">Project connected</h1>
          <p className="mt-2 text-white/60">
            <strong>{name}</strong> is connected and now the active project.
            Everything. chat, monitor, fix, campaigns. runs against it.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/admin" className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:brightness-110">
              Open dashboard
            </Link>
            {kind === "software" ? (
              <Link href="/admin/fix" className="rounded-lg border border-white/15 px-5 py-2.5 text-sm hover:border-accent-soft/50">
                Fix the repo →
              </Link>
            ) : (
              <Link href="/monitor" className="rounded-lg border border-white/15 px-5 py-2.5 text-sm hover:border-accent-soft/50">
                See the live feed →
              </Link>
            )}
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-lg px-6 py-12">
        <h1 className="text-2xl font-semibold">Connect a project</h1>
        <p className="mb-6 mt-1 text-sm text-white/50">
          Two kinds: a software project (the agent fixes the repo) or a physical
          consumer product (the agent monitors + markets it).
        </p>

        <div className="mb-5 grid grid-cols-2 gap-3">
          {(["software", "physical"] as const).map((k) => (
            <button
              key={k}
              onClick={() => setKind(k)}
              className={
                "rounded-xl border p-4 text-left transition " +
                (kind === k
                  ? "border-accent-soft/60 bg-accent/10"
                  : "border-white/10 bg-white/[0.02] hover:border-white/20")
              }
            >
              <div className="text-sm font-medium">
                {k === "software" ? "⌁ Software project" : "🥤 Physical product"}
              </div>
              <div className="mt-1 text-xs text-white/50">
                {k === "software"
                  ? "Connect a GitHub repo. the agent diagnoses + opens PRs."
                  : "Monitor signal, run campaigns + customer interviews."}
              </div>
            </button>
          ))}
        </div>

        {kind && (
          <div className="flex flex-col gap-3">
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={kind === "software" ? "Project name (e.g. Acme App)" : "Brand name (e.g. Olipop)"}
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
            {kind === "software" ? (
              <input
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
              />
            ) : (
              <input
                value={terms}
                onChange={(e) => setTerms(e.target.value)}
                placeholder="Monitor terms, comma-separated (e.g. prebiotic soda, recall)"
                className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
              />
            )}
            <input
              value={discord}
              onChange={(e) => setDiscord(e.target.value)}
              placeholder="Discord channel id (optional. team context)"
              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent-soft/60"
            />
            {err && <p className="text-sm text-red-400">⚠ {err}</p>}
            <button
              onClick={connect}
              disabled={saving || !name.trim()}
              className="mt-1 self-start rounded-lg bg-accent px-5 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-40"
            >
              {saving ? "Connecting…" : "Connect project"}
            </button>
          </div>
        )}
      </main>
    </>
  );
}

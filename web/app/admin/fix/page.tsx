"use client";

import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { Badge, Button, Card, Field, inputCls, Spinner } from "@/components/ui";

interface FixResult {
  file?: string; explanation?: string; before?: string; after?: string;
  resolved?: boolean; preview_url?: string | null; error?: string;
}
interface GithubResult {
  repo?: string; file?: string; explanation?: string; diff?: string;
  pr_url?: string | null; context_used?: boolean; error?: string;
}
interface RepoResult {
  repo?: string; file?: string; explanation?: string; diff?: string;
  pr_url?: string | null; preview_url?: string | null; preview_note?: string;
  resolved?: boolean; error?: string;
}

export default function FixPanel() {
  const [mode, setMode] = useState<"connected" | "github" | "sandbox">("connected");

  // Connected-repo mode (headline: PR + live preview)
  const [repoSymptom, setRepoSymptom] = useState("");
  const [repoRes, setRepoRes] = useState<RepoResult | null>(null);
  const [repoBusy, setRepoBusy] = useState(false);

  // GitHub mode
  const [repoUrl, setRepoUrl] = useState("");
  const [ghSymptom, setGhSymptom] = useState("");

  // Prefill the repo connected during onboarding.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("tc_repo");
      if (saved) setRepoUrl(saved);
    } catch {}
  }, []);
  const [ghCtx, setGhCtx] = useState("");
  const [gh, setGh] = useState<GithubResult | null>(null);
  const [ghBusy, setGhBusy] = useState(false);

  // Sandbox demo mode
  const [symptom, setSymptom] = useState("The homepage hero renders 'hi hi my my' instead of the real line");
  const [res, setRes] = useState<FixResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function runRepo() {
    if (!repoUrl.trim()) return;
    setRepoBusy(true);
    setRepoRes(null);
    try {
      const r = await fetch("/api/fix-repo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl.trim(), symptom: repoSymptom }),
      });
      setRepoRes(await r.json());
    } catch {
      setRepoRes({ error: "Agent unreachable. check the agent deployment." });
    } finally {
      setRepoBusy(false);
    }
  }

  async function runGithub() {
    if (!repoUrl.trim()) return;
    setGhBusy(true);
    setGh(null);
    try {
      const r = await fetch("/api/fix-github", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl.trim(), symptom: ghSymptom, context: ghCtx }),
      });
      setGh(await r.json());
    } catch {
      setGh({ error: "Agent unreachable." });
    } finally {
      setGhBusy(false);
    }
  }

  async function runSandbox() {
    setBusy(true);
    setRes(null);
    try {
      const r = await fetch("/api/fix", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symptom }),
      });
      setRes(await r.json());
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="mb-2 flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Forward-deployed fix</h1>
          <Badge tone="good">Claude</Badge>
        </header>
        <p className="mb-5 text-sm text-white/55">
          Point it at a <strong>GitHub repo</strong>. it clones, diagnoses the bug
          (using context from Discord + web monitoring), patches it, and opens a PR.
          Or run the built-in sandbox demo.
        </p>

        <div className="mb-5 inline-flex rounded-lg border border-white/10 p-0.5 text-sm">
          {(["connected", "github", "sandbox"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={
                "rounded-md px-3 py-1.5 " +
                (mode === m ? "bg-accent text-white" : "text-white/60 hover:text-white")
              }
            >
              {m === "connected" ? "Connected repo → preview + PR" : m === "github" ? "Any GitHub repo" : "Sandbox demo"}
            </button>
          ))}
        </div>

        {mode === "connected" ? (
          <>
            <Card className="mb-6 flex flex-col gap-3">
              <Field label="Connected repo URL">
                <input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo" className={inputCls} />
              </Field>
              <Field label="What's broken? (symptom)">
                <input value={repoSymptom} onChange={(e) => setRepoSymptom(e.target.value)}
                  placeholder="e.g. the homepage hero shows placeholder text" className={inputCls} />
              </Field>
              <div>
                <Button onClick={runRepo} disabled={repoBusy || !repoUrl.trim()}>
                  {repoBusy ? <Spinner /> : "Fix it → preview + PR"}
                </Button>
              </div>
            </Card>

            {repoRes && (
              <Card className="flex flex-col gap-3">
                {repoRes.error ? (
                  <p className="text-sm text-amber-200">{repoRes.error}</p>
                ) : (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      {repoRes.resolved ? <Badge tone="good">✅ fix ready</Badge> : <Badge tone="warn">⚠ review</Badge>}
                      <Badge tone="neutral">{repoRes.repo}</Badge>
                      <span className="text-sm font-medium">{repoRes.file}</span>
                    </div>
                    <p className="text-sm text-white/70">{repoRes.explanation}</p>
                    {repoRes.diff && (
                      <pre className="overflow-x-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs">
                        {repoRes.diff.split("\n").map((l, i) => (
                          <div key={i} className={
                            l.startsWith("+") && !l.startsWith("+++") ? "text-accent-soft" :
                            l.startsWith("-") && !l.startsWith("---") ? "text-red-300" : "text-white/60"
                          }>{l}</div>
                        ))}
                      </pre>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {repoRes.preview_url && (
                        <a href={repoRes.preview_url} target="_blank" rel="noopener noreferrer"
                          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110">
                          Open live preview ↗
                        </a>
                      )}
                      {repoRes.pr_url && (
                        <a href={repoRes.pr_url} target="_blank" rel="noopener noreferrer"
                          className="rounded-lg border border-white/15 px-4 py-2 text-sm hover:border-accent/50">
                          View PR ↗
                        </a>
                      )}
                    </div>
                    {!repoRes.preview_url && repoRes.preview_note && (
                      <p className="text-xs text-white/40">{repoRes.preview_note}</p>
                    )}
                  </>
                )}
              </Card>
            )}
          </>
        ) : mode === "github" ? (
          <>
            <Card className="mb-6 flex flex-col gap-3">
              <Field label="Public GitHub repo URL">
                <input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo" className={inputCls} />
              </Field>
              <Field label="What's wrong? (symptom)">
                <input value={ghSymptom} onChange={(e) => setGhSymptom(e.target.value)}
                  placeholder="e.g. the landing page CTA is broken / copy is off" className={inputCls} />
              </Field>
              <Field label="Extra context (optional. Discord notes, etc.)">
                <textarea value={ghCtx} onChange={(e) => setGhCtx(e.target.value)} rows={3}
                  placeholder="Paste anything the agent should know." className={inputCls} />
              </Field>
              <button
                type="button"
                onClick={async () => {
                  const r = await fetch("/api/discord-context");
                  const d = await r.json();
                  setGhCtx((c) => (d.context ? (c ? c + "\n" : "") + d.context : c));
                }}
                className="self-start rounded-md border border-white/15 px-3 py-1.5 text-xs text-white/70 hover:border-accent-soft/50 hover:text-white"
              >
                ⌁ Pull Discord context
              </button>
              <div>
                <Button onClick={runGithub} disabled={ghBusy || !repoUrl.trim()}>
                  {ghBusy ? <Spinner /> : "Clone, diagnose & open PR"}
                </Button>
              </div>
            </Card>

            {gh && (
              <Card className="flex flex-col gap-3">
                {gh.error ? (
                  <p className="text-sm text-amber-200">{gh.error}</p>
                ) : (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="good">{gh.repo}</Badge>
                      <span className="text-sm font-medium">{gh.file}</span>
                      {gh.context_used && <Badge tone="neutral">context used</Badge>}
                    </div>
                    <p className="text-sm text-white/70">{gh.explanation}</p>
                    {gh.diff && (
                      <pre className="overflow-x-auto rounded-lg border border-white/10 bg-black/40 p-3 text-xs">
                        {gh.diff.split("\n").map((l, i) => (
                          <div key={i} className={
                            l.startsWith("+") && !l.startsWith("+++") ? "text-accent-soft" :
                            l.startsWith("-") && !l.startsWith("---") ? "text-red-300" : "text-white/60"
                          }>{l}</div>
                        ))}
                      </pre>
                    )}
                    {gh.pr_url ? (
                      <a href={gh.pr_url} target="_blank" rel="noopener noreferrer"
                        className="text-sm font-medium text-accent-soft">Open the pull request →</a>
                    ) : (
                      <p className="text-xs text-white/40">Set GITHUB_TOKEN (repo scope) to open the PR automatically. Diff is ready to apply.</p>
                    )}
                  </>
                )}
              </Card>
            )}
          </>
        ) : (
          <>
            <Card className="mb-6 flex flex-col gap-3">
              <Field label="Symptom">
                <input value={symptom} onChange={(e) => setSymptom(e.target.value)} className={inputCls} />
              </Field>
              <div>
                <Button onClick={runSandbox} disabled={busy}>
                  {busy ? <Spinner /> : "Diagnose & fix"}
                </Button>
              </div>
            </Card>

            {res && (
              <Card className="flex flex-col gap-3">
                {res.error ? (
                  <p className="text-sm text-amber-200">{res.error}</p>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      {res.resolved ? <Badge tone="good">✅ resolved</Badge> : <Badge tone="warn">⚠ not resolved</Badge>}
                      <span className="text-sm font-medium">{res.file}</span>
                    </div>
                    <p className="text-sm text-white/70">{res.explanation}</p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <div className="mb-1 text-xs uppercase text-white/40">Before</div>
                        <pre className="rounded-lg border border-red-400/20 bg-black/40 p-3 text-xs text-red-200">{res.before}</pre>
                      </div>
                      <div>
                        <div className="mb-1 text-xs uppercase text-white/40">After</div>
                        <pre className="rounded-lg border border-accent/20 bg-black/40 p-3 text-xs text-accent-soft">{res.after}</pre>
                      </div>
                    </div>
                    {res.preview_url && (
                      <a href={res.preview_url} target="_blank" rel="noopener noreferrer" className="text-sm text-accent-soft">
                        Open preview deploy →
                      </a>
                    )}
                  </>
                )}
              </Card>
            )}
          </>
        )}
      </main>
    </>
  );
}

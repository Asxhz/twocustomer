"use client";

import { useState } from "react";
import Nav from "@/components/Nav";
import { Badge, Button, Card, Field, inputCls, Spinner } from "@/components/ui";

interface FixResult {
  file?: string; explanation?: string; before?: string; after?: string;
  resolved?: boolean; preview_url?: string | null; error?: string;
}

export default function FixPanel() {
  const [symptom, setSymptom] = useState("The homepage hero renders 'hi hi my my' instead of the real line");
  const [res, setRes] = useState<FixResult | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
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
          <Badge tone="good">Claude · sandbox</Badge>
        </header>
        <p className="mb-6 text-sm text-white/55">
          Report a visible bug on the brand&apos;s site. TwoCustomer diagnoses it, patches a
          copy in an <strong>isolated sandbox</strong> (never production), and validates the fix.
        </p>

        <Card className="mb-6 flex flex-col gap-3">
          <Field label="Symptom">
            <input value={symptom} onChange={(e) => setSymptom(e.target.value)} className={inputCls} />
          </Field>
          <div>
            <Button onClick={run} disabled={busy}>
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
                    <pre className="rounded-lg border border-emerald-400/20 bg-black/40 p-3 text-xs text-emerald-200">{res.after}</pre>
                  </div>
                </div>
                {res.preview_url ? (
                  <a href={res.preview_url} target="_blank" className="text-sm text-emerald-400">
                    Open preview deploy →
                  </a>
                ) : (
                  <p className="text-xs text-white/40">Set VERCEL_TOKEN to deploy a live preview URL.</p>
                )}
              </>
            )}
          </Card>
        )}
      </main>
    </>
  );
}

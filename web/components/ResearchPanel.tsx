"use client";

import { useState } from "react";

interface Research {
  fresh?: number;
  high_signal?: number;
  persisted?: number;
  insight?: { title?: string; body?: string; severity?: string } | null;
  influence?: { sentiment?: string; themes?: string[]; influence?: string; by_platform?: Record<string, number> };
  top?: { platform: string; text: string; author: string; score: number }[];
  error?: string;
}

export default function ResearchPanel({ slug }: { slug: string }) {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<Research | null>(null);
  const [imgBusy, setImgBusy] = useState(false);
  const [img, setImg] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setRes(null);
    setImg(null);
    try {
      const r = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brand_slug: slug }),
      });
      setRes(await r.json());
    } catch {
      setRes({ error: "Agent unreachable." });
    } finally {
      setBusy(false);
    }
  }

  // Heuristics -> AI-adjusted product visual (the Snap Spectacles loop).
  async function improve() {
    if (!res) return;
    setImgBusy(true);
    setImg(null);
    const themes = (res.influence?.themes || []).join(", ");
    const drive = res.influence?.influence || "";
    const instruction =
      `A clean, appealing product photo of ${slug.replace(/-/g, " ")} that addresses ` +
      `what customers are saying: ${themes}. ${drive}`.slice(0, 600);
    try {
      const r = await fetch("/api/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const d = await r.json();
      if (d.url) setImg(d.url);
    } finally {
      setImgBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-white/80">Signal search</h3>
          <p className="text-xs text-white/45">Live: web, Reddit, HN, news, X/LinkedIn, Discord.</p>
        </div>
        <button
          onClick={run}
          disabled={busy}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Searching" : "Run signal search"}
        </button>
      </div>

      {res?.error && <p className="mt-3 text-sm text-amber-200">{res.error}</p>}

      {res && !res.error && (
        <div className="mt-4 flex flex-col gap-3">
          <div className="flex flex-wrap gap-2 text-xs text-white/60">
            <span className="rounded-full bg-white/10 px-2 py-0.5">{res.fresh ?? 0} found</span>
            <span className="rounded-full bg-accent/15 px-2 py-0.5 text-accent-soft">{res.high_signal ?? 0} high-signal</span>
            {res.influence?.sentiment && (
              <span className="rounded-full bg-white/10 px-2 py-0.5">sentiment: {res.influence.sentiment}</span>
            )}
          </div>

          {(res.fresh ?? 0) === 0 && (
            <p className="text-sm text-white/50">
              No live mentions found this pass. Add brand terms/handles in setup, or connect Reddit/Browserbase keys for more sources.
            </p>
          )}

          {res.insight && (
            <div className="rounded-lg border border-accent/30 bg-accent/[0.05] p-3">
              <div className="text-xs font-medium text-accent-soft">New insight</div>
              <div className="mt-1 text-sm font-medium">{res.insight.title}</div>
              <p className="text-sm text-white/70">{res.insight.body}</p>
            </div>
          )}

          {res.influence?.themes && res.influence.themes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {res.influence.themes.map((t, i) => (
                <span key={i} className="rounded-full border border-white/10 px-2 py-0.5 text-xs text-white/60">{t}</span>
              ))}
            </div>
          )}
          {res.influence?.influence && (
            <p className="text-xs text-white/55">{res.influence.influence}</p>
          )}

          {(res.fresh ?? 0) > 0 && (
            <div>
              <button
                onClick={improve}
                disabled={imgBusy}
                className="rounded-lg border border-white/15 px-4 py-2 text-sm hover:border-accent/50 disabled:opacity-50"
              >
                {imgBusy ? "Generating" : "Improve product with AI"}
              </button>
              {img && (
                <div className="mt-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={img} alt="AI-adjusted product" className="max-h-72 rounded-lg border border-white/10" />
                </div>
              )}
            </div>
          )}

          {res.top && res.top.length > 0 && (
            <ul className="flex flex-col gap-2">
              {res.top.map((m, i) => (
                <li key={i} className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm">
                  <span className="mr-2 rounded bg-white/10 px-1.5 py-0.5 text-xs uppercase">{m.platform}</span>
                  <span className="text-white/75">{m.text}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

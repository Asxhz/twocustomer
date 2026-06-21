"use client";

import { useEffect, useRef, useState } from "react";
import { readSSE, type ChatMessage } from "@/lib/api";

interface ToolChip {
  name: string;
  done: boolean;
}
type Artifact =
  | { kind: "packet"; text: string }
  | { kind: "image"; url: string }
  | { kind: "call_invite"; reason: string }
  | {
      kind: "fix_result";
      repo?: string;
      file?: string;
      explanation?: string;
      diff?: string;
      pr_url?: string;
      preview_url?: string;
      preview_note?: string;
    };

export default function ChatThread({ injected }: { injected?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [tools, setTools] = useState<ToolChip[]>([]);
  const [status, setStatus] = useState("");
  const [streaming, setStreaming] = useState("");
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (injected) setInput(injected);
  }, [injected]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    setTools([]);
    setStreaming("");
    setArtifact(null);
    setStatus("Thinking…");
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: text }]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      let acc = "";
      await readSSE(res, ({ event, data }) => {
        const parsed = safeParse(data) as Record<string, unknown>;
        if (event === "error") {
          setStatus("");
        } else if (event === "status") {
          setStatus((parsed.text as string) || "Working…");
        } else if (event === "tool_start") {
          const name = parsed.name as string;
          setStatus(`Running ${name}…`);
          setTools((t) =>
            t.some((x) => x.name === name && !x.done)
              ? t
              : [...t, { name, done: false }],
          );
        } else if (event === "tool_end") {
          const name = parsed.name as string;
          setTools((t) =>
            t.map((x) => (x.name === name && !x.done ? { ...x, done: true } : x)),
          );
        } else if (event === "artifact") {
          if (parsed.kind === "image") {
            setArtifact({ kind: "image", url: parsed.url as string });
          } else if (parsed.kind === "call_invite") {
            setArtifact({ kind: "call_invite", reason: (parsed.reason as string) || "" });
          } else if (parsed.kind === "fix_result") {
            setArtifact({ kind: "fix_result", ...(parsed as object) });
          } else {
            setArtifact({ kind: "packet", text: parsed.text as string });
          }
        } else if (event === "token") {
          setStatus("");
          acc += (parsed.text as string) || "";
          setStreaming(acc);
        } else if (event === "message") {
          setStatus("");
          setMessages((m) => [
            ...m,
            { role: "assistant", content: (parsed.text as string) || "" },
          ]);
          setStreaming("");
        }
      });
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "⚠ Agent unreachable. Try again in a moment." },
      ]);
    } finally {
      setBusy(false);
      setStatus("");
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex min-h-48 flex-col gap-3">
        {messages.length === 0 && !busy && (
          <p className="text-sm text-white/40">
            Ask TwoCustomer to monitor a brand, build a campaign, fix a site, or edit an image.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "max-w-[80%] self-end rounded-2xl bg-white/10 px-4 py-2 text-sm"
                : "max-w-[80%] self-start whitespace-pre-wrap rounded-2xl bg-accent/10 px-4 py-2 text-sm text-accent-soft"
            }
          >
            {m.content}
          </div>
        ))}

        {tools.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tools.map((t, i) => (
              <span
                key={i}
                className={
                  "rounded-full border px-2 py-0.5 text-xs " +
                  (t.done
                    ? "border-accent/30 bg-accent/10 text-accent-soft"
                    : "border-amber-400/30 bg-amber-400/10 text-amber-200")
                }
              >
                {t.done ? "✓" : "⏳"} {t.name}
              </span>
            ))}
          </div>
        )}

        {status && (
          <div className="flex items-center gap-2 text-xs text-white/45">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            {status}
          </div>
        )}

        {streaming && (
          <div className="max-w-[80%] self-start whitespace-pre-wrap rounded-2xl bg-accent/10 px-4 py-2 text-sm text-accent-soft">
            {streaming}
            <span className="ml-0.5 animate-pulse">▋</span>
          </div>
        )}

        {artifact?.kind === "packet" && (
          <div className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-3">
            <div className="mb-1 text-xs font-medium text-amber-200">📦 Packet</div>
            <pre className="whitespace-pre-wrap text-xs text-amber-100/90">{artifact.text}</pre>
          </div>
        )}
        {artifact?.kind === "image" && (
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
            <div className="mb-2 text-xs font-medium text-white/60">🖼 Generated image</div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={artifact.url} alt="generated" className="max-h-72 rounded-lg" />
          </div>
        )}
        {artifact?.kind === "call_invite" && <JoinCallCard reason={artifact.reason} />}
        {artifact?.kind === "fix_result" && (
          <div className="rounded-xl border border-accent/30 bg-accent/[0.06] p-3">
            <div className="mb-1 text-xs font-medium text-accent-soft">🔧 Fix ready</div>
            {artifact.explanation && (
              <p className="text-sm text-white/80">{artifact.explanation}</p>
            )}
            {artifact.file && (
              <p className="mt-1 text-xs text-white/50">{artifact.repo} · {artifact.file}</p>
            )}
            {artifact.diff && (
              <pre className="mt-2 max-h-48 overflow-auto rounded-lg border border-white/10 bg-black/40 p-2 text-xs text-white/70">
                {artifact.diff}
              </pre>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              {artifact.preview_url && (
                <a href={artifact.preview_url} target="_blank" rel="noopener"
                   className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:brightness-110">
                  Open preview ↗
                </a>
              )}
              {artifact.pr_url && (
                <a href={artifact.pr_url} target="_blank" rel="noopener"
                   className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:border-accent/50">
                  View PR ↗
                </a>
              )}
            </div>
            {!artifact.preview_url && artifact.preview_note && (
              <p className="mt-2 text-xs text-white/40">{artifact.preview_note}</p>
            )}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Message TwoCustomer…"
          className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent/50"
          disabled={busy}
        />
        <button
          onClick={send}
          disabled={busy}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:bg-accent disabled:opacity-50"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function JoinCallCard({ reason }: { reason: string }) {
  const [busy, setBusy] = useState(false);
  const [room, setRoom] = useState<string | null>(null);

  async function join() {
    setBusy(true);
    try {
      const r = await fetch("/api/session-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      const d = await r.json();
      if (d.room_url) {
        setRoom(d.room_url);
        window.open(d.room_url, "_blank", "noopener");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-accent/30 bg-accent/[0.06] p-3">
      <div className="mb-1 text-xs font-medium text-accent-soft">📞 Let&apos;s hop on a call</div>
      <p className="text-sm text-white/80">
        {reason || "Share your screen so I can see exactly what to change, then I'll build a fixed preview."}
      </p>
      <button
        onClick={join}
        disabled={busy}
        className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
      >
        {busy ? "Creating room…" : room ? "Re-open call" : "Join video call"}
      </button>
      {room && (
        <p className="mt-2 break-all text-xs text-white/40">{room}</p>
      )}
    </div>
  );
}

function safeParse(s: string): unknown {
  try {
    return JSON.parse(s);
  } catch {
    return { text: s };
  }
}

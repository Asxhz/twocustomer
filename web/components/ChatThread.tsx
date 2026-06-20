"use client";

import { useEffect, useRef, useState } from "react";
import { readSSE, type ChatMessage } from "@/lib/api";

interface ToolChip {
  name: string;
  done: boolean;
}
type Artifact =
  | { kind: "packet"; text: string }
  | { kind: "image"; url: string };

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
                : "max-w-[80%] self-start whitespace-pre-wrap rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100"
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
                    ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
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
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            {status}
          </div>
        )}

        {streaming && (
          <div className="max-w-[80%] self-start whitespace-pre-wrap rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100">
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
      </div>

      <div className="flex gap-2">
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Message TwoCustomer…"
          className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-emerald-400/50"
          disabled={busy}
        />
        <button
          onClick={send}
          disabled={busy}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-black hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
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

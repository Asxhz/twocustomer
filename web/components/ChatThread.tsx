"use client";

import { useEffect, useRef, useState } from "react";
import { readSSE, type ChatMessage } from "@/lib/api";

interface ToolEvent {
  name: string;
  output: string;
}

export default function ChatThread({ injected }: { injected?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [tools, setTools] = useState<ToolEvent[]>([]);
  const [streaming, setStreaming] = useState("");
  const [artifact, setArtifact] = useState<string>("");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Voice transcript (or any external text) flows into the input box.
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
    setArtifact("");
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
        const parsed = safeParse(data);
        if (event === "error") {
          const msg = (parsed as { error?: string }).error || "Something went wrong.";
          setMessages((m) => [...m, { role: "assistant", content: `⚠ ${msg}` }]);
          setStreaming("");
        } else if (event === "tool_end") {
          setTools((t) => [...t, parsed as ToolEvent]);
        } else if (event === "artifact") {
          setArtifact((parsed as { text: string }).text);
        } else if (event === "token") {
          acc += (parsed as { text: string }).text;
          setStreaming(acc);
        } else if (event === "message") {
          setMessages((m) => [
            ...m,
            { role: "assistant", content: (parsed as { text: string }).text },
          ]);
          setStreaming("");
        }
      });
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "⚠ agent unreachable (is it running on :8000?)" },
      ]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="flex flex-col gap-3 min-h-48">
        {messages.length === 0 && (
          <p className="text-sm text-white/40">
            Ask TwoCustomer to monitor a brand, build a campaign, or surface insights.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "self-end max-w-[80%] rounded-2xl bg-white/10 px-4 py-2 text-sm"
                : "self-start max-w-[80%] rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100"
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
                className="rounded-full border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-xs text-amber-200"
                title={t.output}
              >
                🔧 {t.name}
              </span>
            ))}
          </div>
        )}
        {streaming && (
          <div className="self-start max-w-[80%] rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm text-emerald-100">
            {streaming}
            <span className="ml-0.5 animate-pulse">▋</span>
          </div>
        )}
        {artifact && (
          <div className="rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-3">
            <div className="mb-1 text-xs font-medium text-amber-200">📦 Packet</div>
            <pre className="whitespace-pre-wrap text-xs text-amber-100/90">{artifact}</pre>
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
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
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

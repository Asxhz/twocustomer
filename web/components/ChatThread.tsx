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
  | { kind: "call_invite"; reason: string; report?: boolean; issue?: string }
  | {
      kind: "fix_result";
      repo?: string;
      file?: string;
      files?: string[];
      explanation?: string;
      diff?: string;
      pr_url?: string;
      preview_url?: string;
      preview_note?: string;
      before?: string;
      after?: string;
      resolved?: boolean;
      iterable?: boolean;
      branch?: string;
      steps?: { label: string; done?: boolean }[];
    };

// Slash commands that open the live "get on a call, show me, I fix it" flow.
const REPORT_COMMANDS = ["/report", "/idea", "/recommend", "/rec"];

// Human labels for the inline activity chips (never show raw tool names).
const TOOL_LABEL: Record<string, string> = {
  fix_connected_repo: "Editing your site",
  fix_site: "Building a preview",
  fix_github: "Reading the code",
  research_product: "Checking live signal",
  monitor_brand: "Scanning mentions",
  edit_product_image: "Editing the image",
  request_call: "Setting up a call",
  create_campaign: "Drafting a campaign",
  edit_copy: "Editing copy",
  web_search: "Searching the web",
};
const toolLabel = (n: string) => TOOL_LABEL[n] || "Working";

export default function ChatThread({ injected, onAssistant }: { injected?: string; onAssistant?: (text: string) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [tools, setTools] = useState<ToolChip[]>([]);
  const [status, setStatus] = useState("");
  const [streaming, setStreaming] = useState("");
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [input, setInput] = useState("");
  const [followup, setFollowup] = useState("");
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (injected) setInput(injected);
  }, [injected]);

  // /report | /idea | /rec | /recommend → open the live call + screen-share flow
  // instead of a plain chat turn.
  function startReportFlow(raw: string) {
    const cmd = raw.split(/\s+/)[0].toLowerCase();
    const issue = raw.slice(cmd.length).trim() || "Something on the site looks off.";
    setInput("");
    setTools([]);
    setStreaming("");
    setStatus("");
    setMessages((m) => [
      ...m,
      { role: "user", content: raw },
      {
        role: "assistant",
        content:
          "Let's hop on a quick call so I can see it. Tap Join, share your screen, " +
          "and show me what's not working. Then I'll build you a fixed preview.",
      },
    ]);
    setArtifact({
      kind: "call_invite",
      reason:
        "Share your screen so I can see exactly what's off, then I'll build a fixed preview.",
      report: true,
      issue,
    });
  }

  // User confirmed they are sharing their screen. Acknowledge, then run the real
  // FDE fix and deploy a preview.
  function onScreenShared(issue: string) {
    setMessages((m) => [
      ...m,
      {
        role: "assistant",
        content:
          "I can see your screen now and I can see the issue. Give me a moment, " +
          "I'm building a fixed preview.",
      },
    ]);
    return runFix(issue, false);
  }

  // Run the connected-repo FDE. iterate=true stacks the change on the prior one
  // (same branch/PR) and redeploys an updated preview — the "keep editing" loop.
  async function runFix(issue: string, iterate: boolean) {
    if (busy || !issue.trim()) return;
    setArtifact(null);
    setBusy(true);
    setStatus(iterate ? "Applying your change" : "Building a preview");
    try {
      const r = await fetch("/api/fix", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symptom: issue, iterate }),
      });
      const d = (await r.json()) as Record<string, unknown>;
      setArtifact({
        kind: "fix_result",
        repo: d.repo as string,
        file: d.file as string,
        files: d.files as string[],
        explanation: d.explanation as string,
        diff: d.diff as string,
        pr_url: d.pr_url as string,
        preview_url: d.preview_url as string,
        before: d.before as string,
        after: d.after as string,
        resolved: Boolean(d.resolved),
        iterable: Boolean(d.iterable),
        branch: d.branch as string,
        steps: (d.steps as { label: string; done?: boolean }[]) || [],
      });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: d.preview_url
            ? (iterate
                ? "Updated. I applied your change and redeployed the preview. Open it below, and tell me the next change."
                : "Done. I made the change and deployed a live preview. Open it below, then tell me what to change next.")
            : d.error
              ? `That did not go through: ${d.error}`
              : "I took a pass at it. Here is what I found.",
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "⚠ Couldn't reach the fix engine. Try again in a moment." },
      ]);
    } finally {
      setBusy(false);
      setStatus("");
      inputRef.current?.focus();
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    if (REPORT_COMMANDS.includes(text.split(/\s+/)[0].toLowerCase())) {
      startReportFlow(text);
      return;
    }
    setBusy(true);
    setInput("");
    setTools([]);
    setStreaming("");
    setArtifact(null);
    setStatus("Working");
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
          setStatus((parsed.text as string) || "Working");
        } else if (event === "tool_start") {
          const name = parsed.name as string;
          const friendly: Record<string, string> = {
            fix_connected_repo: "Looking at your repo",
            fix_site: "Building a preview",
            fix_github: "Reading the code",
            research_product: "Checking live signal",
            monitor_brand: "Scanning mentions",
            edit_product_image: "Generating the image",
            request_call: "Setting up a call",
          };
          setStatus(friendly[name] || "Working");
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
          const reply = (parsed.text as string) || "";
          setMessages((m) => [...m, { role: "assistant", content: reply }]);
          setStreaming("");
          if (reply) onAssistant?.(reply);
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
            <br />
            Or type <span className="text-accent-soft">/report</span> (also{" "}
            <span className="text-accent-soft">/idea</span>,{" "}
            <span className="text-accent-soft">/rec</span>) to hop on a call, share your
            screen, and get a fixed preview.
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
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs " +
                  (t.done
                    ? "border-accent/25 bg-accent/10 text-accent"
                    : "border-white/15 bg-white/[0.04] text-white/60")
                }
              >
                <span className={t.done ? "text-accent" : "h-1.5 w-1.5 animate-pulse rounded-full bg-white/40"}>
                  {t.done ? "✓" : ""}
                </span>
                {toolLabel(t.name)}
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
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.08] p-3">
            <div className="mb-1 text-xs font-semibold text-amber-600">Packet</div>
            <pre className="whitespace-pre-wrap text-xs text-foreground/80">{artifact.text}</pre>
          </div>
        )}
        {artifact?.kind === "image" && (
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
            <div className="mb-2 text-xs font-medium text-white/60">🖼 Generated image</div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={artifact.url} alt="generated" className="max-h-72 rounded-lg" />
          </div>
        )}
        {artifact?.kind === "call_invite" && (
          <JoinCallCard
            reason={artifact.reason}
            report={artifact.report}
            onShared={
              artifact.report ? () => onScreenShared(artifact.issue || "") : undefined
            }
          />
        )}
        {artifact?.kind === "fix_result" && (
          <div className="rounded-xl border border-accent/30 bg-accent/[0.06] p-3">
            <div className="mb-1 text-xs font-semibold text-accent">Preview ready</div>
            {artifact.steps && artifact.steps.length > 0 && (
              <ul className="mb-2 space-y-0.5 text-xs text-white/70">
                {artifact.steps.map((s, i) => (
                  <li key={i}>
                    <span className="text-accent-soft">✓</span> {s.label}
                  </li>
                ))}
              </ul>
            )}
            {artifact.explanation && (
              <p className="text-sm text-white/80">{artifact.explanation}</p>
            )}
            {(artifact.files?.length || artifact.file) && (
              <p className="mt-1 text-xs text-white/50">
                {[artifact.repo, (artifact.files?.length ? artifact.files.join(", ") : artifact.file)]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            )}
            {(artifact.before || artifact.after) && (
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-red-400/20 bg-red-400/[0.06] p-2">
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-red-600">Before</div>
                  <pre className="whitespace-pre-wrap text-foreground/80">{artifact.before}</pre>
                </div>
                <div className="rounded-lg border border-accent/20 bg-accent/[0.06] p-2">
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-accent-soft">After</div>
                  <pre className="whitespace-pre-wrap text-white/80">{artifact.after}</pre>
                </div>
              </div>
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
            {artifact.iterable && artifact.preview_url && (
              <div className="mt-3 border-t border-white/10 pt-2">
                <p className="mb-1.5 text-[11px] text-white/50">
                  Keep editing. For example: “make the accent color green” or “change the font”.
                </p>
                <div className="flex gap-2">
                  <input
                    value={followup}
                    onChange={(e) => setFollowup(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && followup.trim() && !busy) {
                        const v = followup.trim();
                        setFollowup("");
                        runFix(v, true);
                      }
                    }}
                    placeholder="Ask for another change…"
                    className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-1.5 text-xs outline-none focus:border-accent/50"
                    disabled={busy}
                  />
                  <button
                    onClick={() => {
                      const v = followup.trim();
                      if (!v || busy) return;
                      setFollowup("");
                      runFix(v, true);
                    }}
                    disabled={busy}
                    className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white hover:brightness-110 disabled:opacity-50"
                  >
                    {busy ? "…" : "Apply"}
                  </button>
                </div>
              </div>
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
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

interface PreviewLink {
  preview_url?: string;
  pr_url?: string;
  explanation?: string;
  files?: string[];
  at?: number;
}

function JoinCallCard({
  reason,
  report,
  onShared,
}: {
  reason: string;
  report?: boolean;
  onShared?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [room, setRoom] = useState<string | null>(null);
  const [roomUrl, setRoomUrl] = useState<string>("");
  const [links, setLinks] = useState<PreviewLink[]>([]);
  const [err, setErr] = useState("");

  async function join() {
    setBusy(true);
    setErr("");
    try {
      const r = await fetch("/api/call/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok && d.room_url) {
        setRoomUrl(d.room_url);
        setRoom(d.token ? `${d.room_url}?t=${d.token}` : d.room_url);
      } else {
        setErr(d.error || "Could not start the call. Try again.");
      }
    } catch {
      setErr("Could not reach the call service. Try again.");
    } finally {
      setBusy(false);
    }
  }

  // While on a call, poll for preview links the agent produces so they always
  // show in this panel (not only in the Daily chat).
  useEffect(() => {
    if (!roomUrl) return;
    let live = true;
    const tick = async () => {
      try {
        const r = await fetch(`/api/call/links?room=${encodeURIComponent(roomUrl)}`);
        const d = await r.json();
        if (live && Array.isArray(d.links)) setLinks(d.links);
      } catch {
        // ignore transient poll errors
      }
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, [roomUrl]);

  return (
    <div className="rounded-xl border border-white/10 bg-surface p-3">
      <div className="mb-1 text-xs font-semibold text-accent">Live call</div>
      <p className="text-sm text-white/70">
        {reason || "Hop on, share your screen, and I will talk through the change and build it live."}
      </p>
      {!room ? (
        <button
          onClick={join}
          disabled={busy}
          className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
        >
          {busy ? "Starting call" : "Join video call"}
        </button>
      ) : null}
      {err && <p className="mt-2 text-xs text-red-500">{err}</p>}
      {room && (
        <>
          <iframe
            src={room}
            allow="camera; microphone; fullscreen; display-capture; autoplay"
            className="mt-2 h-[55vh] w-full rounded-lg border border-white/10"
          />
          {report && onShared && (
            <button
              onClick={onShared}
              className="mt-2 rounded-lg border border-accent/40 px-4 py-2 text-sm font-medium text-accent hover:bg-accent/10"
            >
              I am sharing my screen, show me the fix
            </button>
          )}
        </>
      )}

      {links.length > 0 && (
        <div className="mt-3 border-t border-white/10 pt-2">
          <div className="mb-1.5 text-xs font-semibold text-white/70">Previews</div>
          <ul className="flex flex-col gap-2">
            {links.map((l, i) => (
              <li key={i} className="rounded-lg border border-white/10 bg-white/[0.02] p-2">
                {l.explanation && (
                  <p className="mb-1 text-xs text-white/70">{l.explanation}</p>
                )}
                <div className="flex flex-wrap gap-2">
                  {l.preview_url && (
                    <a href={l.preview_url} target="_blank" rel="noopener"
                       className="rounded-md bg-accent px-2.5 py-1 text-xs font-medium text-white hover:brightness-110">
                      Open preview
                    </a>
                  )}
                  {l.pr_url && (
                    <a href={l.pr_url} target="_blank" rel="noopener"
                       className="rounded-md border border-white/15 px-2.5 py-1 text-xs text-white/70 hover:text-white">
                      View PR
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
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

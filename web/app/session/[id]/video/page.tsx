"use client";

import { useEffect, useState } from "react";

// Live video + screen-share session. Creates a Daily room via the agent and
// embeds Daily Prebuilt (full video UI + a Screen Share button) in an iframe.
export default function VideoSession() {
  const [roomUrl, setRoomUrl] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/session-video", { method: "POST" })
      .then((r) => r.json())
      .then((d) => {
        if (d.room_url) setRoomUrl(d.room_url);
        else setError(d.error || "Could not start video session");
      })
      .catch(() => setError("Agent unreachable"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="flex min-h-screen flex-col">
      <header className="border-b border-white/10 px-6 py-3">
        <h1 className="text-sm font-semibold">
          Live session. <span className="text-accent-soft">screen share enabled</span>
        </h1>
        <p className="text-xs text-white/50">
          Both join, the customer shares their screen, TwoCustomer interviews + watches.
        </p>
      </header>
      <div className="flex-1">
        {loading && <div className="grid h-full place-items-center text-white/50">Starting room…</div>}
        {error && (
          <div className="grid h-full place-items-center text-center text-white/60">
            <div>
              <p>⚠ {error}</p>
              <p className="mt-1 text-xs text-white/40">Set DAILY_API_KEY on the agent to enable video.</p>
            </div>
          </div>
        )}
        {roomUrl && (
          <iframe
            src={roomUrl}
            allow="camera; microphone; fullscreen; speaker; display-capture"
            className="h-full w-full border-0"
            title="Live session"
          />
        )}
      </div>
    </main>
  );
}

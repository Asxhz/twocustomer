"use client";

import { useCallback, useRef, useState } from "react";
import ChatThread from "@/components/ChatThread";
import VoiceButton from "@/components/VoiceButton";

export default function VoiceSession({ voice }: { voice: boolean }) {
  const [transcript, setTranscript] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [callUrl, setCallUrl] = useState<string | null>(null);
  const [callBusy, setCallBusy] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Speak the agent's reply aloud (Deepgram TTS) so it's a real voice agent.
  const speak = useCallback(async (text: string) => {
    if (!voice) return;
    try {
      setSpeaking(true);
      const r = await fetch("/api/voice/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!r.ok) return;
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        await audioRef.current.play().catch(() => {});
      }
    } finally {
      setSpeaking(false);
    }
  }, [voice]);

  async function startCall() {
    setCallBusy(true);
    try {
      const r = await fetch("/api/session-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "customer interview" }),
      });
      const d = await r.json();
      if (d.room_url) {
        setCallUrl(d.room_url);
        window.open(d.room_url, "_blank", "noopener");
      }
    } finally {
      setCallBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        {voice && (
          <>
            <VoiceButton onTranscript={setTranscript} />
            <span className="text-xs text-white/40">
              {speaking ? "Agent speaking…" : transcript ? "Review and send" : "Tap to answer by voice"}
            </span>
          </>
        )}
        <button
          onClick={startCall}
          disabled={callBusy}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:border-accent/50 disabled:opacity-50"
        >
          {callBusy ? "Starting…" : "🎥 Video call + screen share"}
        </button>
      </div>

      {callUrl && (
        <iframe
          src={callUrl}
          allow="camera; microphone; fullscreen; display-capture; autoplay"
          className="h-[55vh] w-full rounded-xl border border-white/10"
        />
      )}

      <ChatThread injected={transcript} onAssistant={speak} />
      {/* hidden player for agent TTS */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}

"use client";

import { useRef, useState } from "react";

// Records mic audio, posts it to /api/voice (Deepgram STT), and hands the
// transcript back. Degrades gracefully when mic or Deepgram is unavailable.
export default function VoiceButton({
  onTranscript,
}: {
  onTranscript: (text: string) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = (e) => chunksRef.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setBusy(true);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        try {
          const res = await fetch("/api/voice", {
            method: "POST",
            headers: { "Content-Type": "audio/webm" },
            body: blob,
          });
          const data = await res.json();
          if (data.transcript) onTranscript(data.transcript);
        } finally {
          setBusy(false);
        }
      };
      rec.start();
      recRef.current = rec;
      setRecording(true);
    } catch {
      onTranscript("(microphone unavailable)");
    }
  }

  function stop() {
    recRef.current?.stop();
    setRecording(false);
  }

  return (
    <button
      onClick={recording ? stop : start}
      disabled={busy}
      className={
        recording
          ? "rounded-lg bg-red-500 px-3 py-2 text-sm font-medium text-white"
          : "rounded-lg border border-white/15 px-3 py-2 text-sm font-medium disabled:opacity-50"
      }
      title="Voice (Deepgram)"
    >
      {busy ? "…" : recording ? "■ Stop" : "🎙 Speak"}
    </button>
  );
}

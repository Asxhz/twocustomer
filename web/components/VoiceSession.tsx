"use client";

import { useState } from "react";
import ChatThread from "@/components/ChatThread";
import VoiceButton from "@/components/VoiceButton";

export default function VoiceSession({ voice }: { voice: boolean }) {
  const [transcript, setTranscript] = useState("");
  return (
    <div className="flex flex-col gap-3">
      {voice && (
        <div className="flex items-center gap-3">
          <VoiceButton onTranscript={setTranscript} />
          <span className="text-xs text-white/40">
            {transcript ? "Transcript loaded — review and send" : "Tap to answer by voice"}
          </span>
        </div>
      )}
      <ChatThread injected={transcript} />
    </div>
  );
}

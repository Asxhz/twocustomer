// Client + server helpers for talking to the TwoCustomer agent control plane.

export const AGENT_BASE_URL =
  process.env.AGENT_BASE_URL || "http://localhost:8000";

// Server-side headers for agent calls — attaches the shared bearer token when set.
export function agentHeaders(
  extra: Record<string, string> = {},
): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  const tok = process.env.AGENT_SHARED_TOKEN;
  if (tok) h["Authorization"] = `Bearer ${tok}`;
  return h;
}

export type ChatEvent =
  | { event: "tool_end"; data: { name: string; output: string } }
  | { event: "message"; data: { text: string; rounds: number } }
  | { event: "done"; data: Record<string, never> };

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// Parse an SSE text stream into typed events, invoking onEvent per event.
export async function readSSE(
  res: Response,
  onEvent: (evt: { event: string; data: string }) => void,
): Promise<void> {
  const reader = res.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) onEvent({ event, data });
    }
  }
}

// Pure SSE block parser, factored out so it's unit-testable without a Response.

export interface SSEEvent {
  event: string;
  data: string;
}

// Parse a buffer of "event:/data:" blocks separated by blank lines.
// Returns parsed events plus the trailing partial block (not yet terminated).
export function parseSSEBuffer(buffer: string): {
  events: SSEEvent[];
  rest: string;
} {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: SSEEvent[] = [];
  for (const block of blocks) {
    let event = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (data) events.push({ event, data });
  }
  return { events, rest };
}

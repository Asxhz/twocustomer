import { describe, expect, it } from "vitest";
import { parseSSEBuffer } from "../lib/sse";
import { INTEGRATIONS } from "../lib/mock";

describe("parseSSEBuffer", () => {
  it("parses complete event blocks and keeps the trailing partial", () => {
    const buf =
      "event: tool_end\ndata: {\"name\":\"echo\"}\n\n" +
      "event: message\ndata: {\"text\":\"hi\"}\n\n" +
      "event: done\ndata: ";
    const { events, rest } = parseSSEBuffer(buf);
    expect(events).toHaveLength(2);
    expect(events[0].event).toBe("tool_end");
    expect(events[1].data).toContain("hi");
    expect(rest).toContain("done");
  });

  it("defaults event name to message", () => {
    const { events } = parseSSEBuffer("data: {\"text\":\"x\"}\n\n");
    expect(events[0].event).toBe("message");
  });
});

describe("integrations data", () => {
  it("lists the sponsor platforms", () => {
    const names = INTEGRATIONS.map((i) => i.name);
    expect(names).toContain("Anthropic Claude");
    expect(names).toContain("Browserbase");
    expect(names.some((n) => n.includes("Fetch AI"))).toBe(true);
  });
});

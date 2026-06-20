# LLM layer

**Model:** `claude-sonnet-4-6` (Anthropic). Pinned via `ANTHROPIC_MODEL`.

Per the claude-api skill (2026):
- Adaptive thinking is the recommended on-mode (`thinking: {type: "adaptive"}`),
  but it's **off when omitted** on Opus 4.8. We omit `thinking` for the chat/monitor
  loop → lowest latency, and no thinking-block echo bookkeeping. Set `effort: medium`
  via `output_config` to balance quality/cost.
- **No** `temperature` / `top_p` / `top_k` (removed on 4.8 → 400).
- **No** `budget_tokens` (removed → 400).
- Stream for large `max_tokens`; our turns are small (`max_tokens=4096`) so
  `messages.create` is fine. `propose_fix` / long outputs should switch to `.stream()`.
- Tools use the Anthropic format `{name, description, input_schema}` — produced by
  `ToolRegistry.specs()`. Parse `tool_use` blocks; return `tool_result` blocks.

`base.py` is provider-agnostic so the loop runs on `StubLLM` (offline/tests) or
`ClaudeLLM` (live). `main.get_llm()` picks Claude when `ANTHROPIC_API_KEY` is set.

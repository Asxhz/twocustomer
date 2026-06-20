# Fetch AI · ASI:One — TwoCustomer uAgent

**Track:** Best Use of Fetch AI. **Goal:** an agent discoverable through ASI:One
that understands intent and takes real action — not a chatbot or API wrapper.

## What it does
`uagent/agent.py` is a Fetch AI **uAgent** speaking the **Chat Protocol**
(`uagents_core.contrib.protocols.chat`), published with `publish_manifest=True`
so it appears in Agentverse / ASI:One search. When a user messages it on ASI:One:

1. It **acknowledges** the message (chat-protocol requirement).
2. `intent.parse_intent()` maps the text → an action: `monitor` · `campaign` ·
   `interview` · `insights` · `status` · `help`.
3. `control_plane.handle()` drives the **TwoCustomer control plane** (the Claude
   tool-loop in `agent/`) to actually do the work — start monitoring a brand,
   build a campaign, run a customer interview, fetch insights.
4. It **replies** with the result.

So an ASI:One query like *"monitor Aurora Drinks and tell me what's leaking
revenue"* triggers a real monitoring + insight run, then returns the finding.

## Run
```sh
cd uagent
uv sync
export UAGENT_SEED="<stable seed phrase>"        # fixes the agent address
export AGENT_BASE_URL="http://localhost:8000"    # TwoCustomer control plane
export ASI_ONE_API_KEY=...  AGENTVERSE_API_KEY=...
uv run python agent.py        # prints the agent address, starts mailbox
```
Then register the printed address on Agentverse and connect it to ASI:One.

## Status
- ✅ Chat-protocol agent + intent parser (6/6 unit tests pass offline).
- ✅ Control-plane bridge (forwards intents → `/chat`, parses SSE reply).
- `[~]` Live runtime + Agentverse registration + ASI:One discovery: needs
  `UAGENT_SEED`, `AGENTVERSE_API_KEY`, and a funded control plane (Anthropic
  credits) to exercise end-to-end.

## Demo script (Fetch track)
1. Show the agent address + manifest published.
2. From ASI:One, search "TwoCustomer" → message *"monitor Aurora Drinks"*.
3. Agent acks, runs the monitor tool, replies with a live insight.
4. Show the same action reflected in the web dashboard `/admin`.

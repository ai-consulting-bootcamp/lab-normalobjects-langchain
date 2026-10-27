# NormalObjects Creative Complaint Handler

A bootcamp lab for **LAB | Chaos agent: tools, lore, questionable judgment.**
Four local tools supply fictional Hawkins records and clearly labeled comic advice.
The model chooses tools through LangChain's modern `create_agent` loop using
`ChatOpenAI(model="gpt-4o-mini", temperature=0.1)`.

## Setup

Use Python 3.11 or 3.12. From this directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` locally to set `OPENAI_API_KEY`. Do not paste your key into code,
screenshots, traces, or version control. A key must have model access and billing.
The application never prints the key; `.env` is ignored. API runs incur usage.

## Run

```bash
python normalobjects_langchain.py
python normalobjects_langchain.py --demo
python normalobjects_langchain.py --query "My lights keep flickering and I think there is a portal in my basement."
python normalobjects_langchain.py --demo --seed 42
python -m unittest -v
```

Interactive mode accepts `quit` or `exit`. Each complaint starts a fresh conversation.
The demo covers electricity/portal, monster delivery theft, and psychic interference.
Seeding makes local random draws reproducible for an identical tool-call sequence;
it does not guarantee identical model output or model tool choices.

## Workflow and evidence

Complaint → model → selected local tools → model answer → JSON trace → verification.
`AIMessage.tool_calls` supplies names, arguments, and call IDs. `ToolMessage`
supplies actual results and matching IDs. Streamed message states preserve completed
steps if a subsequent call fails. A graph recursion limit of 12 bounds the loop;
requests also have a timeout and limited retries. Errors save partial evidence with
the exception type, without printing provider exception details.

Each real execution creates `traces/trace_<UTC timestamp>_<unique suffix>.json`.
Review `tool_calls`, `tool_results`, `final_response`, and `verification` together.
`traces/example_trace.json` is an exact copy of the first recorded live execution,
including its grounding flag. It is not an additional independent run. Offline tests
use constructed messages and do not constitute live proof.

The record tool returns all matching topics, with stable HK IDs and exact sentences.
The other three tools label their output as improvisation. Matching uses whole words
and a small alias list, so unfamiliar wording can be missed. Spell levels are strictly
`low`, `medium`, or `high`; invalid levels raise `ValueError`.

Automated grounding checks inspect topic relevance, result capture, successful
results, quoted record sentences, and unreturned HK IDs. These checks cannot detect
all unsupported assertions, contradictions, or misleading paraphrases. Every answer
therefore remains `pending_human_review`, even when all automated checks pass.
For each demo, confirm that the appropriate HK records were actually requested and
returned, check every factual claim, and check labels on invented suggestions.

Trace files retain the complaint and response: use fictional sample complaints and
review traces before sharing. Never include credentials in a complaint.

## Submission status

See `lab_proof.md` for the real execution evidence, review of all three demos, and
unresolved topic-coverage and unsupported-addition problems. Automated passes do
not establish complete grounding. No reference
notebook or diagram file was present in the workspace. The implementation follows
the official [LangChain agent API](https://reference.langchain.com/python/langchain/agents/factory).
No deprecated executor or legacy agent factory is used.

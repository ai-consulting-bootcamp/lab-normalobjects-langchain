# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built

I built a small LangChain agent that handles goofy Upside Down complaints using four custom tools:

- `consult_demogorgon(complaint: str)`
- `check_hawkins_records(query: str)`
- `cast_interdimensional_spell(problem: str, creativity_level: str = "medium")`
- `gather_party_wisdom(question: str)`

The agent is created with `create_agent(...)` and a system prompt that requires tool use before answering and says the answer must come only from tool outputs. The notebook also includes a structured, non-agent comparison function that calls the same tools in a fixed order.

## 2. Query

I used this complaint from the notebook:

> "My Christmas lights keep flickering and I hear noises from the wall. What is going on?"

This is a good proof case because it triggers multiple tool calls and the final answer is a combination of tool results rather than the model inventing lore.

## 3. Tool evidence (calls + args + outputs)

The notebook logs the exact tool calls and outputs for this complaint:

```text
TOOL CALL: check_hawkins_records({'query': 'flickering lights'})
TOOL OUTPUT (check_hawkins_records): No record found for 'flickering lights'. Try: portal, monsters, psychics, or electricity.

TOOL CALL: consult_demogorgon({'complaint': 'flickering Christmas lights and noises from the wall'})
TOOL OUTPUT (consult_demogorgon): The Demogorgon tilts its petal-face at 'flickering Christmas lights and noises from the wall'. Interpreted as: 'turn off the lights'.
```

Additional tool evidence from the notebook shows the tool behavior in isolation:

```text
check_hawkins_records.invoke({"query": "What do we know about the Portal?"})
-> "Hawkins Lab records: A gateway to another dimension was opened beneath the lab. Status: unstable, do not approach."

cast_interdimensional_spell.invoke({"problem": "Demodogs in my garden", "creativity_level": "high"})
-> "Spell 3: Summon Eleven's focus and telekinetically fling 'Demodogs in my garden' away.\nSpell 1: Open a tiny portal and push 'Demodogs in my garden' through to the Upside Down.\n..."

gather_party_wisdom.invoke({"question": "what is the plan?"})
-> "The party huddles together, argues for a while, and concludes: 'We should probably ask Mike.'"
```

## 4. Final output

The agent produced this final answer for the complaint:

```text
The Hawkins National Laboratory records do not contain any information on flickering lights. However, the Demogorgon suggests that you "turn off the lights" in response to your situation with the Christmas lights and noises from the wall.

Tools used: check_hawkins_records, consult_demogorgon
```

This final answer is exactly the kind of answer the lab is trying to ground: the agent is not claiming any outside knowledge; it is summarizing results returned by its tools.

## 5. Trace (which claim comes from which tool output?)

The trace is direct:

- Claim: "The Hawkins National Laboratory records do not contain any information on flickering lights."
  - Source: `check_hawkins_records` output: `No record found for 'flickering lights'. Try: portal, monsters, psychics, or electricity.`

- Claim: "The Demogorgon suggests that you 'turn off the lights'..."
  - Source: `consult_demogorgon` output: `The Demogorgon tilts its petal-face ... Interpreted as: 'turn off the lights'.`

- Claim: "... in response to your situation with the Christmas lights and noises from the wall."
  - Source: the complaint text plus the `consult_demogorgon` complaint string passed to the tool: `'flickering Christmas lights and noises from the wall'`.

This shows the answer is grounded in inspectable tool evidence, not an unstated fact from the model’s general knowledge.

## 6. Failure or limitation (where can it give a plausible but unsupported answer?)

The main failure mode is that the creative tools are intentionally chaotic and sometimes humorous, so the agent can turn a playful or unreliable tool result into a serious-sounding answer.

Example risk:

- The Demogorgon tool returns highly stylized, metaphorical text such as "Interpreted as: 'turn off the lights'."
- A model can treat that output as if it were a literal recommendation rather than a joke or a loose interpretation.
- The notebook itself notes that creative agents can be flexible and readable but harder to trace.

Another limitation is that the tool `check_hawkins_records` only matches a small fixed dictionary (`portal`, `monsters`, `psychics`, `electricity`). If a complaint is about a different issue, the best it can do is return a generic "No record found..." message. That means the agent can still produce a plausible but incomplete answer when the system has no actual evidence for the question.

In short: the agent is good at staying within tool boundaries, but with chaotic tools it can still produce a response that sounds authoritative while actually being only a stylized interpretation or a missing-record result.

## 7. Agent vs. structured handler

The notebook compares the creative agent to a structured handler:

| Aspect | Agent | Structured handler |
| --- | --- | --- |
| Same tools every run? | No | Yes |
| Tool order predictable? | No | Yes |
| Can invent facts? | Yes | No |
| Easy to trace? | No | Yes |
| Best use case | Open-ended, varied complaints | Reliable, auditable answers |

The structured handler in the notebook does this in a fixed order:

```python
def structured_handler(complaint: str) -> str:
    records = check_hawkins_records.invoke({"query": complaint})
    wisdom = gather_party_wisdom.invoke({"question": complaint})
    spell = cast_interdimensional_spell.invoke(
        {"problem": complaint, "creativity_level": "low"}
    )
    return (
        f"RECORDS:\n{records}\n\n"
        f"PARTY WISDOM:\n{wisdom}\n\n"
        f"SPELL:\n{spell}"
    )
```

This is more repeatable and easier to audit because each output is explicit and ordered. The agent is more creative and adaptive, but that flexibility is exactly where plausible-but-unsupported answers can slip in.

Conclusion: the notebook demonstrates a successful proof-of-grounding workflow for a creative language-agent setup: one query, one explicit tool path, one final answer, and a clear explanation of where the answer can still become unreliable.
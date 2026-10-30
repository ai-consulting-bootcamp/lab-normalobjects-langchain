# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built

A **creative complaint handler** for NormalObjects: a LangChain agent (`create_agent`, `gpt-4o-mini`, `temperature=0.7`) that **chooses its own tools**, in any order, for each complaint.

```
complaint → agent (LLM) → picks tools (any order) → tool outputs → final answer
```

| Tool | What it returns | Reliable? |
|---|---|---|
| `consult_demogorgon(complaint)` | 1 of 3 random chaotic answers (`random.choice`) | ❌ Random, not facts |
| `check_hawkins_records(query)` | Record for a matching keyword (`portal`, `monsters`, `psychics`, `electricity`), else "No record found" | ✅ Facts, same answer every time |
| `cast_interdimensional_spell(problem, creativity_level)` | 1/2/3 random spells for low/medium/high (`random.sample`) | ❌ Fun, made-up |
| `gather_party_wisdom(question)` | Advice from Mike/Dustin/Lucas/Will for a matching topic (`plan`, `science`, `danger`, `upside down`), else a "huddle" fallback | ⚠️ Advice, not facts |

The **system prompt** forces at least one tool call, encourages creative tool combinations, says to use the records for facts and to answer **only** from tool results, and asks the agent to end with a `Tools used:` line. Each run uses `config={"recursion_limit": 10}`.

For comparison, I also built a **structured handler** (no LLM) that always calls records → party → spell (`low`) in a fixed order.

**Code:** [`normalobjects_langchain.ipynb`](normalobjects_langchain.ipynb) (notebook with outputs) and [`normalobjects_langchain.py`](normalobjects_langchain.py) (exported script)

## 2. Query

> "There is a weird portal in my basement. What's the plan?"

## 3. Tool evidence (calls + args + outputs)

Extracted from `results[1]["messages"]`:

```
👤 COMPLAINT: There is a weird portal in my basement. What's the plan?

🤖 AGENT CALLS: check_hawkins_records
   args: {'query': 'portal'}

🤖 AGENT CALLS: gather_party_wisdom
   args: {'question': 'What should I do about a weird portal in my basement?'}

🔧 TOOL RETURNED (check_hawkins_records):
   Record P-01: The portal in the Hawkins lab basement opened after a psychic experiment. It grows when electrical activity is high.

🔧 TOOL RETURNED (gather_party_wisdom):
   The party huddles in Mike's basement... and agrees: stay together, stay calm, and call Eleven.
```

**Tool order:** `check_hawkins_records → gather_party_wisdom`

## 4. Final output

> According to the official Hawkins records, portals can be quite unpredictable. Notably, Record P-01 indicates that a portal opened in the Hawkins lab basement after a psychic experiment, and they can grow when electrical activity is high.
>
> As for the advice from the party, they suggest that you should stay together and stay calm, and definitely call Eleven for help.
>
> Make sure to gather your friends and keep a close eye on that portal!
>
> Tools used: check_hawkins_records, gather_party_wisdom

## 5. Trace (which claim comes from which tool output?)

| Claim in the final answer | Source | Grounded? |
|---|---|---|
| "Portals can be quite unpredictable" | Not in any tool output | ❌ Invented |
| A portal opened in the Hawkins lab basement after a psychic experiment | `check_hawkins_records` → Record P-01 | ✅ |
| Portals grow when electrical activity is high | `check_hawkins_records` → Record P-01 | ✅ |
| Stay together, stay calm, call Eleven | `gather_party_wisdom` → huddle **fallback** | ✅ (but the fallback, not the real "plan" advice) |
| "Gather your friends and keep a close eye on that portal" | Not in any tool output | ⚠️ Invented (harmless, close to "stay together") |
| Tools used: check_hawkins_records, gather_party_wisdom | Matches the real tool calls | ✅ |

## 6. Failure or limitation (where can it give a plausible but unsupported answer?)

**Main failure: the agent rephrases the question, so the right answer is never found.**

The customer asked *"What's the plan?"*. The party tool has a `plan` record (Mike: *"We stick together, we make a plan at my basement, and nobody goes in alone."*). But the agent sent its **own wording** to the tool: *"What should I do about a weird portal in my basement?"*. The word "plan" was dropped, so the keyword search returned the generic huddle fallback. The final answer looks complete and confident, but it's based on the fallback, not the matching advice.

**Proof:** the structured handler sent the original complaint word for word and got Mike's plan advice:

```
2. PARTY WISDOM:
   Mike: 'We stick together, we make a plan at my basement, and nobody goes in alone.'
```

**Other failures I observed (Step 4):**

1. **Retrieval miss → "no record" although a record exists.** For *"My Christmas lights keep flickering and I hear noises from the wall"*, the agent said there are no records. But the `electricity` record says exactly this: *"Lights flicker and power fails when creatures from the Upside Down are nearby."* The keyword search only matches the exact word "electricity", so the most relevant fact was never found.
2. **Trusting the unreliable tool.** For the cat complaint (no record exists), the agent honestly said "no official records" ✅, but then called the Demogorgon's random answer *"turn off the lights"* possibly *"the key"*, although the prompt says the Demogorgon is not facts. It also added *"Cats are known for their mysterious ways"*, which no tool said.
3. **No facts at all.** For the Demodog complaint, the agent called **only** the spell tool. Its answer added invented effects (*"the lights will flicker in response, guiding you to the truth"*, *"a powerful force"*) that are not in the spell text.

**Why this happens:** the agent decides which tools to call and with which words, and `temperature=0.7` encourages creative wording. The prompt rule "answer ONLY from tool results" reduces invention but does not prevent it.

**Possible fixes:** pass the original complaint to the tools (or tell the agent to keep the customer's key words), use better search than exact keyword matching, lower the temperature, or use a fixed workflow (LangGraph) when facts matter.

## 7. Agent vs. structured handler

**Tool order per complaint (agent):**

```
Lights:  check_hawkins_records → consult_demogorgon → cast_interdimensional_spell
Portal:  check_hawkins_records → gather_party_wisdom
Demodog: cast_interdimensional_spell
Cat:     check_hawkins_records → consult_demogorgon → cast_interdimensional_spell

Counts: check_hawkins_records 3, cast_interdimensional_spell 3, consult_demogorgon 2, gather_party_wisdom 1
```

**Structured handler (same portal complaint):** always records → party → spell (`low`); returned Record P-01, Mike's plan advice, and one spell. Weakness: no understanding: it pastes the whole complaint into the spell text and would also miss the `electricity` record for the lights complaint.

| | Agent | Structured |
|---|---|---|
| Same tools every run? | No: each complaint got a different set (1 to 3 tools) | Yes: always records → party → spell |
| Tool order predictable? | No: the agent decides the order | Yes: fixed order |
| Can invent facts? | Yes: e.g. "portals can be quite unpredictable", and it treated the Demogorgon's random answer as "the key" | No: the output is only tool text, nothing added |
| Easy to trace? | Only by digging through messages (`tool_calls` + tool outputs) | Yes: every line comes from one named tool |
| Best for which client case? | Creative, friendly answers where small inventions are okay (e.g. a fun marketing chatbot) | Cases that need consistency and an audit trail (e.g. support, compliance) |

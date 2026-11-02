# Lab proof: NormalObjects Creative Complaint Handler (LangChain)

Proof comes from one saved run of [`normalobjects_langchain.ipynb`](./normalobjects_langchain.ipynb). The notebook's last section, "Evidence trace", prints the same traces shown here, and can be checked against each quote the cell outputs.

## 1. Workflow

```text
complaint -> create_agent (gpt-4o-mini + system prompt) -> picks tools -> tool output -> final answer
```

- **Agent:** `create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)` from `langchain.agents`, with tools built using `@tool` from `langchain_core.tools`.
- **Four tools**, each plain Python so every output traces to a hardcoded source:

| Tool | How it produces output |
|---|---|
| `consult_demogorgon` | `random.choice` over 3 fixed replies |
| `check_hawkins_records` | looks for a key (portal, monsters, psychics, electricity) inside the lowercased query; otherwise a "not found" message |
| `cast_interdimensional_spell` | `random.sample` of 1, 2 or 3 spells (low, medium, high), each embedding the problem |
| `gather_party_wisdom` | same keyword lookup, answers attributed to Mike, Dustin, Lucas, Will; otherwise a "huddle" fallback |

- **System prompt rules:** use tools, don't invent Hawkins facts, combine tools in any order, quote what tools returned, say so if a tool finds nothing.
- **Loop guard:** `recursion_limit=12` per run.
- **Model:** `gpt-4o-mini` (my project returned a 403 for `gpt-5.5`).
- **API key:** loaded from a git-ignored `.env`; `.env.example` shows the format.

## 2. Query

> There is a glowing portal in my garage and it keeps flickering my lights. Help!

## 3. Tool evidence

The agent made four tool calls (arguments chosen by the LLM, outputs returned by my code):

| # | Tool call | Raw tool output |
|---|---|---|
| 1 | `check_hawkins_records(query='glowing portal')` | `Record 011-A: Portals to the Upside Down open near the lab; they close when the gate is sealed.` |
| 2 | `check_hawkins_records(query='flickering lights')` | `No Hawkins record found for that query. The file may have been classified (or eaten).` |
| 3 | `consult_demogorgon(complaint='glowing portal in garage')` | `The Demogorgon opens its mouth, sighs through 5 rows of teeth, and slowly walks away from your complaint.` |
| 4 | `cast_interdimensional_spell(problem='glowing portal causing flickering lights in garage', creativity_level='high')` | Three spells: Gate Slam, Christmas Wall, Flickering Lights |

## 4. Final output

> **Glowing Portal**: Record 011-A confirms that portals to the Upside Down can indeed pop up near the lab and will close when sealed. [...]
> **Flickering Lights**: Unfortunately, there's no official record on flickering lights being directly linked to portals. However, it's likely they're just nervous about the portal's presence. [...]
> After consulting our chaotic friend the Demogorgon, who just sighed and walked away (classic), I decided to get creative with a few spells: **Spell of the Gate Slam**, **Spell of the Christmas Wall**, **Spell of Flickering Lights** [...]

Full text is in the notebook's "Evidence trace" cell.

## 5. Verification: tracing the answer to the evidence

| Claim in the final answer | Evidence |
|---|---|
| Portals "close when sealed" | Tool call 1, record 011-A |
| No record on flickering lights | Tool call 2 returned "not found" |
| The Demogorgon "sighed and walked away" | Tool call 3 |
| Three named spells | Tool call 4 |
| Flickering lights are "nervous about the portal's presence" | **No tool output supports this.** It is the model's own addition. |

Four of the five claims trace to a tool output. The fifth is a small unsupported flourish. It is harmless here, but it shows the agent mixes grounded and invented content in the same fluent paragraph.

## 6. Failure case: a keyword miss reported as "no record exists"

> My teenage daughter has psychic powers and keeps breaking the TV with her mind.

| Step | What happened |
|---|---|
| Tool call | `check_hawkins_records(query='psychic powers')` |
| Tool output | `No Hawkins record found for that query. The file may have been classified (or eaten).` |
| Final answer | "I checked Hawkins records, but no classified files could be found on psychic powers" |

**Why it failed:** `check_hawkins_records` has a record for `psychics` (Record 011-E, about Eleven), but it matches by checking whether the key appears inside the query (`key in query.lower()`). The query contains `psychic`, not `psychics`, so there is no match. The record exists; the lookup missed it.

**Why this matters for grounding:** the agent had no way to tell "no record exists" from "my keyword match failed". It reported the first, in confident prose. A reader of the final answer would believe Hawkins has nothing on psychics, which is false for this dataset. The answer sounds supported but isn't.

**Confirmed to be the tool, not the LLM:** a fixed pipeline with no LLM (notebook section 5.3) calls the same function and gets the same "No Hawkins record found" on this complaint.

I left this bug in on purpose, because the lab specifies substring matching and it makes a clear failure case. Possible fixes: stem or fuzzy-match the keywords, or have the tool say "no keyword match" instead of "no record".

Related, from the same run: for complaint 5 ("friends can't agree on a strategy"), no party key matched, so the tool returned the generic huddle line. In earlier runs the agent wrapped a paraphrase of that line in quotation marks as if it were a direct quote.

## 7. Analysis of agent behavior (Step 5)

Numbers are from this run (6 complaints, `test_results`).

**Tool usage (total calls):** `check_hawkins_records` 5, `consult_demogorgon` 4, `cast_interdimensional_spell` 3, `gather_party_wisdom` 3. All four tools were used.

**Chaining patterns:**

| # | Complaint topic | Chain |
|---|---|---|
| 1 | Portal in garage | records → records → Demogorgon → spell |
| 2 | Monsters stealing Eggos | Demogorgon → records |
| 3 | Psychic daughter | records → Demogorgon → party → spell |
| 4 | Neighbour's dog | records → Demogorgon → party → spell |
| 5 | Bike-trip strategy | party |
| 6 | Capital of France | none |

- Average chain length 2.5 (0 to 4). 5 distinct chains out of 6.
- The agent usually starts with `check_hawkins_records` (its first move in 3 of 6 complaints), then chains in whatever order suits the complaint.
- Off-topic input (complaint 6) got no tools and an in-character refusal.
- Chains differ from run to run. Earlier runs gave different orders and lengths for the same complaints.

**Comparison with a structured approach:** I built a fixed pipeline (records → party → one spell, no LLM) and ran it on the same complaints.

| | Creative agent | Structured pipeline / LangGraph |
|---|---|---|
| Who picks the tools | The LLM | The developer |
| Predictability | Different chain each run | Same steps every run |
| Off-topic input | Declined "capital of France" | Ran all three steps anyway |
| Failure visibility | Fluent prose can hide a tool miss (section 6) | Raw outputs shown |
| Cost | Several LLM calls per complaint | No LLM calls |

**When to use which:** freeform agents suit this lab's goal (entertaining, varied answers). When the order or the facts must be reliable (audits, compliance, fixed workflows), a structured workflow such as LangGraph is the safer choice.

## 8. Where the system could give a plausible but unsupported answer

1. **Keyword-match misses** reported as "no record found" (section 6).
2. **Model embellishment** mixed in with tool results (section 5, the "nervous" claim).
3. **Random tools** (`consult_demogorgon`, spells) return text with nothing to check against. The agent's paraphrase of them can drift from the original.

## 9. How to reproduce

1. Use an environment with Python 3.10+ (I used a conda env with `langchain` 1.4.7, `langchain-openai` 1.7.3).
2. `pip install langchain langchain-openai python-dotenv`
3. Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.
4. Run `normalobjects_langchain.ipynb` top to bottom. Outputs vary per run because the tools and the LLM are non-deterministic; the structure of the findings above should hold.

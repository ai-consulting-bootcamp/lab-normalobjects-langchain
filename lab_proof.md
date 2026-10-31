# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built

I built a creative complaint-handling AI agent in a Jupyter notebook using LangChain and an OpenAI chat model (`gpt-4o-mini`). The agent receives a complaint from the fictional NormalObjects universe and chooses which tools to call before writing its response. I implemented four tools:

- `consult_demogorgon`: returns a randomly selected, deliberately unreliable Demogorgon opinion.
- `check_hawkins_records`: searches a four-topic dictionary (`portal`, `monsters`, `psychics`, `electricity`) for a case-insensitive keyword match. If there is no match, it returns `No record found for this query.`
- `cast_interdimensional_spell`: selects one, two, or three fictional spells for `low`, `medium`, or `high` creativity, respectively.
- `gather_party_wisdom`: returns a predefined comment from Mike, Dustin, Lucas, or Will if the person's name occurs in the question; otherwise it returns a generic party-huddle message.

The system prompt instructs the agent to call at least one tool, use tool outputs as the basis for its answer, distinguish creative suggestions from records, and list the tools used. Unlike a fixed workflow, the agent decides which tools to use and in what order.

## 2. Query

I tested the agent on four complaints:

1. **Flickering lights:** “My Christmas lights keep flickering and I hear noises from the wall. What is going on?”
2. **Basement portal:** “There is a weird portal in my basement. What's the plan?”
3. **Homework and Demodog:** “A Demodog ate my homework. I need a creative solution, creativity level high!”
4. **Neighbor's cat:** “My neighbor's cat is acting weird. Is it from the Upside Down?”

Each complaint was passed to `agent.invoke(...)` with `config={"recursion_limit": 10}` to limit repeated tool-calling loops. The four result objects were saved in `results` for later inspection.

For the detailed evidence trace below, I selected **complaint 1**, about the flickering Christmas lights and noises from the wall.

## 3. Tool evidence (calls + args + outputs)

For **complaint 1**, the agent called these tools in this order:

**Call 1 — `check_hawkins_records`**

- Arguments: `{'query': 'flickering lights, noises from the wall'}`
- Tool output: `No record found for this query.`

**Call 2 — `consult_demogorgon`**

- Arguments: `{'complaint': 'Christmas lights flickering and noises from the wall'}`
- Observed tool output: `The Demogorgon sniffs 'Christmas lights flickering and noises from the wall' and roars. It seems... hungry, not helpful.`

The Demogorgon response is random, so rerunning the notebook may produce a different response.

### Tool usage across all four complaints

| Complaint | Observed tool-call order |
|---|---|
| 1 — Flickering lights | `check_hawkins_records` → `consult_demogorgon` |
| 2 — Basement portal | `check_hawkins_records` → `gather_party_wisdom` → `consult_demogorgon` |
| 3 — Demodog homework | `cast_interdimensional_spell` → `consult_demogorgon` |
| 4 — Neighbor's cat | `check_hawkins_records` → `consult_demogorgon` |

**Total tool calls across the four tests:**

| Tool | Calls |
|---|---:|
| `consult_demogorgon` | 4 |
| `check_hawkins_records` | 3 |
| `gather_party_wisdom` | 1 |
| `cast_interdimensional_spell` | 1 |
| **Total** | **9** |

These counts come from inspecting the saved AI messages' `.tool_calls`, rather than merely trusting the tool names listed in final responses.

## 4. Final output

For **complaint 1**, the final answer reported that it could not find a matching Hawkins record and that the Demogorgon had not offered useful guidance. It then suggested checking the Christmas lights' wiring, consulting an electrician, and watching for unusual occurrences. The answer ended by listing the tools used: `check_hawkins_records` and `consult_demogorgon`.

This is a **summary of the observed final answer**, not a verbatim transcript. The complete text remains in the notebook's saved `results[0]["messages"][-1].content` and should be consulted if an exact quotation is needed.

For **complaint 4**, about the neighbor's cat, the agent acknowledged that it had no specific Hawkins records connecting unusual cat behavior to the Upside Down. It nevertheless added general suggestions to observe the cat and its surroundings. This example is useful because it tests whether the agent admits missing evidence.

## 5. Trace (which claim comes from which tool output?)

| Claim or suggestion in the final answer to complaint 1 | Evidence source | Assessment |
|---|---|---|
| No matching Hawkins record was found | `check_hawkins_records` returned `No record found for this query.` | **Supported**, for the query the agent actually sent to the tool |
| The Demogorgon did not give useful advice | `consult_demogorgon` returned a response describing the Demogorgon as “hungry, not helpful” | **Supported** by the observed fictional tool output |
| Loose wiring might cause the lights to flicker | Neither tool supplied an electrical diagnosis | **Not grounded in these tool outputs**; plausible real-world advice but not verified by this lab's evidence |
| An electrician could investigate the issue | Neither tool recommended an electrician | **Additional advice**, not sourced from the tool outputs |
| Unusual occurrences might indicate supernatural interference | No Hawkins record was found, and the Demogorgon supplied no reliable evidence | **Speculative**, not established by the tools |

The key lesson is that **using tools does not automatically make the final answer evidence-grounded**. The final response must still be compared claim by claim with the actual returned text. A missing record does not prove that a phenomenon is impossible; it means the tool did not find a match for the supplied query.

## 6. Failure or limitation

The clearest limitation was that the agent produced plausible-sounding advice even when the tool results did not support it. In complaint 1, it recommended checking wiring and contacting an electrician, although the records tool returned no match and the Demogorgon supplied no relevant explanation. The recommendations may be sensible in ordinary life, but they are **not supported by the specific evidence collected in this run**.

Another limitation comes from the simple keyword-based records tool. It checks whether one of four dictionary keys appears in the query. The agent searched for `flickering lights, noises from the wall`, which does not contain the key `electricity`, even though the electricity record concerns flickering lights. Thus, `No record found` can reflect a **keyword mismatch**, not a complete absence of relevant records.

The tools also include intentionally fictional or unreliable content. Demogorgon opinions are random, and spells are creative suggestions rather than factual evidence. The system prompt requests grounded answers, but prompt instructions alone did not prevent unsupported additions.

**Possible improvement:** adjust the records lookup to recognize related terms such as `flickering lights` → `electricity`; require the agent to label unsupported suggestions explicitly; and check the final answer against tool outputs before presenting factual claims.

## 7. Agent vs. structured handler

I also implemented `structured_handler(complaint)`, which always calls the tools in this order, **without an LLM**:

1. `check_hawkins_records` with the complaint as the query.
2. `gather_party_wisdom` with the complaint as the question.
3. `cast_interdimensional_spell` with creativity set to `low`.

When tested on the basement portal complaint, the structured handler returned the portal record, the generic party-huddle response, and one randomly selected fictional spell. The **tool sequence is fixed**, even though the spell text may vary because the spell tool uses randomness.

| Question | AI agent | Structured handler |
|---|---|---|
| Same tools every run? | Not necessarily; depends on the complaint and agent decisions | Yes; the same three tools are always called |
| Tool order predictable? | No; observed orders varied | Yes: records → party → spell |
| Can invent facts? | Yes; the LLM can add claims not grounded in tool results | No LLM-generated claims, but the predefined spell suggestions are fictional |
| Easy to trace? | Requires inspecting tool calls, arguments, outputs, and final text | Easier because the sequence and output fields are explicit |
| Best client use case | Creative, flexible interactions where different tools may be appropriate | Controlled, repeatable processes where consistency and auditability matter |

**Conclusion:** Agentic tool selection is more flexible, but it needs careful evidence checks. A structured handler is more predictable and easier to audit, but it may call unnecessary tools and cannot adapt its sequence to the complaint.

---

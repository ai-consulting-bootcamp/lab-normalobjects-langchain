# Lab Proof: NormalObjects Creative Complaint Handler

Notebook: `Lab_normalobjects_langchain.ipynb` · Model: `gpt-4o-mini` (temperature 0.7) · Framework: LangChain `create_agent`

## 1. What I built

A LangChain agent that handles complaints for *NormalObjects*. The LLM decides which tools to call, in what order, and then writes an answer that should be based only on the tool outputs.

```
complaint → agent (LLM) → picks tools (any order) → tool outputs → final answer
```

**Tools**

| Tool | What it does |
|---|---|
| `consult_demogorgon(complaint)` | Returns one of 3 random, chaotic replies (provided) |
| `check_hawkins_records(query)` | Looks up 4 records (`portal`, `monsters`, `psychics`, `electricity`) by keyword, case-insensitive. Fallback: `"No record found ..."` |
| `cast_interdimensional_spell(problem, creativity_level)` | Maps `low/medium/high` → `1/2/3` and returns that many random spells (`random.sample`) |
| `gather_party_wisdom(question)` | Returns advice from Mike, Dustin, Lucas or Will if named. Fallback: generic "the party huddles..." answer |

**System prompt (rules)**

```text
1. Always call at least one tool before answering. Never answer without using a tool.
2. Be creative: combine several tools if they help (records for facts, party for advice, spells for solutions, Demogorgon for chaos).
3. Answer ONLY using information returned by the tools. Do not invent facts, records or names.
4. If a tool says "No record found", say clearly that no record exists. Do not make one up.
5. At the end of your answer, list the tools you used, like this:
   Tools used: tool_a, tool_b
```

**Agent**

```python
tools = [consult_demogorgon, check_hawkins_records, cast_interdimensional_spell, gather_party_wisdom]
agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)

result = agent.invoke(
    {"messages": [HumanMessage(content=complaint)]},
    config={"recursion_limit": 10},
)
```

Full code for every step is in the notebook.

## 2. Query

> My Christmas lights keep flickering and I hear noises from the wall. What is going on?

## 3. Tool evidence (calls + args + outputs)

From the Step 5b trace of `results[0]`:

| # | Tool call | Args | Output |
|---|---|---|---|
| 1 | `check_hawkins_records` | `{'query': 'electricity'}` | Record #004: Flickering lights and power surges happen when creatures from the Upside Down are close by. |
| 2 | `consult_demogorgon` | `{'complaint': 'Christmas lights flickering and noises from the wall.'}` | The Demogorgon ignores 'Christmas lights flickering and noises from the wall.' and walks back into the wall. Classic. |

Note: the agent did not pass the complaint text to the records tool. It chose the keyword `electricity` itself. The raw complaint contains no record key, so passing it directly would have returned "No record found".

## 4. Final output

> It seems that your flickering Christmas lights and the strange noises from the wall might be related to creatures from the Upside Down. According to Hawkins records, such flickering and power surges typically occur when these creatures are nearby.
>
> As for the Demogorgon, it humorously ignored your complaint and just walked back into the wall, which is quite classic behavior for it!
>
> Tools used: check_hawkins_records, consult_demogorgon

## 5. Trace (which claim comes from which tool output?)

| Claim in final answer | Source | Verdict |
|---|---|---|
| Flickering lights might be related to creatures from the Upside Down | Record #004 | From tool |
| ...and the noises from the wall are related too | Not in any output. Record #004 only covers flickering lights and power surges | Invented link (agent stretched the record to cover the noises) |
| Flickering and power surges occur when these creatures are nearby | Record #004 | From tool |
| The Demogorgon ignored the complaint and walked back into the wall, classic | `consult_demogorgon` output | From tool |
| "humorously" | Not in output | Style addition, not a fact |
| Tools used: check_hawkins_records, consult_demogorgon | Matches the actual calls in Step 5a | Correct |

**Tool usage across all 4 complaints (Step 5a)**

```
Complaint 1: check_hawkins_records → consult_demogorgon
Complaint 2: check_hawkins_records → gather_party_wisdom
Complaint 3: cast_interdimensional_spell
Complaint 4: check_hawkins_records → consult_demogorgon → gather_party_wisdom

check_hawkins_records: 3 · consult_demogorgon: 2 · gather_party_wisdom: 2 · cast_interdimensional_spell: 1
```

Every complaint used at least one tool, and the order changed per complaint.

## 6. Failure or limitation (where can it give a plausible but unsupported answer?)

**Failure: complaint 3, "A Demodog ate my homework... creativity level high!"**

The agent called `cast_interdimensional_spell` and got 3 spells back. The spell texts are fixed strings in the tool code, so it's easy to check what the agent added on top:

| Claim in final answer | In the spell text? |
|---|---|
| Shout "Code Red!" over channel 6 | Yes |
| "This will hopefully alert your friends for backup or distract the creature" | No, invented |
| Place a stack of waffles near it to distract it | Yes |
| "Demodogs have a soft spot for Eggo waffles" | No, an invented lore fact |
| String lights and ask it yes/no questions | Yes |
| "...possibly negotiate for the return of your homework" | No, invented |

So even with "answer ONLY from tool results" in the system prompt, the agent added plausible-sounding explanations that no tool returned. The output reads as grounded, but it isn't fully grounded. The system prompt reduces invention but doesn't prevent it.

**Other limitations seen**

- **Cat complaint (no record exists):** the agent correctly said there are no records about cats, so it did not invent a record. It still added advice that came from no tool ("chat with your neighbor about the odd behavior"). I only traced `results[0]` in detail, so I didn't print the exact args and output of the records call for this complaint.
- **Keyword matching is fragile:** `check_hawkins_records` uses a plain substring match. "monster" (singular) doesn't match `monsters`. Grounding depends on the LLM choosing the right keyword (it chose `electricity` in complaint 1). A wrong keyword means "No record found" even if a relevant record exists.
- **Randomness:** with temperature 0.7 and random tool outputs, the same complaint gives different tools and different answers on each run.

## 7. Agent vs. structured handler

`structured_handler(complaint)` always calls records → party → spell (`low`) and joins the outputs, with no LLM. Output for complaint 2:

```
RECORDS: Record #001: A portal to the Upside Down opened under Hawkins Lab in 1983. Closed, then reopened. Status: unstable.
PARTY: The party huddles in Mike's basement and agrees: stick together, grab the walkie-talkies, and don't trust the Demogorgon.
SPELL: Spell of Christmas Lights: string lights around 'There is a weird portal in my basement. What's the plan?' and ask it yes/no questions.
```

| | Agent | Structured |
|---|---|---|
| Same tools every run? | No. It picked 1 to 3 different tools per complaint | Yes, always the same 3 |
| Tool order predictable? | No | Yes: records → party → spell |
| Can invent facts? | Yes. It did in complaint 3 (Eggo "soft spot", negotiating) | No. Output is only tool text |
| Easy to trace? | Harder. Need to inspect the messages | Easy. Each line is labelled with its tool |
| Best for which client case? | Open-ended, creative complaints where a friendly, flexible answer matters more than strict accuracy | Standard complaints where consistency and an audit trail matter |

Trade-off seen in the runs: the structured handler can't adapt. It passed the full complaint sentence into the spell, which reads awkwardly, and it calls the party tool even when it adds nothing. The agent adapts (it chose the `electricity` keyword itself), but that same freedom is what lets it add unsupported claims.

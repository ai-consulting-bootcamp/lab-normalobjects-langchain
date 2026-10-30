# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built
A LangChain agent (`create_agent`, `gpt-4o-mini`, temperature 0.7) that handles strange complaints from Hawkins with 4 tools:

| Tool | What it does |
|---|---|
| `consult_demogorgon` | Random, unreliable opinion (1 of 3 sentences) |
| `check_hawkins_records` | Dictionary lookup: portal, monsters, psychics, electricity; fallback "No record found" |
| `cast_interdimensional_spell` | 1/2/3 random spells for low/medium/high creativity |
| `gather_party_wisdom` | Advice from Mike, Dustin, Lucas or Will; fallback: the whole party |

System prompt rules: always call at least one tool, combine tools creatively, use only information from tool results, say "No record found" honestly, treat the Demogorgon as chaos and not fact, and end with "Tools used: ...".

```python
tools = [consult_demogorgon, check_hawkins_records, cast_interdimensional_spell, gather_party_wisdom]
agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)
result = agent.invoke({"messages": [HumanMessage(content=complaint)]},
                      config={"recursion_limit": 10})
```

The tool calls were traced from `result["messages"]`: AI messages contain `.tool_calls`, and tool messages contain the outputs.

## 2. Query
> "A Demodog ate my homework. I need a creative solution, creativity level high!"

## 3. Tool evidence (calls + args + outputs)
```
CALL: consult_demogorgon          ARGS: {'complaint': 'A Demodog ate my homework.'}
CALL: cast_interdimensional_spell ARGS: {'problem': 'A Demodog ate my homework.', 'creativity_level': 'high'}

RESULT consult_demogorgon:
The Demogorgon tilts its petal-face at 'A Demodog ate my homework.'. Interpreted as: 'turn off the lights'.

RESULT cast_interdimensional_spell:
🎸 Play loud 80s music at 'A Demodog ate my homework.'. Upside Down creatures hate a good guitar solo.
📻 Tune a radio to static and whisper 'A Demodog ate my homework.' backwards three times.
🕯 Circle of Christmas lights: surround 'A Demodog ate my homework.' with blinking bulbs until it gets bored.
```

Tool order for all 4 complaints:

| # | Complaint | Real tool order |
|---|---|---|
| 1 | Flickering lights | check_hawkins_records → check_hawkins_records → consult_demogorgon |
| 2 | Portal in basement | check_hawkins_records → gather_party_wisdom |
| 3 | Demodog ate homework | consult_demogorgon → cast_interdimensional_spell |
| 4 | Neighbor's cat | check_hawkins_records → consult_demogorgon |

Total uses: records 4, demogorgon 3, party 1, spell 1. The agent's own "Tools used:" line matched the real trace in all 4 cases.

## 4. Final output
> To tackle the issue of your homework being devoured by a Demodog, I've consulted the Demogorgon, which whimsically suggests you should "turn off the lights." For a more creative fix, I recommend the following high-level interdimensional spell: 1. **Play loud 80s music**: Upside Down creatures, including Demodogs, are known to hate a good guitar solo, so cranking up some classic tunes might just scare it away. 2. **Tune a radio to static**: Whisper "A Demodog ate my homework." backwards three times. This could create a mystical distraction. 3. **Create a circle of Christmas lights**: Surround the area where the Demodog is with blinking bulbs. This should intrigue it and possibly make it lose interest in your homework. These combined approaches should help you reclaim your lost homework and keep those mischievous creatures at bay! Tools used: consult_demogorgon, cast_interdimensional_spell

## 5. Trace (which claim comes from which tool output?)
| Claim | Source |
|---|---|
| The Demogorgon suggests "turn off the lights" | ✅ consult_demogorgon |
| Upside Down creatures hate a good guitar solo | ✅ cast_interdimensional_spell |
| "including Demodogs", "might just scare it away" | ❌ added by the model |
| Whisper the problem backwards three times | ✅ cast_interdimensional_spell (word for word) |
| "This could create a mystical distraction" | ❌ added by the model |
| Surround with blinking bulbs | ✅ cast_interdimensional_spell |
| "intrigue it", "lose interest in your homework" | ❌ reworded and added |
| "help you reclaim your lost homework" | ❌ invented promise |
| Tools used: consult_demogorgon, cast_interdimensional_spell | ✅ matches the trace |

**Pattern:** every fact comes from a tool, but the model adds explanations and promises between the facts. Those additions make the answer convincing, and none of them are supported.

## 6. Failure or limitation
**Cat complaint:** "My neighbor's cat is acting weird. Is it from the Upside Down?" There is no record about cats.

> There are no records in Hawkins that specifically mention anything about cats, so I can't confirm if your neighbor's cat is linked to the Upside Down. However, the Demogorgon suggests that the cat's strange behavior could be related to turning off the lights. This chaotic opinion might imply that the cat is reacting to something unusual in its environment. If you suspect something more sinister, it might be worth investigating any unusual happenings around your neighbor's house.

- ✅ "No records about cats": from the records fallback. The agent did not invent a record.
- ✅ "Turn off the lights": from the Demogorgon's random output.
- ❌ "The cat is reacting to something unusual": the model turned a **random** tool output into a meaningful-sounding conclusion.
- ❌ "Investigate your neighbor's house": advice that no tool gave.

The answer follows the rules on the surface (it admits "no record" and calls the Demogorgon "chaotic"), but half of it is not supported by any tool. It is plausible, so a user would believe it. Prompt rules reduce invention but do not prevent it; only the trace shows it.

## 7. Agent vs. structured handler
`structured_handler(complaint)` always calls records → party → spell (low), without an LLM.

Test on the lights complaint: the text contains "lights", not "electricity", so the structured handler returned **"No record found"**. The agent called the records tool twice and got the electricity record ("Flickering lights mark activity from the Upside Down nearby").

| | Agent | Structured |
|---|---|---|
| Same tools every run? | No, different combinations per complaint | Yes, always the same 3 |
| Tool order predictable? | No, the LLM decides | Yes, fixed |
| Can invent facts? | Yes, it adds explanations and promises between tool facts | No, it only joins tool outputs word for word |
| Easy to trace? | Needs the message trace | Yes, the output is the trace |
| Best for which client case? | Open, varied requests where flexibility matters (e.g. creative support, research); needs human review | Regulated or repeatable processes where every answer must be auditable (e.g. complaints with legal relevance, compliance) |

**Conclusion:** the agent is smarter (it recovered from "No record found" by retrying with a better word), but less controllable. The structured handler is safe but rigid. A good middle ground for clients: let the agent choose tools, but show only tool outputs, or add a grounding check before the answer reaches the user.
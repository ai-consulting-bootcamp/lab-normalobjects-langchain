# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built

I built a LangChain tool-calling agent with four themed tools:

- `consult_demogorgon`: returns a random Demogorgon reaction.
- `check_hawkins_records`: searches four keyword-based Hawkins records.
- `cast_interdimensional_spell`: returns 1, 2, or 3 random solutions based on the creativity level.
- `gather_party_wisdom`: returns advice from Mike, Dustin, Lucas, or Will, with a party fallback.

The agent is required to call at least one tool and answer from tool results. It stores the complete message history so the tool calls and outputs can be inspected.

The sample complaints are run with:

```python
results = []
for complaint in complaints:
    result = agent.invoke(
        {"messages": [HumanMessage(content=complaint)]},
        config={"recursion_limit": 10},
    )
    results.append(result)
```

## 2. Query

> My Christmas lights keep flickering and I hear noises from the wall. What is going on?

## 3. Tool evidence

The tool-order analysis recorded this sequence for complaint 1:

```text
check_hawkins_records → check_hawkins_records → consult_demogorgon → cast_interdimensional_spell
```

The evidence trace showed these calls and outputs:

```text
TOOL CALL: check_hawkins_records
ARGS: {'query': 'electricity'}
TOOL OUTPUT (check_hawkins_records): Hawkins records link flickering lights and electrical surges to nearby Upside Down activity.

TOOL CALL: check_hawkins_records
ARGS: {'query': 'monsters'}
TOOL OUTPUT (check_hawkins_records): Hawkins records warn that monsters can cross from the Upside Down and are unusually active around fresh portal activity.

TOOL CALL: consult_demogorgon
ARGS: {'complaint': 'My Christmas lights keep flickering and I hear noises from the wall.'}
TOOL OUTPUT (consult_demogorgon): The Demogorgon sniffs 'My Christmas lights keep flickering and I hear noises from the wall.' and roars. It seems... hungry, not helpful.

TOOL CALL: cast_interdimensional_spell
ARGS: {'problem': 'flickering Christmas lights and noises from the wall', 'creativity_level': 'high'}
TOOL OUTPUT (cast_interdimensional_spell):
Summon a benevolent portal to relocate the problem: flickering Christmas lights and noises from the wall.
Enchant the nearest household object to distract the dimension from: flickering Christmas lights and noises from the wall.
Trade one embarrassing secret to the Upside Down in exchange for solving: flickering Christmas lights and noises from the wall.
```

## 4. Final output

```text
It seems that your Christmas lights flickering and the noises from the wall could be linked to nearby Upside Down activity, as noted in Hawkins records. Unfortunately, the Demogorgon was not very helpful, only expressing hunger!

Here are some creative solutions to address your issue:

1. **Summon a benevolent portal** to safely relocate the problem away from your home. This could help eliminate any negative energy causing the flickering.

2. **Enchant a household object** (like a broom or a pot) to distract the dimension from your home, allowing for a peaceful atmosphere.

3. **Trade one embarrassing secret** to the Upside Down in exchange for resolving the disturbances. This could be a quirky way to deal with the situation!

Choose one of these options, and may your home find peace from the flickering lights and mysterious noises!

Tools used: check_hawkins_records, consult_demogorgon, cast_interdimensional_spell
```

## 5. Trace: which claims are grounded?

| Final-answer claim | Evidence status |
|---|---|
| Flickering lights may be linked to nearby Upside Down activity | Grounded in the electricity record. |
| The Demogorgon was hungry and unhelpful | Grounded in the Demogorgon output. |
| Summon a portal, enchant an object, or trade a secret | Grounded in the three spell outputs. |
| The portal can safely relocate the problem | Partly invented; the tool only says it can relocate the problem, not that it is safe. |
| A broom or pot can be enchanted | Invented detail; the tool only says “nearest household object.” |
| These actions will eliminate negative energy or resolve the disturbances | Unsupported embellishment from the agent. |

The trace proves which tool outputs were available, but it also shows that the final LLM can add plausible details that were not explicitly returned by the tools.

## 6. Failure or limitation

The main grounding risk is that the agent can turn a vague tool suggestion into a more specific claim. For example, the spell tool suggests relocating the problem, but the final answer adds that this can be done “safely.” The system prompt asks the model to use only tool results, but the trace shows that prompt instructions are not a complete guarantee against unsupported elaboration.

Tool selection is also flexible and can vary between runs. In the recorded run, the four complaints used these tool orders:

```text
1. check_hawkins_records → check_hawkins_records → consult_demogorgon → cast_interdimensional_spell
2. check_hawkins_records → consult_demogorgon → cast_interdimensional_spell
3. cast_interdimensional_spell
4. check_hawkins_records → consult_demogorgon
```

## 7. Agent vs. structured handler

The agent uses an LLM to choose tools, decide their order, interpret results, and write a final response. This is useful for exploratory and creative complaints, but its behavior is less predictable and requires message-history tracing.

The structured handler makes direct calls in a fixed order:

```text
complaint → check_hawkins_records → gather_party_wisdom → cast_interdimensional_spell(low)
```

It does not use an LLM; it simply combines the three tool outputs. This makes its routing and grounding easier to audit, but it always runs the same tools and does not synthesize a polished conversational answer. It is better suited to predictable, auditable workflows.

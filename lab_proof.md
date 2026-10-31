# LAB Proof — NormalObjects Creative Complaint Handler

**Project:** LangChain Integration — Chaos Agent  
**Notebook:** `normalobjects_langchain.ipynb`  
**Framework:** LangChain  
**Model:** OpenAI GPT-4o-mini  
**Status:** Implementation and testing completed

---

## 1. Learning Objective

The goal of this lab was to build a creative complaint-handling agent using LangChain and verify whether its responses were grounded in inspectable tool evidence.

The agent operates in the fictional *Stranger Things* universe and handles unusual complaints from Hawkins residents.

The implementation demonstrates:

- Creating custom LangChain tools using the `@tool` decorator.
- Building an autonomous agent with `create_agent()`.
- Allowing an LLM to select tools and generate their input arguments.
- Tracking tool execution and inspecting returned evidence.
- Identifying retrieval failures and unsupported claims.
- Comparing an autonomous agent with a structured Python workflow.

The primary objective was not just to generate successful responses, but to demonstrate that the relationship between user input, tool execution, and final output can be inspected and evaluated.

## 2. Implementation and Workflow

### Environment

The project was implemented in a Jupyter Notebook using Python and the following packages:

- `langchain`
- `langchain-openai`
- `python-dotenv`

The OpenAI API key was loaded through a `.env` file, which is excluded from version control using `.gitignore`.

The language model was initialized using `init_chat_model()` with `gpt-4o-mini` and a temperature of `0.7`.

### Custom Tools

Four custom tools were implemented and individually tested before being integrated into the agent.

| Tool | Functionality |
|---|---|
| `consult_demogorgon` | Returns one randomly selected humorous response to a complaint |
| `check_hawkins_records` | Searches four predefined records using keyword matching |
| `cast_interdimensional_spell` | Generates 1–3 randomly selected magical solutions depending on the creativity level |
| `gather_party_wisdom` | Returns advice from Mike, Dustin, Lucas, or Will based on keyword matching |

The tools were registered using LangChain's `create_agent()` function.

The system prompt instructed the agent to use at least one tool, select tools dynamically, base its answers on tool results, acknowledge missing information, and list the tools used.

### Workflow

1. The user submits a complaint.
2. The LLM analyzes the complaint and selects appropriate tools.
3. LangChain executes the selected tools.
4. Tool outputs are returned to the model.
5. The model generates a final response.
6. The complete message history is stored for analysis.
7. Tool calls and outputs are extracted to verify the response.

The agent was invoked using the following structure:

```python
result = agent.invoke(
    {"messages": [HumanMessage(content=complaint)]},
    config={"recursion_limit": 10}
)
```

The `recursion_limit` parameter was used to limit graph execution steps.

## 3. Proof of Execution — Query, Evidence, and Final Output

The first test was selected as the primary evidence example because it demonstrates both successful tool execution and a grounding limitation.

### User Query

> My Christmas lights keep flickering and I hear noises from the wall. What is going on?

### Actual Tool Evidence

**Tool 1: `check_hawkins_records`**

Input:

```python
{"query": "Christmas lights flickering"}
```

Output:

```text
No record found for this query.
```

**Tool 2: `consult_demogorgon`**

Input:

```python
{"complaint": "noises from the wall"}
```

Output:

```text
The Demogorgon tilts its petal-face at 'noises from the wall'. Interpreted as: 'turn off the lights'.
```

Both tool calls were confirmed through the actual LangChain message history.

### Final Agent Response

> Ah, the classic flickering Christmas lights and mysterious wall noises combo – a true Hawkins holiday special! 🎄✨ Unfortunately, it appears that Hawkins records have no clue about your flickering lights. Maybe they were too busy documenting the latest Upside Down escapades?
>
> As for the noises from the wall, the Demogorgon has weighed in with its unique perspective: “Turn off the lights.” It seems even our favorite interdimensional monster knows when to save on electricity!
>
> So, the best advice? Try switching off those lights and see if the wall settles down. If the noises persist, you might want to consider calling a ghostbuster... or a good old-fashioned carpenter!
>
> Tools used:
> 1. check_hawkins_records
> 2. consult_demogorgon

### Evidence Verification

| Agent Statement | Evidence | Assessment |
|---|---|---|
| Hawkins search returned no information | Tool 1 returned no record | Supported for this specific query |
| Demogorgon suggested turning off the lights | Tool 2 explicitly returned this suggestion | Supported |
| Switching off the lights might stop the noises | No supporting tool evidence | Unsupported inference |
| A ghostbuster or carpenter could help | Not mentioned in tool results | Unsupported recommendation |
| Demogorgon wants to save electricity | Not mentioned in tool results | Humorous invention |

**Verification result:** The agent successfully executed the tools and incorporated their results, but its final answer was only partially grounded.

The tool trace demonstrated that a technically successful agent execution does not necessarily produce a fully evidence-supported response.

## 4. Additional Test Results

Four complaints were tested in total.

| Test | Complaint | Tools Used | Main Finding |
|---|---|---|---|
| 1 | Flickering Christmas lights | Hawkins Records, Demogorgon | Relevant information was missed due to keyword matching |
| 2 | Portal in the basement | Hawkins Records, Demogorgon, Party Wisdom | Agent introduced unsupported solutions |
| 3 | Demodog ate homework | Interdimensional Spell | Correct tool selection and `high` creativity parameter |
| 4 | Neighbor's unusual cat | Demogorgon, Hawkins Records | Agent recognized missing information but generated speculative explanations |

### Tool Usage Statistics

Across the four test cases, the agent executed eight tool calls.

| Tool | Total Calls |
|---|---:|
| `check_hawkins_records` | 3 |
| `consult_demogorgon` | 3 |
| `gather_party_wisdom` | 1 |
| `cast_interdimensional_spell` | 1 |
| **Total** | **8** |

Every test triggered at least one tool call.

The agent demonstrated flexible tool selection, using different combinations depending on the complaint.

The third test also demonstrated successful structured argument generation: the agent correctly selected `cast_interdimensional_spell` with `creativity_level="high"`, which returned three distinct spells.

However, additional tool calls did not consistently improve the grounding of the final responses.

## 5. Failure Modes and Limitations

### Limitation 1 — Keyword-Based Retrieval

The Hawkins Records tool uses basic substring matching.

In Test 1, the agent searched for:

```text
Christmas lights flickering
```

However, the records contain an `electricity` entry describing unusual electrical disturbances.

Because the search query did not contain the exact keyword `electricity`, the relevant record was not retrieved.

This demonstrates a retrieval failure caused by a mismatch between the user's language and the structure of the available knowledge.

**Possible improvement:** Introduce semantic retrieval, synonyms, or LLM-based query rewriting.

### Limitation 2 — Unsupported Generation

The system prompt explicitly instructed the agent to base its answers only on tool outputs.

Despite this instruction, several responses included additional recommendations or explanations that were not supported by the returned evidence.

Examples included:

- Using duct tape or holy water to seal a portal.
- Consulting a ghostbuster or carpenter about wall noises.
- Speculating about interdimensional catnip or psychic abilities.

These examples demonstrate that prompt instructions alone do not guarantee strict grounding.

**Possible improvement:** Introduce structured responses with explicit evidence references and a validation step that checks claims against the corresponding tool outputs.

### Limitation 3 — Tool Input Selection

In Test 2, the agent called `gather_party_wisdom` without including a specific party member's name in its query.

The tool therefore returned its generic fallback.

This demonstrates that successful tool selection does not automatically guarantee appropriate tool arguments.

**Possible improvement:** Improve tool descriptions and define stricter input schemas.

## 6. Agent vs. Structured Workflow

A second implementation, `structured_handler()`, was created to compare autonomous tool selection with a fixed execution sequence.

The structured handler always:

1. Searches Hawkins Records.
2. Requests Party Wisdom.
3. Generates one spell using `creativity_level="low"`.
4. Combines the returned results without additional LLM generation.

### Observed Structured Handler Output

For the basement portal complaint, the structured handler returned:

```text
Hawkins Records: Hawkins Lab reports unstable portals connecting our world to the Upside Down.

Party Wisdom: The party huddles together but cannot agree on a specific solution.

Magical Solution: Summon a magical storm to neutralize 'There is a weird portal in my basement. What's the plan?'.
```

### Comparison

| Criteria | LangChain Agent | Structured Handler |
|---|---|---|
| Tool selection | Dynamic | Fixed |
| Tool sequence | Model-dependent | Predictable |
| Tool arguments | Generated by LLM | Defined in Python |
| Flexibility | High | Limited |
| Traceability | Requires inspection of execution history | Directly inspectable |
| LLM API costs | Yes | None during execution |
| Risk of additional LLM-generated claims | Present | Absent |
| Output consistency | Variable | Fixed structure, potentially variable tool results |

The structured workflow was easier to inspect and avoided additional LLM-generated claims.

However, it was less flexible because it executed the same tools regardless of the user's complaint.

The output was not entirely deterministic because the spell tool still used random selection.

## 7. Key Learnings

This lab demonstrated that an autonomous LangChain agent can dynamically select tools, generate structured arguments, and combine multiple tool results.

However, three aspects must be evaluated separately:

**Tool execution:** Did the requested function run successfully?

**Retrieval quality:** Did the tool return the information needed to answer the question?

**Answer grounding:** Does the final response accurately reflect the returned evidence without introducing unsupported claims?

The experiments showed that successful tool execution does not guarantee successful retrieval or fully grounded output.

They also demonstrated that structured workflows can be a better choice when predictability, auditability, and cost efficiency are more important than autonomous decision-making.

## 8. Conclusion

The NormalObjects Creative Complaint Handler was successfully implemented using LangChain and four custom tools.

All four test queries completed, and the agent performed eight confirmed tool calls.

The experiments demonstrated successful tool integration, dynamic tool selection, parameter handling, and traceable execution.

At the same time, the evaluation identified retrieval limitations, unsuitable tool arguments, and unsupported generation.

**Final conclusion:** A working AI agent is not automatically a reliable or grounded AI agent. Reliable applications require explicit evidence inspection, appropriate retrieval methods, and validation of generated answers.

The complete implementation and additional test outputs are available in `normalobjects_langchain.ipynb`.
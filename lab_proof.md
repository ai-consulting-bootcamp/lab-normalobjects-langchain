# Lab Proof: NormalObjects Creative Complaint Handler (LangChain)

**Entry point for the reviewer.**

| File | Role |
|---|---|
| [normalobjects_langchain.ipynb](normalobjects_langchain.ipynb) | Repo notebook with the saved outputs used below. |
| [normalobjects_langchain.py](normalobjects_langchain.py) | Tool and agent implementation; the requested normal_objects.py is absent. |
| [app.py](app.py) | Gradio Complaint Desk. |
| [lab_proof.md](lab_proof.md) | Reviewer entry point. |

Source note: the repo does not contain Lab_normalobjects_langchain_explained.ipynb, Lab_normalobjects_langchain_ayhan.ipynb, normal_objects.py, or new lab.pdf. The saved evidence below comes from the repo's normalobjects_langchain.ipynb. No PDF text was available to extract, and the Ayhan notebook was not run.

## 1. What I built

The notebook creates a LangChain agent with create_agent, gpt-4o-mini at temperature 0.7, four tools, and a grounding system prompt. Invocations set recursion_limit to 10; the agent can choose tools in any order.

~~~mermaid
flowchart TD
    A([Resident complaint]) --> B["app.py (Gradio) or normalobjects_langchain.py"]
    B --> C["agent.invoke / stream<br/>recursion_limit = 10"]
    C --> D{"LLM picks tools<br/>prompt: only tool facts"}
    D -->|tool calls, any order| E["Tools node"]
    E --> T1["consult_demogorgon<br/>random opinion / LLM in E2"]
    E --> T2["check_hawkins_records<br/>4 records or 'No record found'"]
    E --> T3["cast_interdimensional_spell<br/>1 to 3 spells"]
    E --> T4["gather_party_wisdom<br/>4 topics or huddle"]
    T1 & T2 & T3 & T4 --> F["ToolMessages<br/>the only evidence"]
    F --> D
    D -->|no more tool calls| G["Final answer<br/>bullets + [tool_name] + Tools used"]
    G --> H["Verify: pair calls and outputs by tool_call_id"]
    H --> I["Claim check: FROM TOOL / NOT ATTRIBUTED"]
    I --> J([Case file + lab_proof.md])
    S["structured_handler<br/>records → party → spell low, no LLM"] -.->|comparison 5c and E5| J
~~~

| Tool | Source | Random or fixed | Holds facts? |
|---|---|---|---|
| consult_demogorgon | Three hardcoded chaotic replies | Random, random.choice | No; unreliable opinions |
| check_hawkins_records | Four topic-keyed records | Fixed; first matching key | Yes; record text |
| cast_interdimensional_spell | Four problem-specific spell templates | Random, random.sample | No; suggestions |
| gather_party_wisdom | Four topic-keyed party replies and a fallback | Fixed; first matching topic | No; advice |

Key code copied from the notebook:

~~~python
tools = [
    consult_demogorgon,
    check_hawkins_records,
    cast_interdimensional_spell,
    gather_party_wisdom,
]

agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)

result = agent.invoke(
    {"messages": [HumanMessage(content=complaint)]},
    config={"recursion_limit": 10},
)
~~~

~~~python
system_prompt = """You are the NormalObjects creative complaint handler.
Use the available tools creatively and in any order that helps. For every complaint,
make at least one tool call. Answer only from the results returned by tools. If a
record tool says 'No record found', say 'No record found' and do not invent a cause
or diagnosis. Treat the Demogorgon's opinion as an opinion, not verified evidence.
Write each factual or suggested claim as a short bullet and append the supporting
[tool_name]. Do not cite a tool unless its output supports that claim. End with a
' tools used:' line listing only tools actually called.""".replace("tools", "Tools")
~~~

## 2. Query

Complaint 1, the complaint traced in Step 5b:

~~~text
My Christmas lights keep flickering and I hear noises from the wall. What is going on?
~~~

## 3. Tool evidence (calls + args + outputs)

Step 5b pairs each call ID with its ToolMessage output.

| # | Tool | Call ID | Args | Output |
|---|---|---|---|---|
| 1 | check_hawkins_records | call_cY1gcJye6dFT0jMrXU1ulMZd | {'query': 'Christmas lights flickering'} | No record found for query: Christmas lights flickering |
| 2 | check_hawkins_records | call_7OfY0OTvFugpHZSIKUX83HuH | {'query': 'noises from wall'} | No record found for query: noises from wall |
| 3 | consult_demogorgon | call_WvxXSPoTZQv6keYz6jRdxS9K | {'complaint': 'My Christmas lights keep flickering and I hear noises from the wall.'} | The Demogorgon tilts its petal-face at 'My Christmas lights keep flickering and I hear noises from the wall.'. Interpreted as: 'turn off the lights'. |

## 4. Final output

~~~text
- There are no records found regarding Christmas lights flickering. [check_hawkins_records]
- There are no records found regarding noises from the wall. [check_hawkins_records]
- The Demogorgon suggests to "turn off the lights." [consult_demogorgon]

Tools used: check_hawkins_records, consult_demogorgon
~~~

## 5. Trace (which claim comes from which tool output?)

The first column copies the notebook's Claim attribution lines. I checked each claim against the paired output above.

| Claim | Cited tool | Tool output that supports it | Verdict |
|---|---|---|---|
| There are no records found regarding Christmas lights flickering. [check_hawkins_records] | check_hawkins_records | No record found for query: Christmas lights flickering | supported |
| There are no records found regarding noises from wall. [check_hawkins_records] | check_hawkins_records | No record found for query: noises from wall | supported |
| The Demogorgon suggests to "turn off the lights." [consult_demogorgon] | consult_demogorgon | The Demogorgon tilts its petal-face at 'My Christmas lights keep flickering and I hear noises from the wall.'. Interpreted as: 'turn off the lights'. | supported |

## 6. Failure or limitation

Complaint 4's saved answer:

~~~text
- The Demogorgon ignored the query about the cat and walked back into the wall, suggesting a lack of concern or information regarding the situation. [functions.consult_demogorgon]
- No record found for the query about a neighbor's cat acting weird. [functions.check_hawkins_records]

Tools used: functions.consult_demogorgon, functions.check_hawkins_records
~~~

The answer adds the interpretation “suggesting a lack of concern or information regarding the situation.” The paired Complaint 4 ToolMessages are [missing: Complaint 4's records and Demogorgon outputs; the notebook prints only Complaint 1's paired trace in Step 5b]. A separate direct tool test in the saved notebook returned:

~~~text
No record found for query: my neighbor's cat
~~~

That direct test is not Complaint 4's paired call. The saved Complaint 4 answer cites [functions.consult_demogorgon] and [functions.check_hawkins_records]. The claim checker looks for citations exactly matching [tool_name], so those functions-prefixed citations do not match its tool-name check.

The requested uncited spell lines for Complaint 1 are [missing: no spell claim appears in the saved Complaint 1 answer]. Its saved answer has two records claims and one Demogorgon suggestion, with no spell call.

The records matcher checks whether a stored key is a substring of the query. The saved key is “monsters”; the singular query “monster” does not contain that key, so it cannot match. [missing: saved output for check_hawkins_records with query “monster”]

## 7. Agent vs. structured handler

Step 5c comparison:

| | Agent | Structured |
|---|---|---|
| Same tools every run? | No; the model chooses tools for each complaint. | Yes; records, party, and spell run every time. |
| Tool order predictable? | No; order can vary. | Yes; records → party → spell. |
| Can invent facts? | It can still produce unsupported wording despite the prompt; inspect the trace. | No LLM is used, though tool text itself is limited to its hardcoded data. |
| Easy to trace? | Yes, if AI calls are matched to ToolMessages by call ID. | Yes; the fixed calls and returned values are explicit. |
| Best for which client case? | Open-ended complaints where varied suggestions are useful and reviewed. | Cases needing a predictable, repeatable sequence. |

Extension 5 measurements:

| Complaint | Agent time | LLM calls | Tool calls | Repeated calls | Tokens | Structured time | LLM calls | Tool calls | Repeated calls | Tokens |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| My Christmas lights keep flickering and I hear noises from the wall. What is going on? | 5.35s | 3 | 3 | 1 | {'input': 1189, 'output': 158, 'total': 1347} | 0.0012s | 0 | 3 | 0 | 0 (no LLM) |
| There is a weird portal in my basement. What's the plan? | 3.07s | 2 | 2 | 0 | {'input': 717, 'output': 122, 'total': 839} | 0.0006s | 0 | 3 | 0 | 0 (no LLM) |
| A Demodog ate my homework. I need a creative solution, creativity level high! | 3.69s | 2 | 1 | 0 | {'input': 724, 'output': 136, 'total': 860} | 0.0004s | 0 | 3 | 0 | 0 (no LLM) |
| My neighbor's cat is acting weird. Is it from the Upside Down? | 3.57s | 2 | 2 | 0 | {'input': 741, 'output': 147, 'total': 888} | 0.0004s | 0 | 3 | 0 | 0 (no LLM) |


## 8. Extensions

E2 output:

~~~text
Clearly, your bicycle bell is not malfunctioning; it’s actually a sentient being trying to communicate with you! It’s probably trying to warn you about an impending invasion of rogue squirrels planning to steal your snacks. Embrace the chaos—your bike is now a messenger of the animal kingdom!
~~~

E3 outputs:

~~~text
Red thread: You mentioned a complaint about your Christmas lights flickering.
Blue thread: You mentioned that a portal is in the basement, which seems to be a concern for you. Would you like to discuss it further?
~~~

E4 app.py shows one light for each tool plus an ANSWER light, a Demogorgon SVG loader, a case file with an evidence table, a claim check, a GROUNDED or CHECK BY HAND stamp, and session history. 

E5 measurements are in the table in Section 7.

## 9. Grounding self-review (prompt discipline)

Three grounding risks:

1. A substring-only record lookup misses singular/plural variants such as “monster” versus the saved “monsters” key. The matching rule is visible in the notebook code.
2. The model can add interpretations to a tool result. Complaint 4's saved answer adds “suggesting a lack of concern or information regarding the situation,” but its paired tool output is [missing: Complaint 4 ToolMessages].
3. The Complaint 4 citations have a functions. prefix. The app's claim checker compares citations against bare tool names, so the citation check cannot match those lines.

Two trace checks:

1. Step 5b pairs all three Complaint 1 calls to outputs using their call IDs.
2. Each of Complaint 1's three attributed claims is supported by its paired output, as shown in Section 5.

One simplification: the structured handler always calls records, party, then one low-creativity spell, with no agent LLM choosing the route.



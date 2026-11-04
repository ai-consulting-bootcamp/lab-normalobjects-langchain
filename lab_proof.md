# Lab proof: Creative Complaint Handler

## Implementation and execution

`normalobjects_langchain.py` uses LangChain's `create_agent`, model
`gpt-4o-mini`, and four custom tools: `consult_demogorgon`,
`check_hawkins_records`, `cast_interdimensional_spell`, and
`gather_party_wisdom`. The tools return hardcoded fictional records, advice,
or random humorous suggestions.

The system prompt describes a creative problem solver and sceptical rationalist.
It instructs the agent to evaluate tool outputs critically. The code makes all
four tools available without prescribing a sequence.

I captured a successful run on 4 November 2026 using the existing `bootcamp-env`
Python environment. The default Python environment lacked `langchain_openai`;
the successful run used:

```powershell
& 'C:\Users\tscho\miniconda3\envs\bootcamp-env\python.exe' normalobjects_langchain.py
```

The script now logs tool arguments, results, call IDs, and model-turn numbers.
It saves the query, assistant messages, tool calls, tool results, and final
output in `agent_trace.json`. Call IDs connect each result to its request.

## Query

> The portal in the basement keeps opening, and the lights flicker whenever it does. What should we do?

## Actual tool evidence

Model turn 1 requested these calls together:

- `check_hawkins_records({"query": "portal"})` ? ID `call_5yNyru7or3nKfEnNqIIQf7js`
- `check_hawkins_records({"query": "electricity"})` ? ID `call_Bc6OtpBaJvTT6AOCuxXxeCjM`

Result for `call_5yNyru7or3nKfEnNqIIQf7js`:

> Hawkins Lab opened a portal to the Upside Down beneath the town.

Result for `call_Bc6OtpBaJvTT6AOCuxXxeCjM`:

> Electrical disturbances often signal activity from the Upside Down.

## Actual final output

```text
It appears that the portal opening in the basement is linked to Hawkins Lab's history of opening a portal to the Upside Down. The flickering lights suggest that there could be electrical disturbances related to this interdimensional activity.

Here are some steps you might consider taking:

1. **Secure the Area**: Make sure the basement is secured and that no one enters it until you can fully assess the situation.

2. **Document the Activity**: Keep a log of when the portal opens and any related disturbances, including details about the flickering lights. This could help in understanding a pattern.

3. **Investigate Electrical Systems**: Check the electrical systems near the basement. There may be faulty wiring that is exacerbating the disturbances.

4. **Consult Experts**: If possible, reach out to experts in paranormal activity or professionals with experience dealing with the Upside Down.

5. **Create a Safety Plan**: Establish a plan for evacuation or safety in case the situation escalates.

Would you like further specific advice or recommendations on handling this situation?
```

## Step 5: Analyze agent behavior

### 1. Which tools were used?

The agent called `check_hawkins_records` twice, once with `portal` and once
with `electricity`. These inputs correspond to the basement portal and
flickering lights in the complaint. It did not call the Demogorgon, spell,
or party-wisdom tools in this run.

Using separate queries retrieved both relevant records. This avoided a
limitation of the tool: a single query containing both topic keywords would
return only the first matching record.

### 2. Tool chaining patterns

Both calls appear in the same assistant message, before either tool result.
They are independent requests: the electricity query was not generated after
reading the portal result. The trace therefore shows a batch of two lookups,
followed by synthesis, rather than a dependent chain of tools.

The observed pattern was:

```text
User complaint
  -> Model turn 1: request portal and electricity records
  -> Two tool results
  -> Model turn 2: final answer
```

There was no retry, further investigation, or call to a different tool after
receiving the results. The trace establishes the requests and their grouping;
it does not establish their exact wall-clock execution overlap or reveal the
model's internal reasoning.

The useful adaptation was splitting a complaint into two relevant searches.
This single run does not demonstrate creative chaining across different tools.

### 3. Comparison with a structured approach

A structured workflow could always retrieve the portal record, retrieve the
electricity record, and then ask the model to summarize both. For this complaint,
that would gather the same evidence as the observed agent, with a prescribed
sequence. It could also retrieve the records without a model choosing the calls.

The freeform agent selected the relevant searches itself and skipped the other
available tools. This flexibility is useful when complaints concern different
topics. A fixed workflow is more predictable and easier to inspect, but always
retrieving these two records would be unnecessary for some other complaints.

This is a conceptual comparison. I did not implement or benchmark a second
workflow, so I cannot claim measured differences in speed, cost, or accuracy.

## Grounding check and observed limitation

The answer's opening connects a portal with Hawkins Lab and flickering lights
with electrical disturbances. These statements can be traced to the two tool
results, within the lab's fictional setting.

However, the records do not establish that this particular basement portal
originated from Hawkins Lab, nor do they prove that the portal caused the lights
to flicker. The final answer makes that connection tentatively, using phrases
such as "It appears" and "could be", but does not explain the limited evidence.

The numbered recommendations are model-generated advice, not instructions
provided by the retrieved records. For example, the suggestion that faulty
wiring may exacerbate the disturbances is not supported by either tool result.
The recommendation to consult paranormal experts is also unsupported by the
records. These additions should be distinguished from retrieved evidence.

The agent did not use a spell in this run, but it accepted the fictional premise
and suggested paranormal experts without explicitly questioning the premise.
This shows that the sceptical persona alone did not ensure critical treatment
of all claims. The prompt influences behavior, while the code still permits all
four tools and does not enforce an evidence requirement for each recommendation.

The tools themselves are fictional hardcoded sources, not verification of
real-world supernatural claims. One run also cannot establish how consistently
the agent behaves: future runs may choose different calls or produce different
answers. The captured trace supports the observations above for this run only.

# Lab Proof: NormalObjects — Creative Complaint Handler (LangChain)

## 1. Architecture, Implementation & Execution Commands

This repository implements the **Department of NormalObjects (Becna's Helpline) Creative Complaint Handler** using the modern LangChain v1.x agent API (`from langchain.agents import create_agent`, `from langchain_openai import ChatOpenAI`, `from langchain_core.tools import tool`) and message primitives from `langchain_core.messages` (`AIMessage`, `HumanMessage`, `ToolMessage`).

### Repository Files & Pinned Environment
- [`normalobjects_langchain.py`](./normalobjects_langchain.py) — Core implementation:
  - **Step 2 (Creative Tools):**
    1. `consult_demogorgon(complaint: str) -> str` — selects 1 of 3 chaotic/humorous Upside Down perspectives embedding `complaint` via `random.choice()`.
    2. `check_hawkins_records(query: str) -> str` — performs case-insensitive substring matching across 4 topic-keyed records (`portal`, `monsters`, `psychics`, `electricity`) or returns a `"Record not found"` fallback message.
    3. `cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str` — maps `creativity_level` (`"low"` → 1, `"medium"` → 2, `"high"` → 3, default fallback → 2) and selects $N$ spell templates embedding `problem` via `random.sample()`.
    4. `gather_party_wisdom(question: str) -> str` — performs case-insensitive topic matching across 4 party member responses (`portal` → Mike, `monster` → Dustin, `lights` → Will, `defense` → Lucas) or returns an emergency `"huddle"` fallback.
  - **Step 3 (Agent with Tools & Loop Protection):** Lazy agent initialization (`build_complaint_agent`) using `create_agent(model=llm, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT)` and execution via `handle_complaint_with_agent(..., recursion_limit=10)` passing `config={"recursion_limit": 10}`.
  - **Step 4 & Step 5 (Trace Extraction, Multi-Complaint Evaluation & Structured Workflow):**
    - `extract_trace()` and `ToolUsageTracker` link `AIMessage.tool_calls` to `ToolMessage` strictly by `tool_call_id` and distinguish single-turn multi-tool emission (`is_parallel_call_in_turn`) from multi-turn sequential chaining (`ai_turn_index`).
    - `structured_handler(complaint: str)` executes a **fixed-order structured workflow without LLM**: `check_hawkins_records` → `gather_party_wisdom` → `cast_interdimensional_spell(problem=complaint, creativity_level="low")`.
- [`test_normalobjects_langchain.py`](./test_normalobjects_langchain.py) — 12 offline `unittest` tests covering all 4 tools, case-insensitivity, fallbacks (`"not found"` and `"huddle"`), spell creativity levels, fixed-order `structured_handler`, `tool_call_id` correlation, `recursion_limit` propagation, and error handling.
- [`requirements.txt`](./requirements.txt) — Pinned dependencies:
  ```text
  langchain==1.4.7
  langchain-openai==1.7.3
  langchain-core==1.7.3
  python-dotenv==1.2.4
  ```
- [`agent_eval_results.json`](./agent_eval_results.json) — Inspectable JSON artifact captured from a live run of `gpt-4o-mini` across all 4 sample complaints.

### Execution Commands

1. **Run offline unit tests (no API key or network required):**
   ```bash
   python -m unittest -v test_normalobjects_langchain.py
   ```
2. **Run local offline verification mode (direct tool checks, fallbacks, structured workflow, synthetic trace parser check):**
   ```bash
   python normalobjects_langchain.py --mode local
   ```
3. **Run live LangChain agent evaluation across the 4 sample complaints and export JSON trace:**
   ```bash
   python normalobjects_langchain.py --mode agent --json-output agent_eval_results.json
   ```

---

## 2. Multi-Complaint Evaluation, Turn Groupings & Aggregate Tool Usage

The live evaluation in [`agent_eval_results.json`](./agent_eval_results.json) (`model: "gpt-4o-mini"`, `recursion_limit: 10`) tested the 4 complaints from `SAMPLE_COMPLAINTS`.

### Summary of the 4 Live Agent Runs

| Run # | User Complaint | AI Tool Turns (`total_ai_tool_turns`) | Total Tool Calls (`total_tool_calls`) | Tool Call Grouping by Model Turn (`turns_summary` / `chaining_pattern`) | Tool Arguments Passed (`args`) |
|---|---|---|---|---|---|
| **1** | `"My Christmas lights keep flickering and I hear noises from the wall. What is going on?"` | 1 | 2 | **Turn 1:** `(check_hawkins_records + consult_demogorgon [same AI turn])` | 1. `check_hawkins_records({"query": "electricity"})`<br>2. `consult_demogorgon({"complaint": "flickering Christmas lights and noises from the wall"})` |
| **2** | `"There is a weird portal in my basement. What's the plan?"` | 2 | 3 | **Turn 1:** `(check_hawkins_records + gather_party_wisdom [same AI turn])`<br>**→ Turn 2:** `cast_interdimensional_spell` | **Turn 1:**<br>1. `check_hawkins_records({"query": "portal"})`<br>2. `gather_party_wisdom({"question": "What should we do about a portal in the basement?"})`<br>**Turn 2:**<br>3. `cast_interdimensional_spell({"problem": "weird portal in basement", "creativity_level": "medium"})` |
| **3** | `"A Demodog ate my homework. I need a creative solution, creativity level high!"` | 1 | 1 | **Turn 1:** `cast_interdimensional_spell` | 1. `cast_interdimensional_spell({"problem": "A Demodog ate my homework.", "creativity_level": "high"})` |
| **4** | `"My neighbor's cat is acting weird. Is it from the Upside Down?"` | 1 | 2 | **Turn 1:** `(consult_demogorgon + check_hawkins_records [same AI turn])` | 1. `consult_demogorgon({"complaint": "My neighbor's cat is acting weird. Is it from the Upside Down?"})`<br>2. `check_hawkins_records({"query": "cats from the Upside Down"})` |

### Aggregate Tool Usage Counts (`tracker_summary.aggregate_tool_counts`)

Across the 4 runs (8 total tool invocations):
- `check_hawkins_records`: **3** calls (Runs #1, #2, #4)
- `consult_demogorgon`: **2** calls (Runs #1, #4)
- `cast_interdimensional_spell`: **2** calls (Runs #2, #3)
- `gather_party_wisdom`: **1** call (Run #2)

### Methodological Note on Same-Turn Multi-Tool Calls vs. Sequential Chaining
When `is_parallel_call_in_turn=True` (denoted `[same AI turn]` in Runs #1, #2 Turn 1, and #4), it means the LLM emitted multiple entries inside a single `AIMessage.tool_calls` list during one reasoning step. The order of items inside that single `AIMessage.tool_calls` array only reflects the order in which the model listed them in one message — **it is NOT evidence of sequential step-by-step chaining (where tool B depends on the output of tool A), nor does it prove concurrent wall-clock execution**.

True **multi-turn sequential chaining** occurs only when the model inspects the `ToolMessage` results from Turn 1 and decides in a subsequent `AIMessage` (Turn 2) to invoke another tool. In [`agent_eval_results.json`](./agent_eval_results.json), **Run #2** demonstrates true multi-turn chaining:
- **Turn 1 (`ai_turn_index = 1`):** The model emitted `check_hawkins_records` and `gather_party_wisdom` in the same `AIMessage`.
- **Turn 2 (`ai_turn_index = 2`):** After receiving both `ToolMessage` outputs, the model issued a new `AIMessage` calling `cast_interdimensional_spell(problem="weird portal in basement", creativity_level="medium")`.

---

## 3. End-to-End Trace & Grounding Verification: Complaint #2 (Portal in the Basement)

### Input Query
```text
There is a weird portal in my basement. What's the plan?
```

### Step-by-Step Tool Execution Trace (from `agent_eval_results.json`)

| Call # | AI Turn (`ai_turn_index`) | `is_parallel_call_in_turn` | `tool_call_id` | Tool Name | Input `args` | Raw `ToolMessage` Output (`output`) |
|---|---|---|---|---|---|---|
| **1** | 1 | `true` | `call_EhvXmyDwgFGg670SzyTQjbej` | `check_hawkins_records` | `{"query": "portal"}` | `"Hawkins Record #HNL-01 (Portal): Interdimensional gates form where psychic trauma intersects with high-voltage electromagnetic fields. Standard containment requires sustained heat and sonic disruption."` |
| **2** | 1 | `true` | `call_bIpRzLG77yDIXKBoHKMHcJ9T` | `gather_party_wisdom` | `{"question": "What should we do about a portal in the basement?"}` | `"Mike says: 'Just like in our D&D campaign, a portal is a Vale of Shadows gate! We need a coordinated party plan—nobody goes into the basement alone, and keep your Supercomm on channel 3!'"` |
| **3** | 2 | `false` | `call_njfMjsZLZ1kWB8USWZHUnkqG` | `cast_interdimensional_spell` | `{"problem": "weird portal in basement", "creativity_level": "medium"}` | `"[Arcane Christmas-Light Faraday Cage] Wrap copper fairy lights counter-clockwise around the perimeter of 'weird portal in basement' and pulse Morse code S-O-S to neutralize spore interference.\n[Ritual of the Salt-Bath Resonance] Submerge a walkie-talkie tuned to Channel 7 near a kiddie pool of Epsom salt to invert the polarity of 'weird portal in basement'."` |

### Verbatim Final Output (`final_answer`)
```markdown
Dealing with a weird portal in your basement? Sounds like a classic Hawkins situation! Here’s a plan based on the findings:

### Findings from Hawkins Records
According to **Hawkins Record #HNL-01**, portals often form due to the intersection of psychic trauma and high-voltage electromagnetic fields. To contain these anomalies, you typically need sustained heat and sonic disruption.

### Party Wisdom
**Mike** suggests treating this like a D&D campaign: “No one goes in alone, and keep your Supercomm on channel 3!” This is a solid plan! Teamwork is essential.

### Creative Spell Solutions
Here are two spells you can cast to help manage that pesky portal:

1. **Arcane Christmas-Light Faraday Cage**: Wrap copper fairy lights counter-clockwise around the perimeter of the portal. Then, pulse Morse code S-O-S through the lights to neutralize any spore interference. It’s festive and functional!

2. **Ritual of the Salt-Bath Resonance**: Submerge a walkie-talkie tuned to Channel 7 in a kiddie pool filled with Epsom salt. This ritual will help invert the polarity of the portal, making it safer to handle.

### Final Plan
- Gather your friends (no solo adventures!).
- Set up the **Arcane Christmas-Light Faraday Cage** around the portal.
- Prepare the **Ritual of the Salt-Bath Resonance** with a kiddie pool and a walkie-talkie.

Follow these steps, and you should be well on your way to taming that mysterious portal! Good luck, and remember to stay safe!
```

### Claim-by-Claim Grounding Verification Table

The agent's response is **partially grounded** in the three tool outputs: while the core entities, record numbers, and spell names come from the `ToolMessage` evidence, the LLM introduced several subtle distortions, omissions, and unverified embellishments during synthesis:

| Claim in `final_answer` | Source `tool_call_id` & Tool | Raw Tool Evidence | Grounding Status & Distortion Analysis |
|---|---|---|---|
| *"According to **Hawkins Record #HNL-01**, portals often form due to the intersection of psychic trauma and high-voltage electromagnetic fields. To contain these anomalies, you typically need sustained heat and sonic disruption."* | `call_EhvXmyDwgFGg670SzyTQjbej` (`check_hawkins_records`) | `"Hawkins Record #HNL-01 (Portal): Interdimensional gates form where psychic trauma intersects with high-voltage electromagnetic fields. Standard containment requires sustained heat and sonic disruption."` | **Grounded:** Accurately cites record ID `#HNL-01`, formation cause, and containment requirements (`sustained heat and sonic disruption`). |
| *"**Mike** suggests treating this like a D&D campaign: “No one goes in alone, and keep your Supercomm on channel 3!”"* | `call_bIpRzLG77yDIXKBoHKMHcJ9T` (`gather_party_wisdom`) | `"Mike says: 'Just like in our D&D campaign, a portal is a Vale of Shadows gate! We need a coordinated party plan—nobody goes into the basement alone, and keep your Supercomm on channel 3!'"` | **Partially Grounded (Paraphrased as Direct Quote + Omission):** Formats a paraphrase (*“No one goes in alone...”*) inside quotation marks instead of the exact wording (*"nobody goes into the basement alone"*) and omits Mike's reference to the *"Vale of Shadows gate"*. |
| *"1. **Arcane Christmas-Light Faraday Cage**: Wrap copper fairy lights counter-clockwise around the perimeter of the portal. Then, pulse Morse code S-O-S through the lights to neutralize any spore interference. It’s festive and functional!"* | `call_njfMjsZLZ1kWB8USWZHUnkqG` (`cast_interdimensional_spell`) | `"[Arcane Christmas-Light Faraday Cage] Wrap copper fairy lights counter-clockwise around the perimeter of 'weird portal in basement' and pulse Morse code S-O-S to neutralize spore interference."` | **Grounded Core + Generative Flourish:** Core steps match the spell template, but *"It’s festive and functional!"* is an ungrounded editorial flourish added by the LLM. |
| *"2. **Ritual of the Salt-Bath Resonance**: Submerge a walkie-talkie tuned to Channel 7 in a kiddie pool filled with Epsom salt. This ritual will help invert the polarity of the portal, making it safer to handle."* | `call_njfMjsZLZ1kWB8USWZHUnkqG` (`cast_interdimensional_spell`) | `"[Ritual of the Salt-Bath Resonance] Submerge a walkie-talkie tuned to Channel 7 near a kiddie pool of Epsom salt to invert the polarity of 'weird portal in basement'."` | **Distorted Preposition + Ungrounded Safety Claim:** The raw tool text says `"Submerge a walkie-talkie tuned to Channel 7 near a kiddie pool of Epsom salt"`, whereas the LLM altered `"near"` to **"in"** (*"in a kiddie pool filled with Epsom salt"*) and appended the unsupported claim ***"making it safer to handle"*** (which does not appear in any tool output). |

---

## 4. Real Failure Mode Analysis: Complaint #4 (The Neighbor's Cat)

### Input Query & Tool Trace (Run #4 in `agent_eval_results.json`)
- **Complaint:** `"My neighbor's cat is acting weird. Is it from the Upside Down?"`
- **Call 1 (`call_1GvHeJDWU2ICE9tfVvDWaag3`, `consult_demogorgon`):**
  - **Args:** `{"complaint": "My neighbor's cat is acting weird. Is it from the Upside Down?"}`
  - **Raw Output:** `"*Guttural Upside Down growl* Regarding 'My neighbor's cat is acting weird. Is it from the Upside Down?': the Demogorgon insists it was merely looking for its lost car keys in your dimension and suggests you stop leaving interdimensional doors unlocked."`
- **Call 2 (`call_w2Z35Yqpqx4cZfJYW2LdVk1h`, `check_hawkins_records`):**
  - **Args:** `{"query": "cats from the Upside Down"}`
  - **Raw Output:** `"Hawkins Record Search: Record not found for query 'cats from the Upside Down'. No classified entry matches portal, monsters, psychics, or electricity."`

### Verbatim Final Answer (Run #4)
> *"The Demogorgon has chimed in with its chaotic wisdom, responding to your query about the bizarre behavior of your neighbor's cat. It suggests that the cat was simply on the hunt for its lost car keys in your dimension – a rather relatable plight, don't you think? It also warns you to stop leaving interdimensional doors unlocked, as this could lead to more than just a curious feline!*
>
> *On the official side, I checked the Hawkins Lab records regarding "cats from the Upside Down" but found no classified entries related to our feline friends. It seems that while strange happenings abound, we can safely conclude that your neighbor's cat has not been touched by the chaos of the Upside Down – at least not in any documented way.*
>
> *Perhaps it's just acting weird for more mundane reasons, like a new toy or an existential crisis?"*

### Two Concrete Grounding Failures Observed in Run #4

1. **Entity Attribution Distortion (Misreading Pronoun Reference in `consult_demogorgon`):**
   - In the raw output of `consult_demogorgon`, the phrase *"the Demogorgon insists it was merely looking for its lost car keys in your dimension"* uses *"it"* / *"its"* to refer to **the Demogorgon itself** making an excuse for intruding into the user's dimension.
   - Because `consult_demogorgon` embeds the literal complaint string (`Regarding 'My neighbor's cat is acting weird...'`), the LLM misattributed the pronoun *"it"* to the **neighbor's cat** and fabricated the claim: *"It suggests that the cat was simply on the hunt for its lost car keys in your dimension"*.

2. **Unsupported Negative Conclusion from a Keyword Lookup Miss (Argument from Ignorance):**
   - `check_hawkins_records` only checks whether one of 4 hardcoded substrings (`portal`, `monsters`, `psychics`, `electricity`) appears in `query.lower()`. Passing `query="cats from the Upside Down"` returned `"Record not found..."` solely because none of those 4 keywords appeared in the query string.
   - Instead of treating `"Record not found"` as a limitation of a 4-key dictionary lookup, the LLM extrapolated an affirmative safety conclusion: *"we can safely conclude that your neighbor's cat has not been touched by the chaos of the Upside Down – at least not in any documented way"*, and hallucinated speculative mundane explanations (*"like a new toy or an existential crisis"*).

---

## 5. Freeform Creative Agent vs. Fixed-Order Structured Workflow (`structured_handler`)

In [`agent_eval_results.json`](./agent_eval_results.json), Complaint #1 (`"My Christmas lights keep flickering and I hear noises from the wall. What is going on?"`) was processed both by the **freeform LangChain agent** (`agent_runs[0]`) and by **`structured_handler(SAMPLE_COMPLAINTS[0])`** (`structured_comparison`), which executes a fixed tool sequence without an LLM:
`check_hawkins_records` → `gather_party_wisdom` → `cast_interdimensional_spell(problem=complaint, creativity_level="low")`.

### Direct Comparison on Complaint #1

| Dimension | Freeform LangChain Agent (`agent_runs[0]`) | Fixed-Order `structured_handler` (`structured_comparison`) |
|---|---|---|
| **Tools Invoked & Order** | `check_hawkins_records` + `consult_demogorgon` (both emitted in Turn 1; `gather_party_wisdom` and `cast_interdimensional_spell` were skipped) | Strictly fixed sequence:<br>1. `check_hawkins_records`<br>2. `gather_party_wisdom`<br>3. `cast_interdimensional_spell(..., creativity_level="low")` |
| **Query Reformulation (`check_hawkins_records`)** | LLM abstracted `"flickering Christmas lights"` into `{"query": "electricity"}`, matching key `"electricity"` and retrieving **Hawkins Record #HNL-04 (Electricity)**. | Passed the raw complaint verbatim (`{"query": "My Christmas lights keep flickering..."}`). Because the literal substring `"electricity"` is absent from the complaint, `check_hawkins_records` returned **`"Record not found"`**. |
| **Party Wisdom Retrieval (`gather_party_wisdom`)** | **Missed:** The agent chose not to call `gather_party_wisdom`, missing Will's specific advice about flickering lights and the alphabet wall. | **Succeeded:** Passed the raw complaint containing the substring `"lights"`, matching key `"lights"` and returning Will's advice (*"When the lights flicker and you hear noises in the wall, the Mind Flayer or something from the Upside Down is right behind the membrane—use the alphabet wall..."*). |
| **Spell Generation (`cast_interdimensional_spell`)** | **Skipped:** The agent did not cast a spell for Complaint #1. | **Guaranteed Execution:** Called with `creativity_level="low"`, returning 1 randomly sampled spell (`[Ritual of the Salt-Bath Resonance]...`). |
| **Important Note on Non-Determinism** | Non-deterministic in tool selection, argument phrasing, `random.choice`/`random.sample` tool outputs, and LLM synthesis. | **Fixed call order, NOT deterministic output:** Although the sequence of 3 tool calls and their arguments are strictly fixed without an LLM, step 3 (`cast_interdimensional_spell`) still calls `random.sample(spells, 1)`, so the selected spell varies across runs unless a random seed is fixed. |

### When to Use Freeform Agents vs. Structured Workflows (e.g., LangGraph)
- **Freeform Tool-Calling Agent (`create_agent`):** Best suited when user inputs require semantic query reformulation (e.g., mapping *"Christmas lights keep flickering"* to keyword `"electricity"` or extracting `creativity_level="high"` from natural language in Complaint #3) and dynamic tool selection. However, it may skip helpful tools (`gather_party_wisdom` in Run #1) or misinterpret tool outputs (Run #4).
- **Structured Workflows (`structured_handler` / LangGraph state machines):** Best suited when compliance requires every step in a protocol (`check_hawkins_records` → `gather_party_wisdom` → `cast_interdimensional_spell`) to execute in a guaranteed order. Combining LangGraph nodes with LLM-assisted query extraction provides both guaranteed step ordering and semantic keyword translation.

---

## 6. Tool Grounding (Traceability) vs. Factual Truthfulness & Reliability

A critical lesson from this lab is the distinction between **traceability to tool outputs (tool grounding)** and **factual truthfulness or real-world reliability**:

1. **Traceability (Internal Grounding):** We can inspect `agent_eval_results.json` and verify whether a statement in `final_answer` came from `ToolMessage.content` (such as `Hawkins Record #HNL-04` or `Spell of Eldritch Eggo Ward`).
2. **Unreliable / Chaotic Sources Inside the System Boundary:** Even when the agent faithfully repeats a tool's output, the tools themselves are intentionally fictional, stochastic, or unreliable:
   - `consult_demogorgon` uses `random.choice()` to return humorous, self-serving excuses from a chaotic monster (blaming fluorescent lights, demanding nougat bars, or looking for lost car keys).
   - `cast_interdimensional_spell` uses `random.sample()` to prescribe absurd fictional rituals (arranging Eggo waffles in a pentagram or placing a walkie-talkie near Epsom salt).
   - `check_hawkins_records` and `gather_party_wisdom` rely on brittle substring matching over 4 hardcoded dictionary keys.

Therefore, proving that an agent's claim is **grounded in tool output** only proves **provenance (where the text came from within the pipeline)**—it does **not** make the output objectively true, complete, or safe to follow without domain validation and guardrails.

---

## 7. Provenance of Verification Results & Synthetic Test Data Disclaimer

To maintain strict evidentiary integrity between offline code checks and live LLM behavior:

1. **Provenance of Offline Test Results:** The execution and passing of the 12 offline unit tests (`python -m unittest -v test_normalobjects_langchain.py`) and the local CLI check (`python normalobjects_langchain.py --mode local`) were **run manually by the user and reported back**, rather than executed directly by the agent environment.
2. **Synthetic Test Data vs. Live Agent Evidence:**
   - The `AIMessage` / `ToolMessage` histories constructed inside [`test_normalobjects_langchain.py`](./test_normalobjects_langchain.py) (`TestSyntheticTraceExtraction`) and inside `run_local_verification()` in [`normalobjects_langchain.py`](./normalobjects_langchain.py) are explicitly labeled as **synthetic test data** created solely to unit-test `extract_trace()` (e.g., verifying out-of-order `tool_call_id` matching and missing `ToolMessage` placeholders). They are **never** used as evidence of real LLM behavior.
   - All claims, traces, tool counts, and failure analyses regarding the LangChain agent in Sections 2–5 of this document are derived exclusively from the live `gpt-4o-mini` execution recorded in [`agent_eval_results.json`](./agent_eval_results.json).

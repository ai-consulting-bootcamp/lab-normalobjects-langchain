# NormalObjects — Creative Complaint Handler

## Learning Goal

Build a creative tool-using complaint handler and assess whether its answers follow
actual tool evidence, distinguishing fictional records from invented humor.

## Project Overview

The Python CLI uses LangChain 1.x `create_agent`, `ChatOpenAI` with `gpt-4o-mini`
and temperature 0.1, four typed `@tool` functions, and dotenv configuration.
Three completed demo traces are available. This proof reviews the recorded executions;
no new model requests were needed for this review. The main example deliberately
uses the flagged first execution so its limitation remains visible.

## Architecture and Workflow

Complaint → agent-selected tools → tool results → final answer → JSON trace →
automated checks → manual evidence review. `AIMessage.tool_calls` provides actual
names, arguments, and IDs; `ToolMessage` supplies results linked by call ID.
The recursion limit is 12, with request timeouts and limited retries. This bounds
execution but does not guarantee a complete or grounded answer.

## Tools Implemented

- `consult_demogorgon`: random selection from three explicitly invented comic responses.
- `check_hawkins_records`: four identifiable local fictional records (portal HK-001,
  monsters HK-002, psychics HK-003, electricity HK-004), case-insensitive whole-word
  matching, multiple matches, and an explicit NOT_FOUND fallback.
- `cast_interdimensional_spell`: four problem-specific invented spells sampled without
  replacement; low/medium/high select 1/2/3 spells; invalid levels raise ValueError.
- `gather_party_wisdom`: invented advice attributed to Mike, Dustin, Lucas, and Will,
  selected by topic, with a generic party-huddle fallback.

All four tools have typed parameters and docstrings. The observed demos used records,
Demogorgon consultation, and party wisdom; no live spell call was observed. Offline
tests exercise spells, including valid/default/invalid levels and output formats.

## Test Query

Source: [first original trace](traces/trace_20261027T201921_87393815.json).
Recorded timestamp: `2026-10-27T20:19:21.744841+00:00` (UTC).
Status: `completed`; model: `gpt-4o-mini`.

```text
My lights keep flickering and I think there is a portal in my basement.
```

## Tool Execution Evidence

The following is extracted verbatim from the original trace. Each call has one
successful result; nested results and the top-level result list agree.

Call 1: `check_hawkins_records`; actual ID: `call_1UiKx8erJetMRDrDeZE3gBTz`.

Arguments:

```json
{
  "query": "portal in basement"
}
```

Actual return value (`status: success`):

```text
[FICTIONAL RECORD HK-001 | portal] Suspected portals must be reported to the Hawkins containment desk. Do not enter.
```

Call 2: `consult_demogorgon`; actual ID: `call_exG7Njuj52mXn3BvHudKdOI3`.

Arguments:

```json
{
  "complaint": "My lights keep flickering and I think there is a portal in my basement."
}
```

Actual return value (`status: success`):

```text
[IMPROVISATION] Regarding My lights keep flickering and I think there is a portal in my basement.: The Demogorgon offers a roar-based apology and no tracking number.
```

## Final Agent Output

Exact `final_response` from the first execution (including unsupported additions):

```text
**Fictional record evidence:** I found a record stating, "[FICTIONAL RECORD HK-001 | portal] Suspected portals must be reported to the Hawkins containment desk. Do not enter." So, it seems like your basement might be a bit more than just a storage area!

**Invented humorous suggestions:** As for your flickering lights, the Demogorgon has graciously offered a roar-based apology, but unfortunately, no tracking number for your portal situation. Maybe it’s just trying to get your attention? 

**Next steps:** I recommend reporting the suspected portal to the Hawkins containment desk immediately. They have the expertise to handle such situations (and probably some cool gear). In the meantime, you might want to avoid any late-night basement adventures—who knows what might be lurking down there!
```

## Grounding Verification

Recorded automated verification, reproduced unchanged by running the current verifier
on the saved trace:

```json
{
  "automated_checks": {
    "relevant_tool_called": false,
    "all_tool_results_captured": true,
    "all_tool_results_successful": true,
    "references_returned_evidence": true,
    "no_unreturned_record_ids": true,
    "final_response_present": true
  },
  "automated_checks_passed": false,
  "matched_record_sentences": [
    "Suspected portals must be reported to the Hawkins containment desk. Do not enter."
  ],
  "unsupported_record_ids": [],
  "answer_supported_by_tool_evidence": "pending_human_review",
  "manual_review_required": true,
  "manual_review_flags": [
    "Review every factual claim, including claims without HK IDs, against actual results.",
    "Check that invented advice is labeled and not presented as a verified remedy."
  ],
  "limitation": "Literal matches and topic keywords do not prove semantic grounding."
}
```

The first check is named `relevant_tool_called`, but actually requires **all detected
complaint topics** to occur in at least one records-call argument. The original query
matches `portal` and `electricity`; the submitted argument `portal in basement`
matches only `portal`. A relevant tool was called, but coverage was incomplete.
HK-004 was never returned. This is a real retrieval omission, not a missing result,
an invalid call ID, or an invented citation. All five other checks pass.

Manual evidence review of all three recorded responses:

| Execution | Actual tools and evidence | Automated result | Manual assessment |
| --- | --- | --- | --- |
| [Electricity/portal](traces/trace_20261027T201921_87393815.json) | records HK-001; Demogorgon roar-based apology | Flagged: incomplete topic coverage | Reporting the suspected portal and avoiding entry follow HK-001. The apology/no tracking number follows the comic tool. The basement implication, desk expertise, and “cool gear” are not established by either result. Electricity was not investigated; the electrical-inspection record was missed. Partially supported, incomplete. |
| [Monster/delivery](traces/trace_20261027T201927_3d7efd07.json) | Demogorgon waffle suggestion box; records HK-002 | All checks pass | Missing-parcel report and not pursuing the creature follow HK-002; the waffle box follows the comic tool and is labeled humorous. A delivery service's possible monster protocol, the monster's sweet tooth, and a trade that returns the parcel are speculation, not returned evidence. “Monsters can be unpredictable” and ending up in the Upside Down are unsupported lore additions. Core advice supported; full answer not verified. |
| [Psychic/objects](traces/trace_20261027T201933_cb1d147d.json) | records HK-003; Demogorgon waffle suggestion box; Will's party wisdom | All checks pass | Logging affected objects and times follows HK-003 and Will's actual advice. The waffle box is faithful comic advice. Pattern/trigger identification is an additional plausible rationale, not a tool result; consulting a local psychic is an unverified suggestion outside the explicitly invented sections. Core logging advice supported; full answer not verified. |

Every cited HK ID was actually returned. No invented Hawkins record or nonexistent
tool call was found. All seven calls across the three traces have successful,
ID-linked results. Recomputed checks exactly match saved checks, and deterministic
record-tool outputs agree with the captured record contents. This validates trace
consistency, not independent provenance of an API response or full factual accuracy.

The automated traces retain `pending_human_review` as originally recorded. This
written review supplements them; it does not rewrite historical evidence or change
failed checks into passes. All three answers are partially supported; none merits
an unqualified claim that every assertion is grounded. Records are fictional local
lore and do not verify real supernatural events.

## Failure or Limitation

The first run demonstrates that a prompt asking for the full complaint does not
force the model to preserve it in tool arguments: it compressed away the electricity
topic. Consequently it omitted a useful record and electrical-inspection advice.
The second and third runs demonstrate the verifier's blind spot: exact quotations
and valid IDs can coexist with unsupported sentences elsewhere. A passing keyword
check cannot prove semantic grounding. Some extra jokes also appear in factual or
practical sections rather than clearly labeled invented sections.

Unresolved behavior: complete topic retrieval and consistent labeling of unsupported
additions are not guaranteed. Possible future improvements are enforcing topic
coverage before accepting a response and requiring sentence-level evidence review.
Those improvements have not been implemented or validated by these traces.

## Conclusion

The implementation, three completed live demo traces, exact main-example evidence,
and critical review are available. All **11 available offline tests passed; 0 failed**
on October 27, 2026. `python -m pip check` reported no broken requirements. Tests
cover keyword matching, unknown records, creativity validation, output formats,
trace extraction, missing results, unsupported IDs, relevance, partial failures,
and missing-key handling. Tests use fixtures where appropriate and are not live proof.

Requirement audit:

| Requirement | Status |
| --- | --- |
| Requested project files and four dependencies | Satisfied; example_trace.json is now an exact copy of the first real trace. |
| Modern LangChain agent, requested imports/model, dotenv, low temperature | Satisfied by implementation and observed completed traces. |
| Four creative tools, typed parameters, docstrings, randomness and validation | Implemented; offline tests pass; live spell selection was not observed or required for every complaint. |
| Interactive, demo, and single-query CLI paths; three example complaints | Implemented; all three demo complaints have completed traces. Interactive and single-query modes were not separately exercised in this review. |
| Query, actual names/arguments/results/IDs, final answer, support assessment | Captured in traces; support assessment supplemented by the manual review above. |
| Relevant tools, multiple tools, bounded loops | Observed multi-tool use in every demo; recursion limit implemented. Topic coverage was incomplete for the first complaint. |
| Clearly distinguish records from inventions; no unsupported factual additions | Partially met: record citations are faithful, but unsupported additions and inconsistent labeling remain. |
| Grounding checks and honest manual-review distinction | Satisfied as a simple heuristic with explicit limitations; not a semantic accuracy guarantee. |
| Required proof structure and one real execution | Satisfied by this document. |
| Tests, validation, secret exclusions and submission review | Tests and dependency checks pass; secret-review findings are recorded below. |
| Reference notebook and diagrams if present | Neither file was available; no use claimed. |

**Not every behavioral requirement is fully satisfied.** The lab evidence and review
are ready for assessment, including documented failure modes; the agent should not
be described as fully grounded or fully compliant with the factual-output rules.
The original three traces remain unchanged. `example_trace.json` duplicates the first
trace for the requested filename and is not a fourth independent execution.

Secret review: a credential was found in `.env.example` during review. The template
was restored to the empty assignment `OPENAI_API_KEY=`; the private `.env` was not
modified. After cleanup, all 11 submission files were scanned against configured
credential values and recognizable API/private-key patterns, with no matches.
The reviewed file set comprises source, tests, documentation, configuration
templates, and four trace JSON files. `.env` is excluded from this set.
`.gitignore` excludes `.env`, virtual environments, caches, and key files.
No Git repository is initialized here, so tracked-file status cannot be checked; .gitignore contains the required exclusions.
Submit only the reviewed files, excluding `.env` and `.venv`. The scan cannot prove
the absence of every possible secret format. The review does not establish whether
the former template credential was previously shared or exposed elsewhere.

## How to Reproduce

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# If .env does not already exist: copy .env.example to .env.
# Set OPENAI_API_KEY locally; never include .env in the submission.
python -m unittest -v
python -m pip check
python normalobjects_langchain.py --demo --seed 42
```

Read each new `traces/trace_*.json` and compare tool-call IDs, actual result contents,
final text, and automated flags. The random seed controls local random draws for an
identical call sequence; it does not reproduce model decisions or exact answers.
The recorded executions above remain the evidence for this proof, even if later
runs differ. No API requests were made during this review.

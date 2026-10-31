"""NormalObjects - Creative Complaint Handler (LangChain).

Implements a creative tool-calling agent for handling anomalies and complaints
in the Normal Objects / Hawkins universe, along with a fixed-order structured
workflow without LLM and full tool-call trace extraction.
"""

import argparse
import json
import os
import random
from typing import Any, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# ============================================================================
# Sample Complaints from the Lab Notebook
# ============================================================================

SAMPLE_COMPLAINTS: List[str] = [
    "My Christmas lights keep flickering and I hear noises from the wall. What is going on?",
    "There is a weird portal in my basement. What's the plan?",
    "A Demodog ate my homework. I need a creative solution, creativity level high!",
    "My neighbor's cat is acting weird. Is it from the Upside Down?",
]

SYSTEM_PROMPT: str = (
    "You are the Creative Complaint Handler for the Department of NormalObjects "
    "(Becna's helpline). Your job is to handle complaints about the Upside Down, "
    "Hawkins anomalies, monsters, portals, psychics, and electrical weirdness in "
    "an entertaining, creative, yet evidence-grounded way.\n\n"
    "You have access to four specialized tools:\n"
    "- consult_demogorgon: get chaotic perspective from the Upside Down\n"
    "- check_hawkins_records: search official Hawkins Lab records\n"
    "- cast_interdimensional_spell: generate creative interdimensional spells/solutions\n"
    "- gather_party_wisdom: ask Mike, Dustin, Lucas, and Will for advice\n\n"
    "Feel free to chain multiple tools in whatever order best fits the complaint. "
    "In your final response, explicitly reference the findings and outputs returned "
    "by the tools you called."
)


# ============================================================================
# Step 2: Creative Tools
# ============================================================================

@tool
def consult_demogorgon(complaint: str) -> str:
    """Consult the Demogorgon about a complaint from the Upside Down.

    Accepts a complaint string and returns a chaotic/humorous response from
    the Demogorgon's perspective.
    """
    responses = [
        (
            f"*Screeching petal-jaw noises* The Demogorgon tilts its head at "
            f"'{complaint}', blames Hawkins Lab's fluorescent lighting, and demands "
            f"three nougat bars as tribute."
        ),
        (
            f"*Guttural Upside Down growl* Regarding '{complaint}': the Demogorgon "
            f"insists it was merely looking for its lost car keys in your dimension "
            f"and suggests you stop leaving interdimensional doors unlocked."
        ),
        (
            f"*Echoing spore-cloud roar* The Demogorgon reviewed '{complaint}', "
            f"rated your household terror level a 6/10, and recommends redecorating "
            f"with more vines and pulsing shadow-membranes."
        ),
    ]
    return random.choice(responses)


@tool
def check_hawkins_records(query: str) -> str:
    """Search official Hawkins National Laboratory records for a given query.

    Checks topic-keyed records (portal, monsters, psychics, electricity)
    case-insensitively and returns matching documentation or a 'not found' message.
    """
    records: Dict[str, str] = {
        "portal": (
            "Hawkins Record #HNL-01 (Portal): Interdimensional gates form where "
            "psychic trauma intersects with high-voltage electromagnetic fields. "
            "Standard containment requires sustained heat and sonic disruption."
        ),
        "monsters": (
            "Hawkins Record #HNL-02 (Monsters): Entities include Demogorgons, "
            "Demodogs, and the Mind Flayer hive-mind. All exhibit extreme aversion "
            "to fire, high temperatures, and telekinetic impact."
        ),
        "psychics": (
            "Hawkins Record #HNL-03 (Psychics): Test subjects (notably Subject 011) "
            "demonstrate telekinesis, remote viewing via sensory deprivation baths, "
            "and bi-dimensional rift manipulation."
        ),
        "electricity": (
            "Hawkins Record #HNL-04 (Electricity): Magnetic field anomalies and "
            "flickering lights (especially holiday string lights and wall radios) "
            "indicate proximity to an active Upside Down membrane or entity."
        ),
    }
    normalized_query = query.lower()
    for key, record_value in records.items():
        if key in normalized_query:
            return record_value
    return (
        f"Hawkins Record Search: Record not found for query '{query}'. "
        f"No classified entry matches portal, monsters, psychics, or electricity."
    )


@tool
def cast_interdimensional_spell(
    problem: str, creativity_level: str = "medium"
) -> str:
    """Cast an interdimensional spell to resolve a problem.

    Accepts a problem description and an optional creativity_level
    ('low', 'medium', or 'high') which selects 1, 2, or 3 spell solutions.
    """
    level_map: Dict[str, int] = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }
    multiplier = level_map.get(str(creativity_level).strip().lower(), 2)

    spells: List[str] = [
        (
            f"[Spell of Eldritch Eggo Ward] Arrange toasted Eggo waffles in a "
            f"pentagram around the site of '{problem}' while blasting 85-decibel "
            f"synthwave to seal the dimensional seam."
        ),
        (
            f"[Ritual of the Salt-Bath Resonance] Submerge a walkie-talkie tuned "
            f"to Channel 7 near a kiddie pool of Epsom salt to invert the polarity "
            f"of '{problem}'."
        ),
        (
            f"[Incantation of Hellfire Dice] Roll a natural 20 on a glowing d20 "
            f"while chanting 'Vecna Be Gone' three times to banish '{problem}' "
            f"back into the Shadow Vale."
        ),
        (
            f"[Arcane Christmas-Light Faraday Cage] Wrap copper fairy lights "
            f"counter-clockwise around the perimeter of '{problem}' and pulse "
            f"Morse code S-O-S to neutralize spore interference."
        ),
    ]
    n_spells = min(multiplier, len(spells))
    selected = random.sample(spells, n_spells)
    return "\n".join(selected)


@tool
def gather_party_wisdom(question: str) -> str:
    """Gather wisdom from the Hawkins AV Club Party (Mike, Dustin, Lucas, Will).

    Matches keywords in the question case-insensitively or returns a generic
    party huddle fallback if no specific topic matches.
    """
    party_wisdom: Dict[str, str] = {
        "portal": (
            "Mike says: 'Just like in our D&D campaign, a portal is a Vale of "
            "Shadows gate! We need a coordinated party plan—nobody goes into the "
            "basement alone, and keep your Supercomm on channel 3!'"
        ),
        "monster": (
            "Dustin says: 'Wait, if it's a Demodog or Demogorgon, check your "
            "compasses for magnetic deflection, keep nougat away from it, and "
            "prepare a heat-trap perimeter immediately!'"
        ),
        "lights": (
            "Will says: 'When the lights flicker and you hear noises in the wall, "
            "the Mind Flayer or something from the Upside Down is right behind "
            "the membrane—use the alphabet wall to see if someone is talking!'"
        ),
        "defense": (
            "Lucas says: 'Grab the Wrist Rocket, load up the highest-grade rocks, "
            "and set up motion-tripwires at every entrance before it ambushes us!'"
        ),
    }
    normalized_question = question.lower()
    for key, wisdom_value in party_wisdom.items():
        if key in normalized_question:
            return wisdom_value
    return (
        "The Party forms an emergency huddle in Wheeler's basement: Mike, Dustin, "
        "Lucas, and Will compare D&D manuals and agree this anomaly needs close "
        "observation, walkie-talkie check-ins every 10 minutes, and backup from Eleven."
    )


ALL_TOOLS = [
    consult_demogorgon,
    check_hawkins_records,
    cast_interdimensional_spell,
    gather_party_wisdom,
]


# ============================================================================
# Step 5: Fixed-Order Structured Workflow (Without LLM)
# ============================================================================

def structured_handler(complaint: str) -> Dict[str, Any]:
    """Fixed-order structured workflow without LLM.

    Executes tools in a strict predefined sequence:
    1. check_hawkins_records
    2. gather_party_wisdom
    3. cast_interdimensional_spell(..., creativity_level="low")

    Note: The call order is strictly fixed, though cast_interdimensional_spell
    still uses random.sample() to pick 1 spell from the 4 available templates.
    """
    record_result = check_hawkins_records.invoke({"query": complaint})
    wisdom_result = gather_party_wisdom.invoke({"question": complaint})
    spell_result = cast_interdimensional_spell.invoke(
        {"problem": complaint, "creativity_level": "low"}
    )

    tool_sequence = [
        "check_hawkins_records",
        "gather_party_wisdom",
        "cast_interdimensional_spell",
    ]

    formatted_response = (
        f"=== Structured Complaint Resolution (Fixed-Order Workflow) ===\n"
        f"Complaint: {complaint}\n\n"
        f"[Step 1 - Hawkins Lab Record]:\n{record_result}\n\n"
        f"[Step 2 - Party Wisdom]:\n{wisdom_result}\n\n"
        f"[Step 3 - Interdimensional Spell (creativity_level='low')]:\n{spell_result}"
    )

    return {
        "complaint": complaint,
        "workflow_type": "fixed_order_structured_without_llm",
        "tool_sequence": tool_sequence,
        "steps": [
            {
                "step": 1,
                "tool_name": "check_hawkins_records",
                "args": {"query": complaint},
                "output": record_result,
            },
            {
                "step": 2,
                "tool_name": "gather_party_wisdom",
                "args": {"question": complaint},
                "output": wisdom_result,
            },
            {
                "step": 3,
                "tool_name": "cast_interdimensional_spell",
                "args": {"problem": complaint, "creativity_level": "low"},
                "output": spell_result,
            },
        ],
        "final_output": formatted_response,
    }


# ============================================================================
# Trace Extraction & Tool Usage Tracking
# ============================================================================

def extract_trace(
    messages: List[Any], complaint: Optional[str] = None
) -> Dict[str, Any]:
    """Extract tool call trace and usage statistics from agent messages.

    Matches each entry in AIMessage.tool_calls to its corresponding ToolMessage
    strictly via `tool_call_id`.

    Important semantic note on ordering:
    - When an AIMessage contains multiple `tool_calls` in a single turn, their
      relative order in `AIMessage.tool_calls` only reflects the list ordering
      emitted in that single model turn (`is_parallel_call_in_turn=True`), NOT
      sequential multi-step chaining.
    - True sequential chaining occurs across distinct `AIMessage` -> `ToolMessage`
      -> `AIMessage` turns (`ai_turn_index`).
    """
    tool_messages_by_id: Dict[str, ToolMessage] = {}
    for msg in messages:
        if isinstance(msg, ToolMessage) and getattr(msg, "tool_call_id", None):
            tool_messages_by_id[msg.tool_call_id] = msg

    if complaint is None:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                complaint = str(msg.content)
                break

    trace_steps: List[Dict[str, Any]] = []
    tool_counts: Dict[str, int] = {}
    tool_sequence: List[str] = []
    turns_summary: List[List[str]] = []

    ai_turn_index = 0
    final_answer = ""

    for msg in messages:
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                ai_turn_index += 1
                is_parallel = len(tool_calls) > 1
                current_turn_tools: List[str] = []

                for call_idx, tc in enumerate(tool_calls):
                    tc_id = tc.get("id")
                    tc_name = tc.get("name", "unknown_tool")
                    tc_args = tc.get("args", {})

                    matched_tool_msg = (
                        tool_messages_by_id.get(tc_id) if tc_id else None
                    )
                    tool_output = (
                        str(matched_tool_msg.content)
                        if matched_tool_msg is not None
                        else "<ToolMessage not found for tool_call_id>"
                    )

                    tool_counts[tc_name] = tool_counts.get(tc_name, 0) + 1
                    tool_sequence.append(tc_name)
                    current_turn_tools.append(tc_name)

                    trace_steps.append(
                        {
                            "call_number": len(trace_steps) + 1,
                            "ai_turn_index": ai_turn_index,
                            "index_within_turn": call_idx,
                            "is_parallel_call_in_turn": is_parallel,
                            "tool_call_id": tc_id,
                            "tool_name": tc_name,
                            "args": tc_args,
                            "output": tool_output,
                        }
                    )
                turns_summary.append(current_turn_tools)
            else:
                if msg.content:
                    final_answer = str(msg.content)

    # Format human-readable chain representation distinguishing parallel calls in one turn
    # vs sequential turns: e.g. "(check_hawkins_records + gather_party_wisdom [same AI turn]) -> cast_interdimensional_spell"
    formatted_turns: List[str] = []
    for turn_tools in turns_summary:
        if len(turn_tools) == 1:
            formatted_turns.append(turn_tools[0])
        else:
            formatted_turns.append(f"({' + '.join(turn_tools)} [same AI turn])")
    chaining_pattern = (
        " -> ".join(formatted_turns) if formatted_turns else "no_tools_called"
    )

    return {
        "complaint": complaint or "",
        "total_tool_calls": len(trace_steps),
        "total_ai_tool_turns": ai_turn_index,
        "tool_sequence": tool_sequence,
        "turns_summary": turns_summary,
        "chaining_pattern": chaining_pattern,
        "tool_counts": tool_counts,
        "trace_steps": trace_steps,
        "final_answer": final_answer,
    }


class ToolUsageTracker:
    """Aggregates tool usage and chaining traces across multiple complaint runs."""

    def __init__(self) -> None:
        self.runs: List[Dict[str, Any]] = []
        self.aggregate_counts: Dict[str, int] = {
            t.name: 0 for t in ALL_TOOLS
        }

    def record_run(
        self, messages: List[Any], complaint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract trace from a single agent invocation and update aggregate stats."""
        trace = extract_trace(messages, complaint=complaint)
        self.runs.append(trace)
        for tool_name, count in trace["tool_counts"].items():
            self.aggregate_counts[tool_name] = (
                self.aggregate_counts.get(tool_name, 0) + count
            )
        return trace

    def summary(self) -> Dict[str, Any]:
        """Return aggregated tool usage statistics across all recorded runs."""
        return {
            "total_runs": len(self.runs),
            "aggregate_tool_counts": dict(self.aggregate_counts),
            "chaining_patterns_by_run": [
                {
                    "complaint": r["complaint"],
                    "chaining_pattern": r["chaining_pattern"],
                    "total_tool_calls": r["total_tool_calls"],
                    "total_ai_tool_turns": r["total_ai_tool_turns"],
                }
                for r in self.runs
            ],
        }


# ============================================================================
# Step 3: Lazy Agent Creation & Execution
# ============================================================================

def build_complaint_agent(
    model_name: str = "gpt-4o-mini", temperature: float = 0.7
) -> Any:
    """Lazily initialize environment variables, ChatOpenAI model, and LangChain agent.

    Called ONLY when running in 'agent' mode so importing this module or running
    local unit tests never requires OPENAI_API_KEY or network access.
    """
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set in the environment or .env file. "
            "Please configure OPENAI_API_KEY before running '--mode agent'."
        )

    llm = ChatOpenAI(model=model_name, temperature=temperature)
    agent = create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


def handle_complaint_with_agent(
    agent: Any,
    complaint: str,
    tracker: Optional[ToolUsageTracker] = None,
    recursion_limit: int = 10,
) -> Dict[str, Any]:
    """Invoke the creative agent on a single complaint with recursion_limit protection."""
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": complaint}]},
            config={"recursion_limit": recursion_limit},
        )
        messages = response.get("messages", [])
        if tracker is not None:
            return tracker.record_run(messages, complaint=complaint)
        return extract_trace(messages, complaint=complaint)
    except Exception as exc:
        error_type = type(exc).__name__
        return {
            "complaint": complaint,
            "error": f"{error_type}: Failed to complete agent invocation ({exc})",
            "total_tool_calls": 0,
            "total_ai_tool_turns": 0,
            "tool_sequence": [],
            "turns_summary": [],
            "chaining_pattern": "error",
            "tool_counts": {},
            "trace_steps": [],
            "final_answer": "",
        }


# ============================================================================
# CLI Modes: Local Verification (No API) and Full Agent Evaluation (With API)
# ============================================================================

def run_local_verification() -> Dict[str, Any]:
    """Run offline verification of tools, fallbacks, structured workflow, and trace parser."""
    print("=== Running Local Offline Verification (No API / No Network) ===")
    random.seed(42)

    direct_tool_checks = {
        "consult_demogorgon": consult_demogorgon.invoke(
            {"complaint": "strange static on the TV"}
        ),
        "check_hawkins_records_match": check_hawkins_records.invoke(
            {"query": "What do we know about the PORTAL and ELECTRICITY?"}
        ),
        "check_hawkins_records_fallback": check_hawkins_records.invoke(
            {"query": "Unrelated topic about gardening"}
        ),
        "cast_spell_low": cast_interdimensional_spell.invoke(
            {"problem": "flickering wall", "creativity_level": "low"}
        ),
        "cast_spell_medium": cast_interdimensional_spell.invoke(
            {"problem": "flickering wall", "creativity_level": "medium"}
        ),
        "cast_spell_high": cast_interdimensional_spell.invoke(
            {"problem": "flickering wall", "creativity_level": "high"}
        ),
        "gather_party_wisdom_match": gather_party_wisdom.invoke(
            {"question": "There is a portal in the basement!"}
        ),
        "gather_party_wisdom_fallback": gather_party_wisdom.invoke(
            {"question": "Where should we eat lunch today?"}
        ),
    }

    structured_sample = structured_handler(SAMPLE_COMPLAINTS[0])

    # Synthetic test messages (strictly for offline parser verification, NOT agent proof)
    synthetic_messages = [
        HumanMessage(content="Synthetic test complaint"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "synth_call_1",
                    "name": "check_hawkins_records",
                    "args": {"query": "portal"},
                },
                {
                    "id": "synth_call_2",
                    "name": "gather_party_wisdom",
                    "args": {"question": "portal"},
                },
            ],
        ),
        ToolMessage(
            content="Synthetic record output", tool_call_id="synth_call_1"
        ),
        ToolMessage(
            content="Synthetic wisdom output", tool_call_id="synth_call_2"
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "synth_call_3",
                    "name": "cast_interdimensional_spell",
                    "args": {"problem": "portal", "creativity_level": "low"},
                }
            ],
        ),
        ToolMessage(
            content="Synthetic spell output", tool_call_id="synth_call_3"
        ),
        AIMessage(content="Synthetic final grounded response."),
    ]
    synthetic_trace = extract_trace(synthetic_messages)

    result = {
        "mode": "local_offline_verification",
        "direct_tool_checks": direct_tool_checks,
        "structured_handler_sample": structured_sample,
        "synthetic_trace_verification": synthetic_trace,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def run_agent_evaluation(
    model_name: str = "gpt-4o-mini",
    recursion_limit: int = 10,
    json_output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the LangChain agent on all 4 SAMPLE_COMPLAINTS plus structured comparison."""
    print("=== Running Live Agent Evaluation on 4 Sample Complaints ===")
    agent = build_complaint_agent(model_name=model_name)
    tracker = ToolUsageTracker()

    agent_runs: List[Dict[str, Any]] = []
    for idx, complaint in enumerate(SAMPLE_COMPLAINTS, start=1):
        print(f"\n--- Complaint #{idx}: {complaint} ---")
        trace = handle_complaint_with_agent(
            agent=agent,
            complaint=complaint,
            tracker=tracker,
            recursion_limit=recursion_limit,
        )
        agent_runs.append(trace)
        if "error" in trace:
            print(f"Error: {trace['error']}")
        print(f"Chaining Pattern: {trace['chaining_pattern']}")
        print(f"Total Tool Calls: {trace['total_tool_calls']}")
        for step in trace["trace_steps"]:
            print(
                f"  [Call {step['call_number']} | Turn {step['ai_turn_index']} | "
                f"Parallel={step['is_parallel_call_in_turn']}] "
                f"{step['tool_name']}({step['args']}) -> {step['output']}"
            )
        print(f"Final Answer:\n{trace['final_answer']}\n")

    # Compare with fixed-order structured workflow on the first complaint
    structured_comparison = structured_handler(SAMPLE_COMPLAINTS[0])

    # Explicit direct fallback demonstration for records & party wisdom
    fallback_demonstration = {
        "query": "My neighbor's cat is acting weird. Is it from the Upside Down?",
        "check_hawkins_records_direct_output": check_hawkins_records.invoke(
            {"query": "My neighbor's cat is acting weird. Is it from the Upside Down?"}
        ),
        "gather_party_wisdom_direct_output": gather_party_wisdom.invoke(
            {"question": "My neighbor's cat is acting weird. Is it from the Upside Down?"}
        ),
    }

    report = {
        "mode": "live_agent_evaluation",
        "model": model_name,
        "recursion_limit": recursion_limit,
        "agent_runs": agent_runs,
        "tracker_summary": tracker.summary(),
        "structured_comparison": structured_comparison,
        "fallback_demonstration": fallback_demonstration,
    }

    if json_output_path:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Saved full evaluation report to: {json_output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NormalObjects - Creative Complaint Handler (LangChain)"
    )
    parser.add_argument(
        "--mode",
        choices=["local", "agent"],
        default="local",
        help=(
            "'local' runs offline tool/fallback/structured/trace checks without API; "
            "'agent' runs the live LangChain agent on SAMPLE_COMPLAINTS."
        ),
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model name for '--mode agent' (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=10,
        help="Graph recursion_limit for agent execution (default: 10).",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to save JSON trace report in '--mode agent'.",
    )
    args = parser.parse_args()

    if args.mode == "local":
        run_local_verification()
    else:
        run_agent_evaluation(
            model_name=args.model,
            recursion_limit=args.recursion_limit,
            json_output_path=args.json_output,
        )


if __name__ == "__main__":
    main()

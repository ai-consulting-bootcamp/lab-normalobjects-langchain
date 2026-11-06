"""A small LangChain agent for fictional Hawkins complaints."""

import argparse
import os
import random
import sys
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


# Load the local key into the environment without displaying it.
load_dotenv(Path(__file__).with_name(".env"))


@tool
def consult_demogorgon(complaint: str) -> str:
    """Ask the Demogorgon for a chaotic opinion about an Upside Down complaint."""
    responses = [
        "The Demogorgon says the noise is probably a portal practicing its singing.",
        "The Demogorgon recommends leaving a snack by the portal and asking it to be quiet.",
        "The Demogorgon blames poor interdimensional acoustics and offers no apology.",
    ]
    return random.choice(responses)


@tool
def check_hawkins_records(query: str) -> str:
    """Search Hawkins records for portal, monsters, psychics, or electricity facts."""
    records = {
        "portal": "Hawkins records note that unstable portals can hum, flicker, and react to nearby power.",
        "monsters": "Hawkins records describe local monsters as attracted to food, blood, and generally poor security.",
        "psychics": "Hawkins records say psychic activity often spikes near dimensional disturbances.",
        "electricity": "Hawkins records report that unusual electrical surges can precede a portal disturbance.",
    }
    lowered_query = query.lower()
    for topic, record in records.items():
        if topic in lowered_query:
            return record
    return "No matching Hawkins record was found."


@tool
def cast_interdimensional_spell(
    problem: str, creativity_level: str = "medium"
) -> str:
    """Suggest one to three playful spells for a problem, based on creativity level."""
    counts = {"low": 1, "medium": 2, "high": 3}
    level = creativity_level.lower().strip()
    if level not in counts:
        raise ValueError("creativity_level must be 'low', 'medium', or 'high'.")

    spells = [
        f"Whisper 'settle down' to {problem}, then tap a flashlight three times.",
        f"Draw a chalk circle around {problem} and appoint a toy knight as guard.",
        f"Offer {problem} a tiny welcome mat labeled 'please behave'.",
        f"Play one calm song toward {problem} and close the nearest wardrobe for good measure.",
    ]
    selected = random.sample(spells, k=min(counts[level], len(spells)))
    return "\n".join(selected)


@tool
def gather_party_wisdom(question: str) -> str:
    """Ask the party for advice about portal, monsters, psychics, or electricity."""
    wisdom = {
        "portal": "Mike: Make a plan, mark the exits, and do not let the portal split up the party.",
        "monsters": "Dustin: First identify the species; then check whether it can be distracted with snacks.",
        "psychics": "Lucas: Trust your friend, but keep a clear escape route and a spare slingshot.",
        "electricity": "Will: If the lights flicker, tell someone and get away from the wiring.",
    }
    lowered_question = question.lower()
    for topic, response in wisdom.items():
        if topic in lowered_question:
            return response
    return "The party suggests a quick huddle, a map, and not investigating the noise alone."


TOOLS = [
    consult_demogorgon,
    check_hawkins_records,
    cast_interdimensional_spell,
    gather_party_wisdom,
]

SYSTEM_PROMPT = """You are the Creative Complaint Handler for fictional Hawkins.
Use the available tools to investigate complaints and shape a useful, playful answer.
Choose tools in whatever order fits the complaint; use one or more tools when helpful.
Base factual claims about Hawkins on tool results, and do not claim a tool said something
it did not. Clearly distinguish playful spell ideas from verified record information.
Keep the final answer concise and address the user's complaint directly."""

SAMPLE_COMPLAINTS = [
    "A portal in my basement hums all night and keeps me awake.",
    "A monster keeps taking food from my fridge. How do I stop it?",
    "The power in my house flickers whenever my psychic cousin visits.",
]


def create_complaint_agent():
    """Build the tool-calling agent using the key supplied by the environment."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Set it in the environment before running the agent."
        )
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return create_agent(model, TOOLS, system_prompt=SYSTEM_PROMPT)


def _message_text(content: Any) -> str:
    """Convert common LangChain message content forms to readable text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in content
        ]
        return "\n".join(parts)
    return str(content)


def extract_trace(result: dict[str, Any]) -> dict[str, Any]:
    """Collect tool requests, tool results, and the final assistant message."""
    calls = []
    outputs = []
    final_response = ""
    for message in result.get("messages", []):
        for call in getattr(message, "tool_calls", []) or []:
            calls.append({"name": call.get("name"), "args": call.get("args", {})})
        if getattr(message, "type", "") == "tool":
            outputs.append(
                {"name": getattr(message, "name", "tool"), "output": _message_text(message.content)}
            )
        elif getattr(message, "type", "") == "ai" and not getattr(message, "tool_calls", []):
            final_response = _message_text(message.content)
    return {"tool_calls": calls, "tool_outputs": outputs, "final_response": final_response}


def handle_complaint(agent, complaint: str) -> dict[str, Any]:
    """Run one complaint and return an inspectable trace."""
    result = agent.invoke({"messages": [{"role": "user", "content": complaint}]})
    return extract_trace(result)


def print_trace(complaint: str, trace: dict[str, Any]) -> None:
    """Print a compact trace that can be copied into the lab proof."""
    print(f"\nQuery: {complaint}")
    print("Tool calls:")
    if not trace["tool_calls"]:
        print("  (none)")
    for call in trace["tool_calls"]:
        print(f"  {call['name']}({call['args']})")
    print("Tool outputs:")
    if not trace["tool_outputs"]:
        print("  (none)")
    for output in trace["tool_outputs"]:
        print(f"  {output['name']}: {output['output']}")
    print("Final response:")
    print(trace["final_response"] or "(no final response returned)")


def run_tool_checks() -> None:
    """Run deterministic assertions around the four tool contracts."""
    demogorgon_options = {
        "The Demogorgon says the noise is probably a portal practicing its singing.",
        "The Demogorgon recommends leaving a snack by the portal and asking it to be quiet.",
        "The Demogorgon blames poor interdimensional acoustics and offers no apology.",
    }
    assert consult_demogorgon.invoke({"complaint": "A portal is noisy."}) in demogorgon_options
    expected_records = {
        "PORTAL": "unstable portals",
        "Monsters": "local monsters",
        "Psychics": "psychic activity",
        "ELECTRICITY": "electrical surges",
    }
    for topic, expected_text in expected_records.items():
        assert expected_text in check_hawkins_records.invoke({"query": topic})
    assert check_hawkins_records.invoke({"query": "bicycles"}) == "No matching Hawkins record was found."
    for level, expected_count in (("low", 1), ("medium", 2), ("high", 3)):
        spells = cast_interdimensional_spell.invoke(
            {"problem": "the humming portal", "creativity_level": level}
        ).splitlines()
        assert len(spells) == expected_count
        assert all("the humming portal" in spell for spell in spells)
    try:
        cast_interdimensional_spell.invoke(
            {"problem": "a problem", "creativity_level": "wild"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("An unsupported creativity level should be rejected.")
    expected_advice = {
        "PORTAL": "Mike:",
        "Monsters": "Dustin:",
        "psychics": "Lucas:",
        "ELECTRICITY": "Will:",
    }
    for topic, character in expected_advice.items():
        assert character in gather_party_wisdom.invoke({"question": topic})
    assert "huddle" in gather_party_wisdom.invoke({"question": "lost bikes"})
    print("Tool self-checks passed: all four tools, matching, fallbacks, and spell levels.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-check", action="store_true", help="check tool behavior without an API call"
    )
    parser.add_argument(
        "--query", action="append", help="complaint to run; repeat to run multiple complaints"
    )
    args = parser.parse_args()

    if args.self_check:
        run_tool_checks()
        if not args.query:
            return 0
    try:
        agent = create_complaint_agent()
    except EnvironmentError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    complaints = args.query or SAMPLE_COMPLAINTS
    for complaint in complaints:
        try:
            print_trace(complaint, handle_complaint(agent, complaint))
        except Exception as exc:
            details = str(exc)
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if api_key:
                details = details.replace(api_key, "[REDACTED]")
            print(
                f"Agent request failed ({type(exc).__name__}): {details}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

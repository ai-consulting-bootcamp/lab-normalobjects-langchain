import argparse
import os
import random
from collections import Counter
from time import perf_counter

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# Create the model and agents without making an API request.
model = init_chat_model(model="gpt-4o-mini", model_provider="openai", temperature=0.7)

# The creative tools.
@tool
def consult_demogorgon(complaint: str) -> str:
    """Ask the Demogorgon for a short, chaotic opinion about a complaint."""
    response = model.invoke(
        "Give one short, chaotic, clearly unreliable NormalObjects-style opinion "
        f"about this complaint: {complaint}"
    )
    return response.content


@tool
def check_hawkins_records(query: str) -> str:
    """Search the four topic-keyed Hawkins records for a key in the query."""
    records = {
        "portal": "Portal log: a gate was reported in Hawkins Lab's basement; the report recommends keeping distance.",
        "monsters": "Monster log: Demogorgon and Demodog sightings are listed; this record does not identify ordinary animals as monsters.",
        "psychics": "Psychics log: reports describe telekinetic activity; the log does not confirm a cause for any individual event.",
        "electricity": "Electricity log: flickering lights and voltage drops have been reported near unusual activity; cause not confirmed.",
    }
    query_lower = query.lower()
    for key, record in records.items():
        if key.lower() in query_lower:
            return record
    return f"No record found for query: {query}"


@tool
def cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str:
    """Suggest one to three playful spells for the stated problem."""
    multipliers = {"low": 1, "medium": 2, "high": 3}
    count = multipliers.get(creativity_level.lower(), 2)
    spells = [
        f"The Mirror Maze: redirect {problem} through a harmless mirror loop.",
        f"The Pocket Portal: shrink {problem} into a labeled lunchbox for one hour.",
        f"The Cosmic Confetti: surround {problem} with distracting, non-sticky stardust.",
        f"The Reverse Echo: send {problem} back as a polite note to its point of origin.",
    ]
    selected_spells = random.sample(spells, k=min(count, len(spells)))
    return "\n".join(selected_spells)


@tool
def gather_party_wisdom(question: str) -> str:
    """Find party advice by topic word, with a huddle fallback."""
    responses = {
        "plan": "Mike: Make a plan, agree on a signal, and stay together.",
        "science": "Dustin: Check the evidence first; a strange reading is still just a reading.",
        "danger": "Lucas: Keep a safe distance and have an exit ready.",
        "upside down": "Will: Trust your instincts, but compare them with what the records say.",
    }
    question_lower = question.lower()
    for topic, response in responses.items():
        if topic.lower() in question_lower:
            return response
    return "The party huddles around the map and agrees to compare notes before acting."


tools = [
    consult_demogorgon,
    check_hawkins_records,
    cast_interdimensional_spell,
    gather_party_wisdom,
]

system_prompt = """You are the NormalObjects creative complaint handler.
Use the available tools creatively and in any order that helps. For every complaint,
make at least one tool call. Answer only from the results returned by tools. If a
record tool says 'No record found', say 'No record found' and do not invent a cause
or diagnosis. Treat the Demogorgon's opinion as an opinion, not verified evidence.
Write each factual or suggested claim as a short bullet and append the supporting
[tool_name]. Do not cite a tool unless its output supports that claim. End with a
' tools used:' line listing only tools actually called.""".replace("tools", "Tools")

# The app agent uses the Extension 2 Demogorgon tool and the Extension 3 in-memory saver.
llm_agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)
agent = llm_agent
memory_agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=InMemorySaver(),
    system_prompt=system_prompt,
)

# The standalone Extension 3 memory example keeps conversation separate from tool evidence.
memory_demo_agent = create_agent(
    model=model,
    tools=[],
    checkpointer=InMemorySaver(),
    system_prompt="Use conversation history to answer questions about the earlier message.",
)

complaints = [
    "My Christmas lights keep flickering and I hear noises from the wall. What is going on?",
    "There is a weird portal in my basement. What's the plan?",
    "A Demodog ate my homework. I need a creative solution, creativity level high!",
    "My neighbor's cat is acting weird. Is it from the Upside Down?",
]

# The app updates these after each completed complaint.
tool_rounds = []
evidence_rows = []
run_stats = []
results = []
agent_elapsed = []


def structured_handler(complaint: str) -> str:
    record = check_hawkins_records.invoke({"query": complaint})
    party = gather_party_wisdom.invoke({"question": complaint})
    spell = cast_interdimensional_spell.invoke(
        {"problem": complaint, "creativity_level": "low"}
    )
    return f"Records: {record}\nParty: {party}\nSpell: {spell}"


def claim_check(answer: str, rows: list) -> list:
    called = {row["tool"] if isinstance(row, dict) else row[0] for row in rows}
    verdicts = []
    for line in answer.splitlines():
        claim = line.strip(" -*\t")
        if not claim or claim.lower().startswith("tools used:"):
            continue
        cited = [item.name for item in tools if f"[{item.name}]" in claim]
        if not cited:
            verdicts.append(("check:", f"Unattributed claim: {claim}"))
        elif any(name not in called for name in cited):
            verdicts.append(("check:", f"Citation has no matching evidence row: {claim}"))
        else:
            verdicts.append(("grounded:", f"{', '.join(cited)}: {claim}"))
    return verdicts


def agent_metrics(result):
    llm_calls = 0
    tool_names = []
    token_totals = {"input": 0, "output": 0, "total": 0}
    saw_usage = False
    for message in result["messages"]:
        if message.type == "ai":
            llm_calls += 1
            tool_names.extend(call["name"] for call in message.tool_calls)
            usage = getattr(message, "usage_metadata", None) or {}
            if usage:
                saw_usage = True
                token_totals["input"] += usage.get("input_tokens", 0)
                token_totals["output"] += usage.get("output_tokens", 0)
                token_totals["total"] += usage.get("total_tokens", 0)
    counts = Counter(tool_names)
    repeats = sum(max(0, count - 1) for count in counts.values())
    tokens = token_totals if saw_usage else "N/A (provider returned no usage metadata)"
    return llm_calls, len(tool_names), repeats, tokens


def _tool_trace(result):
    messages = result["messages"]
    outputs = {
        message.tool_call_id: message.content
        for message in messages
        if message.type == "tool"
    }
    rounds = []
    rows = []
    for message in messages:
        if message.type == "ai" and message.tool_calls:
            rounds.append([call["name"] for call in message.tool_calls])
            for call in message.tool_calls:
                rows.append({
                    "tool": call["name"],
                    "args": str(call["args"]),
                    "output": outputs.get(call["id"], "No matching ToolMessage"),
                })
    return rounds, rows


def _run_examples():
    global results, agent_elapsed, tool_rounds, evidence_rows
    results = []
    agent_elapsed = []
    counts = Counter()
    for complaint in complaints:
        started = perf_counter()
        result = agent.invoke(
            {"messages": [HumanMessage(content=complaint)]},
            config={"recursion_limit": 10},
        )
        elapsed = perf_counter() - started
        results.append(result)
        agent_elapsed.append(elapsed)
        print(f"\nComplaint: {complaint}")
        print(f"Answer: {result['messages'][-1].content}")
        rounds, rows = _tool_trace(result)
        order = [name for one_round in rounds for name in one_round]
        counts.update(order)
        print(f"Tool order: {' → '.join(order)}")
        llm_calls, tool_calls, repeats, tokens = agent_metrics(result)
        run_stats.append({
            "elapsed_seconds": elapsed,
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "repeats": repeats,
            "tokens": tokens,
        })
    if results:
        tool_rounds, evidence_rows = _tool_trace(results[0])
    print("Total tool calls:", dict(counts))

    trace_rounds, trace_rows = _tool_trace(results[0])
    trace_answer = results[0]["messages"][-1].content
    for row in trace_rows:
        print(f"Tool: {row['tool']} | Args: {row['args']} | Output: {row['output']}")
    print("Claim attribution:", claim_check(trace_answer, trace_rows))
    print("Structured handler:", structured_handler(complaints[1]))


def _run_extensions():
    print("\nExtension 2: Demogorgon tool")
    print(consult_demogorgon.invoke({"complaint": "My bicycle bell rings by itself."}))

    print("\nExtension 3: separate in-memory threads")
    thread_red = {"configurable": {"thread_id": "complaint-red"}, "recursion_limit": 10}
    thread_blue = {"configurable": {"thread_id": "complaint-blue"}, "recursion_limit": 10}
    memory_demo_agent.invoke(
        {"messages": [HumanMessage(content="Remember my complaint: Christmas lights flicker.")]},
        config=thread_red,
    )
    red_followup = memory_demo_agent.invoke(
        {"messages": [HumanMessage(content="What complaint did I mention?")]},
        config=thread_red,
    )
    memory_demo_agent.invoke(
        {"messages": [HumanMessage(content="Remember my complaint: a portal is in the basement.")]},
        config=thread_blue,
    )
    blue_followup = memory_demo_agent.invoke(
        {"messages": [HumanMessage(content="What complaint did I mention?")]},
        config=thread_blue,
    )
    print("Red thread:", red_followup["messages"][-1].content)
    print("Blue thread:", blue_followup["messages"][-1].content)

    print("\nExtension 5: agent versus structured handler")
    for index, complaint in enumerate(complaints):
        llm_calls, tool_calls, repeats, tokens = agent_metrics(results[index])
        started = perf_counter()
        structured_handler(complaint)
        structured_seconds = perf_counter() - started
        print(f"\nComplaint {index + 1}: {complaint}")
        print(
            f"Agent: time={agent_elapsed[index]:.2f}s, LLM calls={llm_calls}, "
            f"tool calls={tool_calls}, repeated calls={repeats}, tokens={tokens}"
        )
        print(
            f"Structured: time={structured_seconds:.4f}s, LLM calls=0, "
            "tool calls=3, repeated calls=0, tokens=0 (no LLM)"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extensions", action="store_true")
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Add OPENAI_API_KEY to .env before running the complaint examples.")
    _run_examples()
    if args.extensions:
        _run_extensions()

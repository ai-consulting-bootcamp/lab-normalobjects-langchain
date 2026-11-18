"""
NormalObjects - Creative Complaint Handler (LangChain)
LAB | Chaos agent: tools, lore, questionable judgment

A small LangChain 1.0 agent that answers complaints from the "Normal Objects"
(Stranger Things-style) universe by combining four themed tools.

For every complaint the script records:
  - which tools the agent called, in which order, with which arguments
  - the raw output of every tool  (= the evidence)
  - the final answer
  - a simple grounding check: how much of the answer is backed by tool output

Everything is written to lab_run_output.md so a reviewer can trace each
answer back to the tool evidence.

Run:
    pip install -r requirements.txt
    cp .env.example .env        # then add your OPENAI_API_KEY
    python normalobjects_langchain.py
"""

import os
import random
import re
import sys
import time
from collections import Counter
from typing import Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# --------------------------------------------------------------------------
# Step 1: Setup
# --------------------------------------------------------------------------
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
# Agent loop safety: LangGraph counts every model step and every tool step.
# 12 steps ≈ max 5-6 tool rounds (the old AgentExecutor `max_iterations`).
RECURSION_LIMIT = int(os.getenv("RECURSION_LIMIT", "12"))
# Fix the random seed so random tools are reproducible for the proof.
# Set RANDOM_SEED="" in .env to get real chaos.
RANDOM_SEED = os.getenv("RANDOM_SEED", "42")

OUTPUT_FILE = "lab_run_output.md"


# --------------------------------------------------------------------------
# Step 2: Creative tools
# --------------------------------------------------------------------------
@tool
def consult_demogorgon(complaint: str) -> str:
    """Consult the Demogorgon about a complaint involving the Upside Down.

    Use this for complaints about the Upside Down, monsters, or anything
    dark and dimension-related. The answer is chaotic and not reliable.

    Args:
        complaint: The complaint to bring to the Demogorgon.
    """
    responses = [
        f"The Demogorgon tilts its petal-head at '{complaint}', screeches, and knocks over "
        "a bicycle. Interpretation: it does not care, but it is now hungry.",
        f"The Demogorgon drags your complaint '{complaint}' into the Upside Down. "
        "It comes back covered in spores and slightly more valid.",
        f"The Demogorgon responds to '{complaint}' by making every light in the room flicker "
        "in Morse code. It spells: 'N-O-T M-Y P-R-O-B-L-E-M'.",
    ]
    return random.choice(responses)


@tool
def check_hawkins_records(query: str) -> str:
    """Search the official Hawkins records for facts.

    Available topics: portal, monsters, psychics, electricity.
    Use this FIRST when the complaint needs facts.

    Args:
        query: What to look up (include a topic keyword).
    """
    records = {
        "portal": "RECORD H-001: The gate under Hawkins National Laboratory opened in Nov 1983. "
                  "It is sealed by closing it from the inside. Do not approach without Eleven.",
        "monsters": "RECORD H-002: Known entities: Demogorgon, Mind Flayer, Demodogs. "
                    "Weak to fire and loud noises. Cold temperatures make them sluggish.",
        "psychics": "RECORD H-003: Subject 011 ('Eleven') shows telekinesis and remote viewing. "
                    "Powers weaken with stress; nosebleeds are a known side effect. Eggos help.",
        "electricity": "RECORD H-004: Power fluctuations in Hawkins are linked to Upside Down "
                       "activity. Flickering lights indicate an entity nearby. Christmas lights "
                       "can be used for communication.",
    }
    for key, value in records.items():
        if key in query.lower():
            return value
    return (f"NO RECORD FOUND for '{query}'. The Hawkins archive only holds files on: "
            f"{', '.join(records)}. Do not make up official information.")


@tool
def cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str:
    """Cast interdimensional spells that propose creative solutions to a problem.

    Args:
        problem: The problem to solve.
        creativity_level: "low" (1 spell), "medium" (2 spells) or "high" (3 spells).
    """
    multiplier = {"low": 1, "medium": 2, "high": 3}.get(creativity_level.lower(), 2)
    spells = [
        f"🔮 Spell of the Walkie-Talkie: broadcast '{problem}' on channel 11 until someone answers.",
        f"🔮 Christmas Light Ward: string lights around the source of '{problem}' and ask it yes/no questions.",
        f"🔮 Eggo Offering: leave a stack of waffles near '{problem}'; psychic help may follow.",
        f"🔮 Kate Bush Shield: play 'Running Up That Hill' at full volume until '{problem}' loses interest.",
    ]
    n = min(multiplier, len(spells))
    return "\n".join(random.sample(spells, n))


@tool
def gather_party_wisdom(question: str) -> str:
    """Ask the party (Mike, Dustin, Lucas, Will) for advice.

    Topics they know about: plan, science, danger, feelings.

    Args:
        question: The question for the party (include a topic keyword).
    """
    wisdom = {
        "plan": "MIKE: 'We stick together, we make a plan, and we never leave a friend behind. "
                "Friends don't lie.'",
        "science": "DUSTIN: 'Okay, so scientifically speaking, it's about electromagnetism. "
                   "Get me a compass and I'll find the source.'",
        "danger": "LUCAS: 'Bad idea. We scout first, wrist-rocket ready, and we have an exit route.'",
        "feelings": "WILL: 'I can feel it when something's wrong. Trust that feeling, "
                    "and tell someone before it gets worse.'",
    }
    for key, value in wisdom.items():
        if key in question.lower():
            return value
    return ("THE PARTY HUDDLES: 'We don't know yet... but whatever it is, "
            "we face it together. Meet at Castle Byers.'")


TOOLS = [consult_demogorgon, check_hawkins_records, cast_interdimensional_spell, gather_party_wisdom]


# --------------------------------------------------------------------------
# Step 3: Agent with tools
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """You are the NormalObjects Creative Complaint Handler for the town of Hawkins.
Citizens bring you complaints about strange events. Solve them creatively using your tools.

Rules:
- Use check_hawkins_records for FACTS. If it returns NO RECORD FOUND, say that no official
  record exists. Never invent official facts.
- Use the other tools freely and in any order or combination to be creative.
- In your final answer, clearly separate:
    FACTS (from Hawkins records), ADVICE (from the party), and CREATIVE IDEAS (spells / Demogorgon).
- Keep the final answer under 150 words and stay in character, but be helpful."""


def build_agent(model=None):
    """Create the LangChain 1.0 agent (create_agent replaces AgentExecutor)."""
    if model is None:
        model = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    return create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)


# --------------------------------------------------------------------------
# Step 4 + 5: Run complaints and capture the trace
# --------------------------------------------------------------------------
def extract_trace(messages) -> List[Dict]:
    """Pair every tool call with its output from the agent's message history."""
    outputs = {m.tool_call_id: m.content for m in messages if isinstance(m, ToolMessage)}
    trace = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                trace.append({
                    "tool": tc["name"],
                    "args": tc["args"],
                    "output": outputs.get(tc["id"], "<no output>"),
                })
    return trace


STOPWORDS = set("""the and for that this with from your you are was were have has not but they
them their what when where which will would could should about into only than then there
these those because been being just like more most some such very also it's don't""".split())


def content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z']{4,}", text.lower()) if w not in STOPWORDS}


def grounding_check(final_answer: str, trace: List[Dict], complaint: str) -> Dict:
    """Simple, inspectable grounding check.

    support_ratio = share of the answer's content words that appear in a tool output
                    or in the complaint itself. Low ratio → more unsupported text.
    flags         = specific risks we can detect mechanically.
    """
    answer_words = content_words(final_answer)
    evidence_words = set().union(*[content_words(t["output"]) for t in trace]) if trace else set()
    evidence_words |= content_words(complaint)
    supported = answer_words & evidence_words
    ratio = len(supported) / len(answer_words) if answer_words else 0.0

    flags = []
    if not trace:
        flags.append("NO_TOOLS_USED: the whole answer comes from the model, not from evidence.")
    no_record = any(t["tool"] == "check_hawkins_records" and t["output"].startswith("NO RECORD")
                    for t in trace)
    if no_record and re.search(r"\brecord\s+h-\d+", final_answer.lower()):
        flags.append("INVENTED_RECORD: records returned nothing but the answer cites a record ID.")
    if no_record:
        flags.append("NO_RECORD: no official facts were found; check the answer doesn't state any.")
    if not any(t["tool"] == "check_hawkins_records" for t in trace) and "fact" in final_answer.lower():
        flags.append("FACTS_WITHOUT_RECORDS: answer presents 'facts' but never checked the records.")
    if any(t["tool"] in ("consult_demogorgon", "cast_interdimensional_spell") for t in trace):
        flags.append("RANDOM_TOOL: part of the evidence is random; reruns can give a different answer.")
    return {"support_ratio": round(ratio, 2), "unsupported_words": sorted(answer_words - evidence_words)[:15],
            "flags": flags}


def run_complaint(agent, complaint: str) -> Dict:
    start = time.time()
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=complaint)]},
            config={"recursion_limit": RECURSION_LIMIT, "tags": ["normalobjects-lab"]},
        )
        messages = result["messages"]
        final = messages[-1].content
        error = None
    except Exception as e:  # e.g. GraphRecursionError when the agent loops
        messages, final, error = [], "", f"{type(e).__name__}: {e}"
    trace = extract_trace(messages)
    return {
        "complaint": complaint,
        "trace": trace,
        "final": final,
        "error": error,
        "seconds": round(time.time() - start, 2),
        "grounding": grounding_check(final, trace, complaint) if not error else None,
    }


# --------------------------------------------------------------------------
# Comparison: a structured (fixed-order, no-LLM) pipeline
# --------------------------------------------------------------------------
def structured_pipeline(complaint: str) -> Dict:
    """Same tools, fixed order, no model deciding. Fully traceable, but rigid."""
    start = time.time()
    steps = [
        ("check_hawkins_records", {"query": complaint}),
        ("gather_party_wisdom", {"question": complaint}),
        ("cast_interdimensional_spell", {"problem": complaint, "creativity_level": "low"}),
    ]
    by_name = {t.name: t for t in TOOLS}
    trace = [{"tool": n, "args": a, "output": by_name[n].invoke(a)} for n, a in steps]
    final = "\n".join(f"[{t['tool']}] {t['output']}" for t in trace)
    return {"complaint": complaint, "trace": trace, "final": final, "seconds": round(time.time() - start, 3)}


SAMPLE_COMPLAINTS = [
    # 1. Facts + science: records (electricity) and Dustin should be used
    "The lights in my house keep flickering every night and my electricity bill doubled. Is something from the Upside Down nearby?",
    # 2. Monsters + danger: records (monsters), Lucas, maybe Demogorgon
    "A monster keeps eating the pumpkins in my garden. What's the plan and how dangerous is this?",
    # 3. Psychics + feelings: records (psychics), Will
    "My daughter can move spoons with her mind and gets nosebleeds. I have strange feelings about it. Who should I talk to?",
    # 4. Pure creativity: spells + Demogorgon
    "The Demogorgon stole my Walkman. Give me your most creative (high creativity) ideas to get it back.",
    # 5. FAILURE CASE: no matching record/party key → tests whether the agent invents facts
    "The arcade machine at the Palace Arcade keeps eating my quarters. What does the official Hawkins file say about it?",
]


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def format_run(i: int, run: Dict) -> str:
    lines = [f"## Complaint {i}", "", f"**Query:** {run['complaint']}", ""]
    if run["error"]:
        lines += [f"**ERROR:** `{run['error']}`", ""]
        return "\n".join(lines)
    lines += [f"**Tool chain:** {' → '.join(t['tool'] for t in run['trace']) or '(no tools)'}",
              f"**Time:** {run['seconds']} s", "", "### Tool evidence", ""]
    for n, t in enumerate(run["trace"], 1):
        lines += [f"{n}. `{t['tool']}({t['args']})`", "", "```", t["output"], "```", ""]
    g = run["grounding"]
    lines += ["### Final answer", "", run["final"], "",
              "### Grounding check", "",
              f"- Support ratio (answer words found in evidence/complaint): **{g['support_ratio']}**",
              f"- Sample unsupported words: {', '.join(g['unsupported_words']) or '—'}"]
    lines += [f"- ⚠️ {f}" for f in g["flags"]] or ["- No flags"]
    return "\n".join(lines + [""])


def analysis(runs: List[Dict], structured: List[Dict]) -> str:
    ok = [r for r in runs if not r["error"]]
    usage = Counter(t["tool"] for r in ok for t in r["trace"])
    chains = Counter(" → ".join(t["tool"] for t in r["trace"]) for r in ok)
    firsts = Counter(r["trace"][0]["tool"] for r in ok if r["trace"])
    avg_tools = sum(len(r["trace"]) for r in ok) / len(ok) if ok else 0
    avg_agent = sum(r["seconds"] for r in ok) / len(ok) if ok else 0
    avg_struct = sum(s["seconds"] for s in structured) / len(structured) if structured else 0
    avg_support = sum(r["grounding"]["support_ratio"] for r in ok) / len(ok) if ok else 0

    out = ["# Analysis: agent behaviour", "",
           "## Tool usage", "", "| Tool | Calls |", "|---|---|"]
    out += [f"| {name} | {usage.get(name, 0)} |" for name in [t.name for t in TOOLS]]
    out += ["", "## Tool chaining patterns", "", "| Chain | Times |", "|---|---|"]
    out += [f"| {c or '(no tools)'} | {n} |" for c, n in chains.most_common()]
    out += ["", f"- First tool chosen: {dict(firsts)}",
            f"- Average tools per complaint: **{avg_tools:.1f}**",
            f"- Average grounding support ratio: **{avg_support:.2f}**",
            f"- Errors / loops stopped: {len(runs) - len(ok)}", "",
            "## Agent vs structured pipeline", "",
            "| | Agent (LLM decides) | Structured (fixed order) |", "|---|---|---|",
            f"| Avg time | {avg_agent:.2f} s | {avg_struct:.3f} s |",
            f"| Tools per complaint | {avg_tools:.1f} (varies) | 3 (always) |",
            "| Tool choice | adapts to the complaint | same every time, irrelevant tools still run |",
            "| Output | natural, combined answer | raw tool outputs glued together |",
            "| Traceability | needs trace capture | trivial |",
            "| Risk | can skip records or add unsupported text | can't hallucinate, but can't adapt |", "",
            "## Structured pipeline output for the failure case", "",
            "```", structured[-1]["final"] if structured else "", "```", ""]
    return "\n".join(out)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not found. Copy .env.example to .env and add your key.")
    if RANDOM_SEED:
        random.seed(int(RANDOM_SEED))

    agent = build_agent()
    print(f"Agent ready: {MODEL_NAME}, temperature={TEMPERATURE}, tools={[t.name for t in TOOLS]}\n")

    runs = []
    for i, complaint in enumerate(SAMPLE_COMPLAINTS, 1):
        print(f"[{i}/{len(SAMPLE_COMPLAINTS)}] {complaint}")
        run = run_complaint(agent, complaint)
        runs.append(run)
        if run["error"]:
            print(f"   ERROR: {run['error']}\n")
            continue
        print(f"   tools: {' → '.join(t['tool'] for t in run['trace']) or '(none)'}")
        print(f"   answer: {run['final'][:200]}{'...' if len(run['final']) > 200 else ''}")
        print(f"   grounding: {run['grounding']['support_ratio']} | flags: {len(run['grounding']['flags'])}\n")

    structured = [structured_pipeline(c) for c in SAMPLE_COMPLAINTS]

    report = [f"# NormalObjects run log", "",
              f"Model: `{MODEL_NAME}` · temperature {TEMPERATURE} · random seed {RANDOM_SEED or 'none'} · "
              f"recursion limit {RECURSION_LIMIT} · run at {time.strftime('%Y-%m-%d %H:%M')}", ""]
    report += [format_run(i, r) for i, r in enumerate(runs, 1)]
    report.append(analysis(runs, structured))
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(analysis(runs, structured))
    print(f"Full trace written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

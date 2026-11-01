# Lab proof: NormalObjects Creative Complaint Handler (LangChain)

## 1. Code
````python

import os
import random
from typing import List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

load_dotenv()


@tool
def consult_demogorgon(complaint: str) -> str:
    """Consult the Demogorgon about a complaint regarding the Upside Down.
    Use this for complaints about monsters, darkness, or strange dimensions."""
    responses = [
        "The Demogorgon growls and eats your complaint. No refunds.",
        "The Demogorgon tilts its faceless head and shrugs.",
        "The Demogorgon files your complaint in the Upside Down. It will be reviewed in 10,000 years.",
    ]
    return random.choice(responses)


@tool
def check_hawkins_records(query: str) -> str:
    """Search the town archive for a record on one of four topics:
    portal, monsters, psychics, electricity.
    Use this when the complaint mentions one of these topics."""
    records = {
        "portal": "File #A-1: The portal opened in the basement on 6 Nov 1983.",
        "monsters": "File #B-1: Monsters ate kebap on 01 june 1995",
        "psychics": "File #C-1: Psychics were seen dancing on 08 April 1987",
        "electricity": "File #D-1: Electricity was gone all over town on 14 June 1993",
    }
    for key in records:
        if key in query.lower():
            return records[key]
    return "No record found for this query."


@tool
def cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str:
    """Cast spells that propose creative solutions to a problem.
    creativity_level can be low, medium or high (more spells)."""
    levels = {"low": 1, "medium": 2, "high": 3}
    n = levels.get(creativity_level, 2)

    spells = [
        f"makes you bigger {problem}",
        f"show things brighter {problem}",
        f"Make people fall in love {problem}",
        f"Makes your problem disappear 1 hour {problem}",
    ]

    chosen = random.sample(spells, min(n, len(spells)))
    return "\n".join(chosen)

@tool
def gather_party_wisdom(question: str) -> str:
    """Ask the party (Mike, Dustin, Lucas, Will) for advice on school, food, bike or homework questions."""
    wisdom = {
        "school": "Mike says:I hate literature  class",
        "food": "Dustin says: I can eat pasta all day",
        "bike": "Lucas says: that kid rides my bike",
        "homework": "Will says: i still have 3 lab homeworks to finish",
    }
    for key in wisdom:
        if key in question.lower():
            return wisdom[key]
    return "The party huddles and says: let's talk about it together."

tools = [consult_demogorgon, check_hawkins_records, cast_interdimensional_spell, gather_party_wisdom]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

agent = create_agent(
    llm,
    tools=tools,
    system_prompt="You are a creative complaint handler. Use the tools to answer. "
                  "Base facts only on tool outputs and say which tool you used.",
)

query = "My neighbor's pizza oven is too loud, what do the records say?"
result = agent.invoke({"messages": [{"role": "user", "content": query}]})

for m in result["messages"]:
    print(m.type, "|", getattr(m, "tool_calls", ""), "|", m.content) 
    ````

## 2. Query
There was an electricity problem in town, what do the records say?

## 3. Tool evidence
The agent called `check_hawkins_records` with the argument `electricity`. Full trace:

```
human |  | There was an electricity problem in town, what do the records say?
ai | [{'name': 'check_hawkins_records', 'args': {'query': 'electricity'}, 'id': 'call_8SX5jalWCiV0dzakxa9FBDpo', 'type': 'tool_call'}] | 
tool |  | File #D-1: Electricity was gone all over town on 14 June 1993
ai | [] | According to the town archive, there was an electricity problem in Hawkins on June 14, 1993, when electricity was gone all over town. If you have any specific concerns or further questions about thisissue, feel free to ask!
```

## 4. Final output
According to the town archive, there was an electricity problem in Hawkins on June 14, 1993, when electricity was gone all over town. (last sentence trimmed)

The date and "gone all over town" trace back to File #D-1. The word "Hawkins" does not appear in File #D-1.

## 5. Failure or limitation
Query: My neighbor's pizza oven is too loud, what do the records say?

```
human |  | My neighbor's pizza oven is too loud, what do the records say?
ai | [{'name': 'check_hawkins_records', 'args': {'query': 'electricity'}, 'id': 'call_Xydx6yV1BBAuFB7iYvoZ2uTe', 'type': 'tool_call'}] | 
tool |  | File #D-1: Electricity was gone all over town on 14 June 1993
ai | [] | According to the town records, there was an incident on June 14, 1993, when electricity was out all over town. However, there areno specific records concerning loud pizza ovens.
```

1. In the pizza oven query, the agent changed my search term from "pizza oven" to "electricity" by itself, so the tool was asked to search for something I never asked.
2. The tool then returned File #D-1, which is about a blackout in town in 1993 and has nothing to do with a loud pizza oven.
3. The final answer still mentioned that record, so the answer looked supported although the evidence did not match the question.
4. A second weakness is that the tool only matches exact keywords: in my direct test, "monster" did not find "monsters". In the electricity run, the answer also added "Hawkins", which is not in File #D-1.

## 6. Earlier direct tool tests

| Query | Tool | Output |
|---|---|---|
| My basement is too dark | consult_demogorgon | The Demogorgon tilts its faceless head and shrugs. |
| tell me about the portal | check_hawkins_records | File #A-1: The portal opened in the basement on 6 Nov 1983. |
| what about electricity | check_hawkins_records | File #D-1: Electricity was gone all over town on 14 June 1993 |
| what about pizza | check_hawkins_records | No record found for this query. |
| I saw a monster | check_hawkins_records | No record found for this query. |

Note: consult_demogorgon picks one of three lines at random, so its output changes between runs.
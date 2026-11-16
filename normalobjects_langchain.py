import random

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_cohere import ChatCohere
from langchain_core.tools import tool


@tool
def consult_demogorgon(complaint: str) -> str:
    """Consulta al Demogorgon sobre quejas relacionadas con el Upside Down (el mundo del revés)."""
    respuestas = [
        "El Demogorgon se ha cansado de responderte y quiere dormir.",
        "Lo siento, pero el Demogorgon no está: se fue a buscar a 11.",
        "Como vuelvas a molestarme por una queja estúpida, te haré pedazos.",
    ]
    return random.choice(respuestas)


@tool
def check_hawkins_records(query: str) -> str:
    """Busca en los registros oficiales de Hawkins sobre el portal, monstruos, psíquicos o electricidad."""
    registros = {
        "portal": "Registro 1983: se abrió un portal al Upside Down bajo el laboratorio de Hawkins.",
        "monsters": "Registro 1984: avistamientos de criaturas sin cara en el bosque de Hawkins.",
        "psychics": "Registro 1983: una niña con poderes mentales escapó del laboratorio.",
        "electricity": "Registro 1985: los apagones coinciden con la actividad del portal.",
    }
    for tema in registros:
        if tema in query.lower():
            return registros[tema]
    return "No se ha encontrado ningún registro sobre eso en los archivos de Hawkins."


@tool
def cast_interdimensional_spell(problem: str, creativity_level: str = "medium") -> str:
    """Lanza hechizos interdimensionales para resolver un problema. creativity_level puede ser "low", "medium" o "high"."""
    niveles = {"low": 1, "medium": 2, "high": 3}
    cantidad = niveles.get(creativity_level, 2)
    hechizos = [
        f"Hechizo de inversión: lleva {problem} al Upside Down y déjalo allí.",
        f"Conjuro de luces: deletrea {problem} con bombillas hasta que desaparezca.",
        f"Ritual de los gofres: ofrece gofres a Eleven para que cierre {problem} con la mente.",
        f"Hechizo walkie-talkie: transmite {problem} por el canal 11 y espera respuesta.",
    ]
    cantidad = min(cantidad, len(hechizos))
    elegidos = random.sample(hechizos, cantidad)
    return "\n".join(elegidos)


@tool
def gather_party_wisdom(question: str) -> str:
    """Pide consejo al grupo de amigos (Mike, Dustin, Lucas y Will) sobre monstruos, el portal, la electricidad o un plan."""
    consejos = {
        "monster": "Lucas: Ni se te ocurra enfrentarte a él solo. Ve con el tirachinas cargado.",
        "portal": "Will: Yo he estado al otro lado. No lo cruces, hace mucho frío.",
        "electricity": "Dustin: Si las luces parpadean, algo se acerca. Es pura ciencia.",
        "plan": "Mike: Nos vemos en el sótano a las siete. Traed los walkie-talkies.",
    }
    for tema in consejos:
        if tema in question.lower():
            return consejos[tema]
    return "El grupo se reúne en piña, discute un buen rato… y no se pone de acuerdo."


load_dotenv()

model = ChatCohere(model="command-a-03-2025", temperature=0.7)

agent = create_agent(
    model=model,
    tools=[consult_demogorgon, check_hawkins_records, cast_interdimensional_spell, gather_party_wisdom],
    system_prompt=(
        "Eres un empleado de atención al cliente del pueblo de Hawkins. "
        "Ante cada queja, consulta al menos una de tus herramientas y combina lo que te devuelvan "
        "en una respuesta creativa y divertida. "
        "No inventes hechos ni registros que no vengan de una herramienta. "
        "Si no encuentran nada, dilo claramente en lugar de seguir buscando."
    ),
)

queja = "The portal monsters cut my electricity"

resultado = agent.invoke(
    {"messages": [{"role": "user", "content": queja}]},
    config={"recursion_limit": 10},
)

for mensaje in resultado["messages"]:
    print("----", mensaje.type.upper())
    if mensaje.content:
        print(mensaje.content)
    for llamada in getattr(mensaje, "tool_calls", []) or []:
        print("PIDE HERRAMIENTA:", llamada["name"], "| CON DATOS:", llamada["args"])

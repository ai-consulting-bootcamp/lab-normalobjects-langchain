# Lab proof — Chaos agent: tools, lore, questionable judgment

**Archivo principal:** `normalobjects_langchain.py`
**Fecha de las pruebas:** 4/11/2026

---

## 1. Código y flujo

### Herramientas (`@tool`)

| Herramienta | Recibe | Hace | Devuelve |
|---|---|---|---|
| `consult_demogorgon` | `complaint: str` | Elige 1 de 3 respuestas con `random.choice()` | Una frase del Demogorgon |
| `check_hawkins_records` | `query: str` | Recorre 4 claves (`portal`, `monsters`, `psychics`, `electricity`) y comprueba si alguna aparece en la consulta (con `.lower()`) | El registro de la primera coincidencia o "No se ha encontrado ningún registro…" |
| `cast_interdimensional_spell` | `problem: str`, `creativity_level: str = "medium"` | Traduce el nivel a 1/2/3 y elige ese número de hechizos con `random.sample()`, con un tope de la longitud de la lista | Los hechizos, uno por línea |
| `gather_party_wisdom` | `question: str` | Recorre 4 claves (`monster`, `portal`, `electricity`, `plan`) igual que la herramienta de Hawkins | El consejo de Mike, Dustin, Lucas o Will, o el mensaje de "huddle" |

### Agente

- `create_agent(model, tools, system_prompt)`, el enfoque moderno de LangChain 1.x.
- `recursion_limit = 10` para cortar posibles bucles (el equivalente moderno de `max_iterations`).
- **System prompt:** empleado de atención al cliente de Hawkins. Debe consultar al menos una herramienta, no inventar hechos y, si no encuentra nada, decirlo en lugar de seguir buscando.

### Flujo de una petición

```
HUMAN (queja) → AI (el modelo PIDE herramienta + argumentos)
             → TOOL (Python EJECUTA la función y devuelve texto)
             → AI (el modelo redacta la respuesta final)
```

La traza se imprime recorriendo `resultado["messages"]`: tipo de mensaje, contenido y `tool_calls` (nombre y argumentos).

### Desviaciones del enunciado

- **Modelo:** el enunciado pide OpenAI. Se usó **Cohere `command-a-03-2025`** con cuenta gratuita, para no tener coste. LangChain permite cambiar de proveedor cambiando solo el modelo; herramientas, agente y prompt no cambian.
- **API del agente:** se usa `create_agent` en lugar de `AgentExecutor` / `create_openai_tools_agent`, que están obsoletos desde LangChain 1.0. Por eso no hacen falta `ChatPromptTemplate` ni `MessagesPlaceholder`.

---

## 2. Prueba 1 — consulta en español (fallo)

- **Consulta:** "Los monstruos del portal me han cortado la electricidad de casa"
- **Herramienta pedida por el modelo:** `check_hawkins_records` con `{'query': 'electricidad'}`
- **Salida de la herramienta (TOOL):** "No se ha encontrado ningún registro sobre eso en los archivos de Hawkins."
- **Respuesta final (AI):** "Lo siento, no he encontrado información sobre la electricidad en Hawkins."

## 3. Prueba 2 — consulta en inglés

- **Consulta:** "The portal monsters cut my electricity"
- **Herramienta pedida por el modelo:** `consult_demogorgon` con `{'complaint': 'The portal monsters cut my electricity'}`
- **Salida de la herramienta (TOOL):** "El Demogorgon se ha cansado de responderte y quiere dormir."
- **Respuesta final (AI):** "The Demogorgon is tired of answering your questions and wants to sleep."

### Pruebas previas de las herramientas sin modelo (`.invoke`, sin coste)

| Herramienta | Entrada | Resultado real |
|---|---|---|
| `check_hawkins_records` | "problemas de electricity en casa" | Registro 1985 |
| `check_hawkins_records` | "problemas de electricidad en casa" | No encontrado |
| `check_hawkins_records` | "me ha atacado un monster" | No encontrado |
| `check_hawkins_records` | "hay monsters saliendo del portal" | Registro del portal (primera clave que coincide) |
| `cast_interdimensional_spell` | "el apagón de mi casa", `high` | 3 hechizos distintos con el problema dentro |
| `gather_party_wisdom` | "the monsters attacked me" | Lucas |
| `gather_party_wisdom` | "me duele la cabeza" | Mensaje de "huddle" |
| `consult_demogorgon` | 8 ejecuciones | Frases variadas (azar confirmado) |

---

## 4. Conclusiones: `check_hawkins_records`

### 4.1. Funcionamiento del buscador secuencial
Hemos comprobado que el código funciona como un archivero cuadriculado. Sigue una lógica puramente mecánica dividida en tres pasos:
* **Normalización a minúsculas:** Al aplicar `.lower()`, evitamos fallos por culpa de las mayúsculas. El programa procesa "ELECTRICITY" y "electricity" exactamente igual.
* **Revisión en orden:** El bucle `for` actúa como un dedo que señala un cajón a la vez en una cómoda de 4 compartimentos (`portal`, `monsters`, `psychics`, `electricity`).
* **Frenazo inmediato:** En el momento en que hay coincidencia (`if tema in query.lower()`), la función ejecuta el `return`, entrega la frase correspondiente y se detiene por completo sin revisar los cajones restantes.

### 4.2. Limitaciones del sistema rígido (coincidencia exacta)
Las pruebas en el laboratorio han evidenciado el mayor defecto de este enfoque: el código no piensa ni entiende el contexto, solo compara caracteres idénticos.
* **El fallo del plural:** Si buscamos la frase *"me ha atacado un monster"*, el programa devuelve el error de "No encontrado". Para una persona es obvio lo que significa, pero la máquina busca la palabra exacta `monsters` (con S). Al faltarle una letra, el condicional da falso.
* **El fallo del idioma:** Si el usuario introduce la palabra en español (*"electricidad"*), el buscador se pierde. No sabe relacionarla con la etiqueta en inglés (`electricity`) porque no tiene capacidad de traducción.

### 4.3. Lección de código: la importancia de la sangría
El laboratorio nos ha dejado claro que la estructura visual en Python es vital para la lógica:
* Colocar el último `return` (el mensaje de no encontrado) alineado con el `for` (fuera del bucle) es lo que garantiza que se revisen los cuatro registros antes de tirar la toalla. Si lo hubiéramos metido dentro, el código se habría rendido tras mirar únicamente la primera carpeta.

---

## 5. Verificación: ¿dónde podría el sistema dar una respuesta creíble sin respaldo?

Cuando `check_hawkins_records` devuelve «No encontrado» (por ejemplo, con «monster» en singular o con «electricidad» en español), el LLM puede rellenar el hueco con lo que sabe de *Stranger Things* y dar una respuesta convincente que no sale de ningún registro. Lo mismo ocurre si el agente contesta sin llamar a la herramienta: la respuesta suena segura, pero en la traza no aparece ninguna llamada que la respalde.

---

## 6. Uso de IA (Prompt Discipline)

- **Alumno:** estructura y frases de `consult_demogorgon`; decisiones del system prompt (rol, uso obligatorio de herramientas, no inventar, no hacer bucles); elección del proveedor gratuito; predicciones; ejecución de las pruebas; conclusiones de la sección 4.
- **Sección 5:** redactada por el asistente de IA a petición del alumno, a partir de las conclusiones del alumno en la sección 4.
- **Asistente de IA (tutor):** corrección de errores; código de las herramientas 2–4 y del agente a partir del enunciado, que el alumno revisó, probó y validó; reordenación de los imports; montaje de este documento con los resultados reales del terminal.

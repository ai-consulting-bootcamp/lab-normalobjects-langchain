# Lab Proof: NormalObjects Creative Complaint Handler

## 1. What I built
Construí un agente con LangChain que recibe una queja, elige entre las herramientas disponibles y genera una respuesta a partir de sus resultados.

Tiene cuatro herramientas: consultar registros ficticios de Hawkins, obtener opiniones poco fiables del Demogorgon, proponer hechizos ficticios y consultar consejos del grupo.

El código está en Lab_normalobjects_langchain.ipynb. Lo comparé con un flujo estructurado que siempre llama a registros → grupo → hechizo, sin utilizar un modelo para elegir herramientas ni redactar la respuesta.

## 2. Query
There is a weird portal in my basement. What's the plan?

## 3. Tool evidence (calls + args + outputs)
TOOL CALL: check_hawkins_records
ARGS: {'query': 'portal in basement'}
CALL ID: call_4lllqoxO7oiL4xKpFTZGyDP0

TOOL CALL: gather_party_wisdom
ARGS: {'question': 'What to do with a weird portal?'}
CALL ID: call_FC07AqIjllhjHgWFozOcXIZ0

TOOL OUTPUT: check_hawkins_records
CALL ID: call_4lllqoxO7oiL4xKpFTZGyDP0
CONTENT: A rift in Hawkins Lab opened a gateway to a dark parallel dimension.

TOOL OUTPUT: gather_party_wisdom
CALL ID: call_FC07AqIjllhjHgWFozOcXIZ0
CONTENT: The party huddles together to discuss the question.

## 4. Final output
FINAL ANSWER:
According to Hawkins records, there have been instances where a rift opened a gateway to a dark parallel dimension. This suggests that your weird portal may be connected to similar phenomena.
As for what to do with it, the party wisdom is mixed, but here are some general suggestions: 

1. **Avoid it**: Stay clear of the portal until you gather more information.
2. **Investigate safely**: If you're feeling brave, consider exploring it with protective gear and some friends.
3. **Reach out for help**: Contact someone knowledgeable about the Upside Down or portals.

Without more specific evidence about your situation, these are the best initial steps. 

Tools used: 
- check_hawkins_records
- gather_party_wisdom

## 5. Trace (which claim comes from which tool output?)
El registro respalda que una grieta en Hawkins Lab abrió un acceso a otra dimensión. Sin embargo, ningún resultado demuestra una conexión con el portal del sótano. El mensaje del grupo no respalda “the party wisdom is mixed” ni las tres recomendaciones.

## 6. Failure or limitation
Que usar una herramienta no garantiza que la respuesta esté respaldada. Además, algunas herramientas devuelven opiniones o soluciones ficticias.
Por ejemplo: el agente recomendó explorar con equipo y amigos, aunque ninguna herramienta devolvió ese consejo. Ello también ocurrió pese a la instrucción de responder solo desde los resultados.


## 7. Agent vs. structured handler  
| | Agent | Structured |
|---|---|---|
| Same tools every run? |eligió herramientas diferentes según la queja en las pruebas realizadas| el flujo fijo siempre llama a las mismas tres herramientas.|
| Tool order predictable? |decide qué llamar; no tiene ese orden obligatorio. | registros → grupo → hechizo|
| Can invent facts? |añadió consejos sin respaldo | devuelve los textos de las herramientas sin ampliarlos, aunque esos textos contienen ficción. |
| Easy to trace? |necesitamos inspeccionar sus llamadas, argumentos y resultados |es más directo de revisar porque tiene tres llamadas explícitas |
| Best for which client case? |Consultas variadas que requieren elegir herramientas según la necesidad del cliente |Procesos que deben seguir siempre pasos obligatorios en un orden definido |

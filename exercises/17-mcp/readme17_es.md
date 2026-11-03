# Ejercicio 17: Convierte tu API REST en un servidor MCP

## Objetivo
Convertir la API de Notas del ejercicio 05 en un **servidor MCP**, para que cualquier asistente de IA compatible con MCP (Claude, VS Code, Cursor...) pueda listar, leer y crear notas a través de **tu** API, con **tu** autenticación y tus límites.

## Descripción
El Model Context Protocol (MCP) es un estándar abierto para conectar aplicaciones de IA con herramientas y datos. Un servidor MCP expone **tools** (acciones que el modelo puede pedir), **resources** (datos que puede leer) y **prompts**. Por debajo es JSON-RPC sobre stdio o HTTP: al final, todo son APIs.

```
App de IA (cliente MCP)  --JSON-RPC (stdio)-->  mcp_server.py  --HTTP + X-API-Key-->  notes_api.py
 asistente / IDE                                tu servidor MCP                         tu API REST
```

El patrón más habitual en las empresas es justo este: **ya tienes una API REST y la envuelves** como servidor MCP. Cada tool es una pequeña función de Python que llama a un endpoint. El modelo elige la tool y sus argumentos; tu código hace la llamada HTTP, así que el modelo nunca tiene tus credenciales.

Para el ejercicio principal no necesitas ningún LLM ni ninguna API key de pago: pruebas el servidor con un cliente pequeño (`client.py`) o con el **MCP Inspector**, que te enseñan exactamente lo que vería un asistente.

Completa los huecos (`_____`) de `mcp_server.py`.

## Inicio Rápido

```bash
cd exercises/17-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1: la API REST (completa, no hay nada que rellenar)
fastapi dev notes_api.py

# Terminal 2: prueba tu servidor MCP
python client.py
```

> Necesitas **Python 3.12 o superior** (el mismo que el resto del curso; el paquete `mcp` no funciona con versiones antiguas).

## Ficheros

| Fichero | Qué es |
|---------|--------|
| `notes_api.py` | La API de Notas del ejercicio 05, con una API key opcional. **No hay nada que rellenar.** |
| `mcp_server.py` | Tu servidor MCP. **Completa aquí los huecos.** |
| `client.py` | Un cliente MCP mínimo para probar tu servidor sin asistente de IA. |
| `example/example17.py` | La solución (¡inténtalo antes!). |

## Requisitos

1. **Dependencias:** `FastAPI`, `httpx` (cliente HTTP) y `mcp` (el SDK oficial de Python, versión 2). Ver `requirements.txt`.

2. **Tools que hay que exponer:**

   | Tool | Llama a | ¿Cambia datos? |
   |------|---------|----------------|
   | `list_notes(limit=10)` | `GET /notes?limit=` | No (`read_only_hint=True`) |
   | `get_note(note_id)` | `GET /notes/<id>` | No (`read_only_hint=True`) |
   | `create_note(title, content="")` | `POST /notes` | Sí |
   | `delete_note(note_id)` | `DELETE /notes/<id>` | Sí, destructiva. **Solo se expone si `NOTES_ALLOW_DELETE=1`** |

3. **Un resource:** `notes://{note_id}` devuelve una nota en JSON (ya está implementado).

4. **El transporte es stdio:** el asistente arranca `mcp_server.py` como subproceso y habla con él por stdin/stdout.

## Pasos Sugeridos

1. **Lee `mcp_server.py`:**
   - `call_api()` es el único sitio que habla HTTP. Envía la API key, pone un `timeout` y convierte los errores RFC 9457 (`404`, `422`...) en un `ToolError` cuyo mensaje puede leer el modelo.
   - `list_notes` está completa: úsala de modelo para las demás. Fíjate en que el **docstring** es la descripción que lee el modelo, y los **type hints** (`limit: int = 10`) se convierten en el JSON Schema de los parámetros. Una buena especificación OpenAPI se traduce casi directamente en definiciones de tools.

2. **Rellena los huecos (`_____`):**

   ```python
   # La cabecera que espera la API de Notas (mira check_api_key en notes_api.py)
   headers = {'_____': NOTES_API_KEY} if NOTES_API_KEY else {}

   # get_note: ¿cambia algo? ¿Qué método HTTP lee una nota?
   @mcp.tool(annotations=ToolAnnotations(read_only_hint=_____))
   return call_api('_____', f'/notes/{note_id}')

   # create_note: regístrala como tool, descríbela para el modelo y elige el método
   @mcp._____()
   """_____"""
   return call_api('_____', '/notes', json=...)

   # El transporte de un servidor que el cliente arranca como subproceso
   mcp.run(transport='_____')
   ```

3. **Prueba con `client.py`** (la API de Notas tiene que estar en marcha en otra terminal):

   ```bash
   python client.py                        # tu mcp_server.py
   python client.py example/example17.py   # la solución
   ```

   Hace lo mismo que un asistente por detrás: `tools/list`, luego `tools/call` sobre algunas tools y `resources/read`. Salida esperada (resumida):

   ```
   tools/list -> what the model would see:
     - list_notes(limit): List the most recent notes, newest first. ...
     - get_note(note_id): Get one note by its id, with its full content.
     - create_note(title, content): Create a new note. ...

   tools/call get_note {"note_id": 999}  (does not exist)
     ERROR (the model reads this): Error executing tool get_note: 404: Note 999 does not exist.

   delete_note is NOT exposed (NOTES_ALLOW_DELETE is off)
   ```

   > Las líneas con hora e `INFO` (`HTTP Request: GET ...`) son el log del servidor por stderr: cada una es una llamada HTTP real a la API de Notas.
   >
   > Si `client.py` termina con un traceback largo y `MCPError: Connection closed`, tu servidor ha fallado al arrancar: el error real de Python (por ejemplo `NameError: name '_____' is not defined`) aparece al principio. También puedes ejecutar `python mcp_server.py` solo para verlo (si arranca bien, se queda esperando JSON-RPC por stdin: páralo con `Ctrl+C`). Si la API de Notas no está en marcha, cada llamada a una tool o a un resource imprime una línea `ERROR` (`Cannot reach the Notes API at http://127.0.0.1:8000: ...`): arráncala en la Terminal 1 y vuelve a ejecutar el cliente.

4. **Prueba con el MCP Inspector** (necesita [Node.js](https://nodejs.org/)): una interfaz web donde listas las tools, las llamas a mano y ves cada mensaje JSON-RPC.

   ```bash
   npx @modelcontextprotocol/inspector python mcp_server.py
   ```

   Ejecútalo con el venv activado: el `python` de ese comando tiene que ser el del venv (en Windows, un `python` a secas apunta si no a un intérprete global sin `mcp` y el Inspector muestra `Connection Error`). Se abre en el navegador. Pulsa **Connect**, luego **Tools → List Tools**, elige `create_note`, rellena el formulario y pulsa **Run Tool**. Comprueba en la Terminal 1 que la API de Notas recibió un `POST /notes` de verdad.

## Resultados Esperados

- `tools/list` muestra `list_notes`, `get_note` y `create_note`, cada una con una descripción clara y sus parámetros.
- Llamar a `create_note` crea una nota real en la API de Notas (`GET /notes` la muestra).
- Los errores de la API llegan al modelo como mensajes legibles (`404: Note 999 does not exist.`), no como un fallo.
- `delete_note` **no** aparece salvo que arranques el servidor con `NOTES_ALLOW_DELETE=1`.

## Retos Adicionales

### 1. La API key se queda en el servidor

Arranca la API de Notas con una key. Ahora cualquier petición sin ella recibe `401`:

```bash
# Linux/macOS
export NOTES_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Windows PowerShell
$env:NOTES_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"

fastapi dev notes_api.py
curl -i http://127.0.0.1:8000/notes      # 401 Unauthorized (Linux/macOS)
curl.exe -i http://127.0.0.1:8000/notes    # 401 Unauthorized (Windows PowerShell)
```

Ejecuta `python client.py` **en una terminal donde `NOTES_API_KEY` tenga el mismo valor**: funciona, porque `mcp_server.py` lee la key de su entorno y añade la cabecera `X-API-Key`. Mira `tools/list`: la key no aparece por ningún sitio. El modelo puede usar tu API, pero nunca ve tus credenciales.

### 2. Mínimo privilegio: borrar solo si se activa

Pon `NOTES_ALLOW_DELETE=1` (`export NOTES_ALLOW_DELETE=1` en Linux/macOS, `$env:NOTES_ALLOW_DELETE = "1"` en Windows PowerShell) y vuelve a ejecutar `client.py`: ahora aparece `delete_note`, marcada con `destructive_hint=True` (los asistentes lo usan para pedir confirmación al usuario). Piénsalo: ¿qué tools expondrías a un asistente que usa toda tu empresa?

### 3. Úsalo desde un asistente de IA real

Conecta el servidor a un asistente y pide en lenguaje natural: *"Crea una nota llamada 'Repasar JWT' con el contenido 'refresh tokens e iss/aud'"*, y luego *"¿Cuáles son mis últimas notas?"*. Usa **rutas absolutas** y el Python de tu venv.

- **Claude Desktop:** Settings → Developer → Edit Config (`claude_desktop_config.json`):

  ```json
  {
    "mcpServers": {
      "notes": {
        "command": "C:\\ruta\\a\\17-mcp\\venv\\Scripts\\python.exe",
        "args": ["C:\\ruta\\a\\17-mcp\\mcp_server.py"],
        "env": { "NOTES_API_KEY": "la-misma-key-que-la-api" }
      }
    }
  }
  ```

- **Claude Code:** un solo comando, ejecutado en la carpeta en la que trabajes (`-e` pasa la key al entorno del servidor):

  ```bash
  claude mcp add notes -e NOTES_API_KEY=la-misma-key-que-la-api -- C:\ruta\a\17-mcp\venv\Scripts\python.exe C:\ruta\a\17-mcp\mcp_server.py
  ```

  Guarda la misma entrada `mcpServers` que Claude Desktop (en `~/.claude.json`, solo para esta carpeta); para compartirla con el proyecto, pon ese JSON en un fichero `.mcp.json` en la raíz del proyecto. Compruébalo con `claude mcp list`.

- **Cursor:** el mismo JSON `mcpServers` que Claude Desktop, en `.cursor/mcp.json` (este proyecto) o `~/.cursor/mcp.json` (todos los proyectos).

- **VS Code (modo agente de Copilot):** crea `.vscode/mcp.json` en la carpeta que abras:

  ```json
  {
    "servers": {
      "notes": {
        "type": "stdio",
        "command": "C:\\ruta\\a\\17-mcp\\venv\\Scripts\\python.exe",
        "args": ["C:\\ruta\\a\\17-mcp\\mcp_server.py"]
      }
    }
  }
  ```

El bloque `env` (o `-e`) solo hace falta si arrancaste la API de Notas con `NOTES_API_KEY` (reto 1). La API de Notas tiene que seguir en marcha en su propia terminal: el asistente solo arranca el servidor MCP.

### 4. Añade un prompt o una tool nueva

- Añade una tool `update_note(note_id, title=None, content=None)` que llame a `PATCH /notes/<id>` (envía solo los campos que no sean `None`).
- Añade un prompt con `@mcp.prompt()` que devuelva una instrucción ya preparada, por ejemplo *"Resume mis 5 últimas notas en 3 puntos"*.

## Entendiendo MCP

### Tools, resources y prompts

| Primitiva | Quién decide usarla | Ejemplo aquí |
|-----------|---------------------|--------------|
| **Tool** | El **modelo** (pide al cliente que la llame) | `create_note` |
| **Resource** | La **aplicación/el usuario** (se adjunta como contexto) | `notes://1` |
| **Prompt** | El **usuario** (elige una plantilla) | Reto 4 |

### Por qué stdout es sagrado

Con el transporte stdio, **stdout lleva los mensajes JSON-RPC**. Un `print("hola")` suelto corrompe el flujo: el cliente recibe una línea que no es JSON-RPC (`client.py` registra `Failed to parse JSONRPC message from server`; otros clientes pueden desconectarse). Escribe los logs en **stderr** (`print(..., file=sys.stderr)`), como hace el fichero de partida.

### Las mismas reglas que cualquier cliente de una API

Un servidor MCP es solo otro cliente de tu API. Todo lo visto en el curso sigue valiendo: mínimo privilegio (expón solo las tools necesarias), validación (la API sigue devolviendo `422`), autenticación (la key vive en el servidor), rate limits y logging.

## Recursos Adicionales

- [Model Context Protocol: introducción](https://modelcontextprotocol.io/docs/getting-started/intro)
- [SDK de MCP para Python](https://github.com/modelcontextprotocol/python-sdk) y su [guía de migración a v2](https://py.sdk.modelcontextprotocol.io/v2/migration/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Especificación de MCP](https://modelcontextprotocol.io/specification)

## Notas

- La API de Notas guarda todo en memoria: las notas creadas por MCP se pierden al reiniciar `notes_api.py`.
- Este ejercicio usa la versión 2 del paquete `mcp` (`from mcp.server.mcpserver import MCPServer`). Muchos tutoriales en Internet siguen mostrando la versión 1 (`from mcp.server.fastmcp import FastMCP`): la idea es la misma, pero el import cambia.

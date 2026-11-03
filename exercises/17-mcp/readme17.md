# Exercise 17: Wrap Your REST API as an MCP Server

## Objective
Turn the Notes API from exercise 05 into an **MCP server**, so that any MCP-compatible AI assistant (Claude, VS Code, Cursor...) can list, read and create notes through **your** API, with **your** authentication and limits.

## Description
The Model Context Protocol (MCP) is an open standard to connect AI applications to tools and data. An MCP server exposes **tools** (actions the model can ask for), **resources** (data it can read) and **prompts**. Under the hood it is JSON-RPC over stdio or HTTP: it's APIs all the way down.

```
AI app (MCP client)  --JSON-RPC (stdio)-->  mcp_server.py  --HTTP + X-API-Key-->  notes_api.py
 assistant / IDE                            your MCP server                         your REST API
```

The most common pattern in real companies is exactly this one: **you already have a REST API, and you wrap it** as an MCP server. Each tool is a small Python function that calls an endpoint. The model chooses the tool and its arguments; your code makes the HTTP call, so the model never holds your credentials.

You don't need an LLM or any paid API key for the main exercise: you test the server with a small client (`client.py`) or with the **MCP Inspector**, which show you exactly what an assistant would see.

Complete the blanks (`_____`) in `mcp_server.py`.

## Quick Start

```bash
cd exercises/17-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1: the REST API (complete, nothing to fill in)
fastapi dev notes_api.py

# Terminal 2: test your MCP server
python client.py
```

> Requires **Python 3.12 or newer** (the same as the rest of the course; the `mcp` package does not support old versions).

## Files

| File | What it is |
|------|------------|
| `notes_api.py` | The Notes API from exercise 05, plus an optional API key. **Nothing to fill in.** |
| `mcp_server.py` | Your MCP server. **Complete the blanks here.** |
| `client.py` | A minimal MCP client to test your server without an AI assistant. |
| `example/example17.py` | The solution (try first!). |

## Requirements

1. **Dependencies:** `FastAPI`, `httpx` (HTTP client) and `mcp` (the official Python SDK, version 2). See `requirements.txt`.

2. **Tools to expose:**

   | Tool | Calls | Changes data? |
   |------|-------|---------------|
   | `list_notes(limit=10)` | `GET /notes?limit=` | No (`read_only_hint=True`) |
   | `get_note(note_id)` | `GET /notes/<id>` | No (`read_only_hint=True`) |
   | `create_note(title, content="")` | `POST /notes` | Yes |
   | `delete_note(note_id)` | `DELETE /notes/<id>` | Yes, destructive. **Only exposed if `NOTES_ALLOW_DELETE=1`** |

3. **One resource:** `notes://{note_id}` returns one note as JSON (already implemented).

4. **The transport is stdio:** the assistant starts `mcp_server.py` as a subprocess and talks to it through stdin/stdout.

## Suggested Steps

1. **Read `mcp_server.py`:**
   - `call_api()` is the only place that talks HTTP. It sends the API key, sets a `timeout`, and turns RFC 9457 errors (`404`, `422`...) into a `ToolError` whose message the model can read.
   - `list_notes` is complete: use it as your model for the others. Notice that the **docstring** is the description the model reads, and the **type hints** (`limit: int = 10`) become the JSON Schema of the parameters. A good OpenAPI spec translates almost directly into tool definitions.

2. **Fill in the blanks (`_____`):**

   ```python
   # The header the Notes API expects (see check_api_key in notes_api.py)
   headers = {'_____': NOTES_API_KEY} if NOTES_API_KEY else {}

   # get_note: does it change anything? Which HTTP method reads one note?
   @mcp.tool(annotations=ToolAnnotations(read_only_hint=_____))
   return call_api('_____', f'/notes/{note_id}')

   # create_note: register it as a tool, describe it for the model, and pick the method
   @mcp._____()
   """_____"""
   return call_api('_____', '/notes', json=...)

   # The transport for a server that the client starts as a subprocess
   mcp.run(transport='_____')
   ```

3. **Test with `client.py`** (the Notes API must be running in another terminal):

   ```bash
   python client.py                        # your mcp_server.py
   python client.py example/example17.py   # the solution
   ```

   It does what an assistant does behind the scenes: `tools/list`, then `tools/call` on some tools, and `resources/read`. Expected output (abridged):

   ```
   tools/list -> what the model would see:
     - list_notes(limit): List the most recent notes, newest first. ...
     - get_note(note_id): Get one note by its id, with its full content.
     - create_note(title, content): Create a new note. ...

   tools/call get_note {"note_id": 999}  (does not exist)
     ERROR (the model reads this): Error executing tool get_note: 404: Note 999 does not exist.

   delete_note is NOT exposed (NOTES_ALLOW_DELETE is off)
   ```

   > The lines with a timestamp and `INFO` (`HTTP Request: GET ...`) are the server's log on stderr: each one is a real HTTP call to the Notes API.
   >
   > If `client.py` ends with a long traceback and `MCPError: Connection closed`, your server crashed on start-up: the real Python error (for example `NameError: name '_____' is not defined`) is printed at the top. You can also run `python mcp_server.py` on its own to see it (if it starts fine, it just waits for JSON-RPC on stdin: stop it with `Ctrl+C`). If the Notes API is not running, every tool and resource call prints an `ERROR` line (`Cannot reach the Notes API at http://127.0.0.1:8000: ...`): start it in Terminal 1 and run the client again.

4. **Test with the MCP Inspector** (needs [Node.js](https://nodejs.org/)): a web UI where you list tools, call them by hand and see every JSON-RPC message.

   ```bash
   npx @modelcontextprotocol/inspector python mcp_server.py
   ```

   Run it with the venv activated: the `python` in that command must be the venv's (on Windows, a bare `python` otherwise resolves to a global interpreter without `mcp` and the Inspector shows `Connection Error`). It opens in the browser. Click **Connect**, then **Tools → List Tools**, choose `create_note`, fill in the form and **Run Tool**. Check in Terminal 1 that the Notes API received a real `POST /notes`.

## Expected Results

- `tools/list` shows `list_notes`, `get_note` and `create_note`, each with a clear description and its parameters.
- Calling `create_note` creates a real note in the Notes API (`GET /notes` shows it).
- Errors from the API reach the model as readable messages (`404: Note 999 does not exist.`), not as a crash.
- `delete_note` does **not** appear unless you start the server with `NOTES_ALLOW_DELETE=1`.

## Stretch Goals

### 1. Keep the API key on the server

Start the Notes API with a key. Now every request without it gets `401`:

```bash
# Linux/macOS
export NOTES_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
# Windows PowerShell
$env:NOTES_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"

fastapi dev notes_api.py
curl -i http://127.0.0.1:8000/notes      # 401 Unauthorized (Linux/macOS)
curl.exe -i http://127.0.0.1:8000/notes    # 401 Unauthorized (Windows PowerShell)
```

Run `python client.py` **in a terminal where `NOTES_API_KEY` is set to the same value**: it works, because `mcp_server.py` reads the key from its environment and adds the `X-API-Key` header. Look at `tools/list`: the key appears nowhere. The model can use your API, but it never sees your credentials.

### 2. Least privilege: opt-in delete

Set `NOTES_ALLOW_DELETE=1` (`export NOTES_ALLOW_DELETE=1` on Linux/macOS, `$env:NOTES_ALLOW_DELETE = "1"` in Windows PowerShell) and run `client.py` again: `delete_note` now appears, marked with `destructive_hint=True` (assistants use it to ask the user for confirmation). Think about it: which tools would you expose to an assistant used by your whole company?

### 3. Use it from a real AI assistant

Connect the server to an assistant and ask in natural language: *"Create a note called 'Review JWT' with the content 'refresh tokens and iss/aud'"*, then *"What are my latest notes?"*. Use **absolute paths** and the Python of your venv.

- **Claude Desktop:** Settings → Developer → Edit Config (`claude_desktop_config.json`):

  ```json
  {
    "mcpServers": {
      "notes": {
        "command": "C:\\path\\to\\17-mcp\\venv\\Scripts\\python.exe",
        "args": ["C:\\path\\to\\17-mcp\\mcp_server.py"],
        "env": { "NOTES_API_KEY": "the-same-key-as-the-api" }
      }
    }
  }
  ```

- **Claude Code:** one command, run in the folder you work in (`-e` passes the key to the server's environment):

  ```bash
  claude mcp add notes -e NOTES_API_KEY=the-same-key-as-the-api -- C:\path\to\17-mcp\venv\Scripts\python.exe C:\path\to\17-mcp\mcp_server.py
  ```

  It saves the same `mcpServers` entry as Claude Desktop (in `~/.claude.json`, only for this folder); to share it with the project, put that JSON in a `.mcp.json` file at the root of the project. Check it with `claude mcp list`.

- **Cursor:** the same `mcpServers` JSON as Claude Desktop, in `.cursor/mcp.json` (this project) or `~/.cursor/mcp.json` (all projects).

- **VS Code (Copilot agent mode):** create `.vscode/mcp.json` in the folder you open:

  ```json
  {
    "servers": {
      "notes": {
        "type": "stdio",
        "command": "C:\\path\\to\\17-mcp\\venv\\Scripts\\python.exe",
        "args": ["C:\\path\\to\\17-mcp\\mcp_server.py"]
      }
    }
  }
  ```

The `env` block (or `-e`) is only needed if you started the Notes API with `NOTES_API_KEY` (stretch goal 1). The Notes API must keep running in its own terminal: the assistant only starts the MCP server.

### 4. Add a prompt or a new tool

- Add an `update_note(note_id, title=None, content=None)` tool that calls `PATCH /notes/<id>` (send only the fields that are not `None`).
- Add a prompt with `@mcp.prompt()` that returns a ready-made instruction, e.g. *"Summarise my last 5 notes in 3 bullet points"*.

## Understanding MCP

### Tools, resources and prompts

| Primitive | Who decides to use it | Example here |
|-----------|----------------------|--------------|
| **Tool** | The **model** (it asks the client to call it) | `create_note` |
| **Resource** | The **application/user** (attached as context) | `notes://1` |
| **Prompt** | The **user** (picks a template) | Stretch goal 4 |

### Why stdout is sacred

With the stdio transport, **stdout carries the JSON-RPC messages**. A stray `print("hello")` corrupts the stream: the client receives a line that is not JSON-RPC (`client.py` logs `Failed to parse JSONRPC message from server`; other clients may disconnect). Log to **stderr** instead (`print(..., file=sys.stderr)`), as the starter does.

### Same rules as any API client

An MCP server is just another client of your API. Everything from the course still applies: least privilege (expose only the tools you need), validation (the API still returns `422`), authentication (the key lives on the server), rate limits and logging.

## Additional Resources

- [Model Context Protocol: introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and its [v2 migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [MCP specification](https://modelcontextprotocol.io/specification)

## Notes

- The Notes API keeps everything in memory: notes created through MCP are lost when you restart `notes_api.py`.
- This exercise uses version 2 of the `mcp` package (`from mcp.server.mcpserver import MCPServer`). Many tutorials online still show version 1 (`from mcp.server.fastmcp import FastMCP`): the idea is the same, but the import is different.

"""Exercise 17: wrap the Notes REST API as an MCP server.

An AI assistant (the MCP client) starts this file and talks to it over stdio with JSON-RPC.
Each tool below is a normal Python function that calls the REST API with httpx:
the model chooses the tool and its arguments, but OUR code makes the HTTP call.

Complete the blanks (_____). Then test it (the Notes API must be running: python notes_api.py):
    python client.py
    npx @modelcontextprotocol/inspector python mcp_server.py
"""
import os
import sys

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

NOTES_API_URL = os.getenv('NOTES_API_URL', 'http://127.0.0.1:5000')
NOTES_API_KEY = os.getenv('NOTES_API_KEY', '')                # stays here: the model never sees it
ALLOW_DELETE = os.getenv('NOTES_ALLOW_DELETE') == '1'         # least privilege: off by default

mcp = MCPServer(
    'notes',
    instructions='Tools to read and write the user\'s notes in the Notes API.',
)


def call_api(method, path, **kwargs):
    """Call the Notes API and return the JSON body (None for 204).

    Errors are raised as ToolError: its message is sent to the model, which can read it and react
    (any other exception reaches the model only as a generic "Error executing tool").
    """
    # TODO: Send the API key in the header the Notes API expects (see check_api_key in notes_api.py)
    headers = {'_____': NOTES_API_KEY} if NOTES_API_KEY else {}
    try:
        response = httpx.request(method, NOTES_API_URL + path, headers=headers, timeout=10, **kwargs)
    except httpx.ConnectError:
        raise ToolError(f'The Notes API is not running at {NOTES_API_URL}. Start it with: python notes_api.py')

    if response.is_error:
        # The API answers with RFC 9457 problem+json: pass the readable "detail" back to the model
        try:
            detail = response.json().get('detail', response.text)
        except ValueError:
            detail = response.text
        raise ToolError(f'{response.status_code}: {detail}')

    return response.json() if response.content else None


# ---------------------------------------------------------------------------
# Tools: the docstring is the description the model reads, the type hints become the JSON Schema
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_notes(limit: int = 10) -> list[dict]:
    """List the most recent notes, newest first. limit: how many notes to return (1-100)."""
    # GET /notes returns {"data": [...], "page": {...}}: give the model just the list
    return call_api('GET', '/notes', params={'limit': limit})['data']


@mcp.tool(annotations=ToolAnnotations(read_only_hint=_____))  # TODO: Does this tool change anything?
def get_note(note_id: int) -> dict:
    """Get one note by its id, with its full content."""
    return call_api('_____', f'/notes/{note_id}')  # TODO: Which HTTP method reads one note?


@mcp._____()  # TODO: Register this function as an MCP tool
def create_note(title: str, content: str = '') -> dict:
    # TODO: Write the docstring. It is the description the model reads to decide when to use this tool.
    """_____"""
    return call_api('_____', '/notes', json={'title': title, 'content': content})  # TODO: Method that creates


def delete_note(note_id: int) -> str:
    """Delete a note by its id. This cannot be undone."""
    call_api('DELETE', f'/notes/{note_id}')
    return f'Note {note_id} deleted.'


# Only expose the destructive tool when it is explicitly enabled
if ALLOW_DELETE:
    mcp.tool(annotations=ToolAnnotations(destructive_hint=True))(delete_note)


# ---------------------------------------------------------------------------
# Resource: data the client can read (and attach as context) without calling a tool
# ---------------------------------------------------------------------------

@mcp.resource('notes://{note_id}', mime_type='application/json')
def note_resource(note_id: int) -> dict:
    """One note as a resource, e.g. notes://1"""
    return call_api('GET', f'/notes/{note_id}')


if __name__ == '__main__':
    # stdout carries the JSON-RPC messages: anything else you print must go to stderr
    print(f'Notes MCP server -> {NOTES_API_URL} (delete tool: {"on" if ALLOW_DELETE else "off"})', file=sys.stderr)
    mcp.run(transport='_____')  # TODO: The transport for a server that the client starts as a subprocess

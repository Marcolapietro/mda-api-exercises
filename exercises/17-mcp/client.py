"""Minimal MCP client to test your server without an AI assistant (nothing to fill in here).

It does what an assistant does behind the scenes: start the server, ask for its tools
(tools/list) and call some of them (tools/call). No LLM and no API key are involved.

    python client.py                        # tests mcp_server.py (your version)
    python client.py example/example17.py   # tests the solution

The Notes API must be running first: fastapi dev notes_api.py
"""
import asyncio
import json
import os
import sys

from mcp import Client, MCPError, StdioServerParameters

SERVER_FILE = sys.argv[1] if len(sys.argv) > 1 else 'mcp_server.py'


def show(result):
    """Print a tool result on one line: structured data if there is any, otherwise the text content."""
    text = ' '.join(' '.join(block.text.split()) for block in result.content if block.type == 'text')
    if result.is_error:
        print('  ERROR (the model reads this):', text)
    elif result.structured_content is not None:
        print(' ', json.dumps(result.structured_content, ensure_ascii=False)[:300])
    else:
        print(' ', text[:300])


async def main():
    # Same as an assistant's config: which command starts the server, and its environment
    server = StdioServerParameters(command=sys.executable, args=[SERVER_FILE], env=dict(os.environ))

    async with Client(server) as client:
        print(f'Connected to: {client.server_info.name}\n')

        print('tools/list -> what the model would see:')
        tools = (await client.list_tools()).tools
        for tool in tools:
            params = ', '.join(tool.input_schema.get('properties', {}))
            print(f'  - {tool.name}({params}): {tool.description}')
        names = {tool.name for tool in tools}

        print('\ntools/call list_notes {"limit": 3}')
        show(await client.call_tool('list_notes', {'limit': 3}))

        if 'create_note' in names:
            print('\ntools/call create_note {"title": "Sent through MCP"}')
            show(await client.call_tool('create_note', {'title': 'Sent through MCP', 'content': 'Hello from client.py'}))

        if 'get_note' in names:
            print('\ntools/call get_note {"note_id": 999}  (does not exist)')
            show(await client.call_tool('get_note', {'note_id': 999}))

        print('\nresources/read notes://1')
        try:
            contents = (await client.read_resource('notes://1')).contents
            print(' ', ' '.join(contents[0].text.split())[:300])
        except MCPError as exc:  # a resource error arrives as a JSON-RPC error, not as is_error
            print(f'  ERROR: {exc}')

        print('\ndelete_note is', 'exposed' if 'delete_note' in names else 'NOT exposed (NOTES_ALLOW_DELETE is off)')


if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import logging
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tools import ALL_TOOLS, HANDLERS

# MCP uses stdout for JSON-RPC. Redirect all logging to stderr
# so nothing corrupts the protocol stream.
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

app = Server("insightStudios")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return ALL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    return await handler(arguments)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list-tools":
        for tool in ALL_TOOLS:
            print(f"{tool.name}: {tool.description}")
        sys.exit(0)
    asyncio.run(main())

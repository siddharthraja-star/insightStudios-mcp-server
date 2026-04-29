import asyncio
import logging
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tools import ALL_TOOLS, HANDLERS

# MCP uses stdout for JSON-RPC. Redirect all logging to stderr
# so nothing corrupts the protocol stream.
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

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
    logger.info("insightStudios MCP server starting")
    async with stdio_server() as (read_stream, write_stream):
        logger.info("insightStudios MCP server started, listening on stdio")
        await app.run(read_stream, write_stream, app.create_initialization_options())
    logger.info("insightStudios MCP server stopped")


async def cli_call_tool(name: str, args_json: str = "{}"):
    import json
    handler = HANDLERS.get(name)
    if handler is None:
        print(f"Unknown tool: {name}", file=sys.stderr)
        sys.exit(1)
    arguments = json.loads(args_json)
    results = await handler(arguments)
    for r in results:
        print(r.text)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list-tools":
        for tool in ALL_TOOLS:
            print(f"{tool.name}: {tool.description}")
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "call-tool":
        if len(sys.argv) < 3:
            print("Usage: main.py call-tool <tool_name> [json_args]", file=sys.stderr)
            sys.exit(1)
        asyncio.run(cli_call_tool(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "{}"))
        sys.exit(0)
    asyncio.run(main())

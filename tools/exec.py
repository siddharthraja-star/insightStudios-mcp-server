from mcp.types import Tool, TextContent
from .client import get_docker_client

TOOL_DEF = Tool(
    name="exec_in_container",
    description="Run a command inside a running Docker container and return its output",
    inputSchema={
        "type": "object",
        "properties": {
            "container_id": {
                "type": "string",
                "description": "Container ID or name",
            },
            "command": {
                "type": "string",
                "description": "Shell command to execute inside the container",
            },
        },
        "required": ["container_id", "command"],
    },
)


async def handle(arguments: dict) -> list[TextContent]:
    container_id = arguments["container_id"]
    command = arguments["command"]

    container = get_docker_client().containers.get(container_id)
    result = container.exec_run(["sh", "-c", command], stdout=True, stderr=True)
    output = result.output.decode("utf-8", errors="replace") if result.output else ""
    return [
        TextContent(
            type="text",
            text=f"Exit code: {result.exit_code}\n{output}",
        )
    ]

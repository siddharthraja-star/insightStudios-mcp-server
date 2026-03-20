import json
from mcp.types import Tool, TextContent
from .client import get_docker_client

TOOL_DEF = Tool(
    name="list_containers",
    description="List all Docker containers (running and stopped)",
    inputSchema={
        "type": "object",
        "properties": {
            "all": {
                "type": "boolean",
                "description": "Include stopped containers. Default: false (only running)",
                "default": False,
            }
        },
    },
)


async def handle(arguments: dict) -> list[TextContent]:
    include_all = arguments.get("all", False)
    containers = get_docker_client().containers.list(all=include_all)
    if not containers:
        return [TextContent(type="text", text="No containers found.")]

    rows = []
    for c in containers:
        rows.append(
            {
                "id": c.short_id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                "status": c.status,
            }
        )
    return [TextContent(type="text", text=json.dumps(rows, indent=2))]

import asyncio
import time
from mcp.types import Tool, TextContent
from .client import get_docker_client

GET_LOGS_TOOL_DEF = Tool(
    name="get_container_logs",
    description="Get stdout/stderr logs from a Docker container",
    inputSchema={
        "type": "object",
        "properties": {
            "container_id": {
                "type": "string",
                "description": "Container ID or name",
            },
            "tail": {
                "type": "integer",
                "description": "Number of lines from the end to return. Default: 100",
                "default": 100,
            },
            "since": {
                "type": "string",
                "description": "Show logs since timestamp (e.g. '2024-01-01T00:00:00') or relative (e.g. '10m', '1h')",
            },
        },
        "required": ["container_id"],
    },
)

STREAM_LOGS_TOOL_DEF = Tool(
    name="stream_container_logs",
    description="Stream real-time stdout logs from a Docker container for a given duration",
    inputSchema={
        "type": "object",
        "properties": {
            "container_id": {
                "type": "string",
                "description": "Container ID or name",
            },
            "duration_seconds": {
                "type": "integer",
                "description": "How many seconds to stream logs. Default: 10",
                "default": 10,
            },
            "tail": {
                "type": "integer",
                "description": "Number of existing log lines to include before streaming. Default: 20",
                "default": 20,
            },
        },
        "required": ["container_id"],
    },
)

WAIT_AND_STREAM_TOOL_DEF = Tool(
    name="wait_and_stream_logs",
    description="Wait for a container matching a name pattern to start, then stream its stdout logs in real time",
    inputSchema={
        "type": "object",
        "properties": {
            "name_pattern": {
                "type": "string",
                "description": "Substring to match against container names",
            },
            "wait_timeout_seconds": {
                "type": "integer",
                "description": "How long to wait for the container to start. Default: 60",
                "default": 60,
            },
            "stream_duration_seconds": {
                "type": "integer",
                "description": "How many seconds to stream logs once container is found. Default: 30",
                "default": 30,
            },
        },
        "required": ["name_pattern"],
    },
)


def _stream_blocking(container, duration: int, tail: int, log_lines: list):
    log_stream = container.logs(
        stdout=True, stderr=True, stream=True, follow=True, tail=tail
    )
    end = time.monotonic() + duration
    for chunk in log_stream:
        if time.monotonic() > end:
            break
        line = chunk.decode("utf-8", errors="replace") if isinstance(chunk, bytes) else chunk
        log_lines.append(line)


async def handle_get_logs(arguments: dict) -> list[TextContent]:
    container_id = arguments["container_id"]
    tail = arguments.get("tail", 100)
    since = arguments.get("since")

    container = get_docker_client().containers.get(container_id)
    kwargs = {"stdout": True, "stderr": True, "tail": tail, "stream": False}
    if since:
        kwargs["since"] = since

    logs = container.logs(**kwargs)
    text = logs.decode("utf-8", errors="replace") if isinstance(logs, bytes) else logs
    return [TextContent(type="text", text=text or "(no logs)")]


async def handle_stream_logs(arguments: dict) -> list[TextContent]:
    container_id = arguments["container_id"]
    duration = arguments.get("duration_seconds", 10)
    tail = arguments.get("tail", 20)

    container = get_docker_client().containers.get(container_id)
    log_lines = []
    loop = asyncio.get_event_loop()
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, _stream_blocking, container, duration, tail, log_lines),
            timeout=duration + 2,
        )
    except asyncio.TimeoutError:
        pass

    return [TextContent(type="text", text="".join(log_lines) or "(no output)")]


async def handle_wait_and_stream(arguments: dict) -> list[TextContent]:
    name_pattern = arguments["name_pattern"]
    wait_timeout = arguments.get("wait_timeout_seconds", 60)
    stream_duration = arguments.get("stream_duration_seconds", 30)

    deadline = time.monotonic() + wait_timeout
    container = None

    while time.monotonic() < deadline:
        running = get_docker_client().containers.list()
        for c in running:
            if name_pattern.lower() in c.name.lower():
                container = c
                break
        if container:
            break
        await asyncio.sleep(1)

    if not container:
        return [
            TextContent(
                type="text",
                text=f"No running container matching '{name_pattern}' found within {wait_timeout}s.",
            )
        ]

    found_msg = f"Found container: {container.name} ({container.short_id})\n--- logs ---\n"
    log_lines = [found_msg]

    await asyncio.wait_for(
        asyncio.get_event_loop().run_in_executor(
            None, _stream_blocking, container, stream_duration, 0, log_lines
        ),
        timeout=stream_duration + 2,
    )

    return [TextContent(type="text", text="".join(log_lines) or "(no output)")]

# insightStudios MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes Docker container introspection and management as tools for AI assistants like Claude.

## Tools

| Tool | Description |
|------|-------------|
| `list_containers` | List all Docker containers (running and/or stopped) |
| `get_container_logs` | Fetch stdout/stderr logs from a container |
| `stream_container_logs` | Stream real-time logs from a container for a given duration |
| `wait_and_stream_logs` | Wait for a container matching a name pattern to start, then stream its logs |
| `exec_in_container` | Run a shell command inside a running container and return the output |

### Tool details

#### `list_containers`
```
all (bool, optional): Include stopped containers. Default: false
```

#### `get_container_logs`
```
container_id (string, required): Container ID or name
tail         (int, optional):    Lines from end to return. Default: 100
since        (string, optional): Timestamp or relative time, e.g. "10m", "1h", "2024-01-01T00:00:00"
```

#### `stream_container_logs`
```
container_id      (string, required): Container ID or name
duration_seconds  (int, optional):    Seconds to stream. Default: 10
tail              (int, optional):    Existing lines to include before streaming. Default: 20
```

#### `wait_and_stream_logs`
```
name_pattern            (string, required): Substring to match against container names
wait_timeout_seconds    (int, optional):   Max seconds to wait for the container. Default: 60
stream_duration_seconds (int, optional):   Seconds to stream once found. Default: 30
```

#### `exec_in_container`
```
container_id (string, required): Container ID or name
command      (string, required): Shell command to run inside the container
```

## Requirements

- Python 3.10+
- Docker daemon running and accessible via the Docker socket

## Installation

```bash
pip install -r requirements.txt
```

## Running

### As an MCP server (stdio transport)

```bash
python main.py
```

The server communicates over stdin/stdout using the MCP JSON-RPC protocol. All logging is directed to stderr to avoid corrupting the protocol stream.

### List available tools

```bash
python main.py list-tools
```

## Connecting to Claude Code

Add the server to your Claude Code MCP config (`.claude/settings.json` or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "insightStudios": {
      "command": "python",
      "args": ["/path/to/mcp_servers/main.py"]
    }
  }
}
```

## Generating docs

The `docs/` folder contains RCA (Root Cause Analysis) reports produced by Claude using this MCP server. No separate script is needed — the workflow is entirely prompt-driven inside Claude Code.

### How it works

1. **Connect** the MCP server to Claude Code (see above).
2. **Ask Claude** to investigate a container. Example prompts:

   ```
   Fetch the last 500 lines from container ai_videos_backend-pp and write an RCA to docs/
   ```

   ```
   Stream logs from ai_videos_backend-pp for 60 seconds, then write a structured RCA report to docs/rca_<container>_<date>.md
   ```

3. Claude calls `list_containers`, `get_container_logs` / `stream_container_logs`, and optionally `exec_in_container` to gather evidence, then writes a structured Markdown report.

### Suggested report prompt

```
Use the insightStudios MCP tools to:
1. List containers and find <container-name>
2. Fetch the last 1000 log lines (or stream for N seconds)
3. Write a structured RCA to docs/rca_<container>_<YYYY-MM-DD>.md covering:
   - Executive summary
   - Timeline of events
   - Root cause analysis
   - Recommendations
```

### Report naming convention

```
docs/rca_<container-name>_<YYYY-MM-DD>.md
docs/rca_<container-name>_<YYYY-MM-DD>_<window>.md   # e.g. _10min for a narrow window
```

## Project structure

```
mcp_servers/
├── main.py           # MCP server entry point
├── requirements.txt  # Python dependencies
└── tools/
    ├── __init__.py   # Tool registry
    ├── client.py     # Shared Docker client (lazy singleton)
    ├── containers.py # list_containers tool
    ├── logs.py       # get_container_logs, stream_container_logs, wait_and_stream_logs
    └── exec.py       # exec_in_container tool
```

import asyncio
import os
import re
from datetime import datetime, timezone
from mcp.types import Tool, TextContent
from .client import get_docker_client
from .logs import _stream_blocking, _apply_filters, _extract_filters

_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

RCA_TOOL_DEF = Tool(
    name="analyze_and_write_rca",
    description=(
        "Stream logs from a Docker container, analyze them with GPT-4o (as a senior architect), "
        "and write a structured RCA markdown report to docs/<output_file>.md. "
        "Extracts API traces, latencies, error chains, and produces actionable recommendations. "
        "Requires OPENAI_API_KEY in the environment."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "container_id": {
                "type": "string",
                "description": "Container ID or name to fetch logs from",
            },
            "output_file": {
                "type": "string",
                "description": (
                    "Output filename without path or extension, "
                    "e.g. 'rca_backend_2026-05-17'. Defaults to auto-generated name."
                ),
            },
            "since": {
                "type": "string",
                "description": "Show logs since timestamp (e.g. '2024-01-01T00:00:00') or relative (e.g. '30m', '1h')",
            },
            "tail": {
                "type": "integer",
                "description": "Number of log lines to fetch from the end of the log. Default: 1000",
                "default": 1000,
            },
            "stream_duration_seconds": {
                "type": "integer",
                "description": "Stream live logs for this many additional seconds before analysis. Default: 0",
                "default": 0,
            },
            "trace_id": {
                "type": "string",
                "description": "Filter log lines to only those containing this trace ID",
            },
            "job_id": {
                "type": "string",
                "description": "Filter log lines to only those containing this job ID",
            },
            "task": {
                "type": "string",
                "description": "Filter log lines to only those containing this task type",
            },
        },
        "required": ["container_id"],
    },
)

_RCA_SYSTEM_PROMPT = """\
You are a Principal Platform Engineer and Senior Architect with 15+ years of experience in \
distributed systems, observability, and production incident analysis. Your expertise spans:

- Distributed tracing, structured logging, and APM
- API latency profiling, connection pool management, and throughput analysis
- Database query analysis, ORM behaviour, and slow-query detection
- Cloud infrastructure (GCP, AWS, Kubernetes, Docker)
- AI/ML inference pipelines, async job queues, and GPU workloads
- Root cause analysis, failure mode reasoning, and post-mortem authoring

## Your methodology

1. **Timeline reconstruction** — extract exact timestamps, trace IDs, and event sequences in \
chronological order. Group into logical phases (session start, data load, job execution, cleanup).

2. **API trace analysis** — for every HTTP call note method, path, status code, and latency. \
Calculate P50/P99 where multiple samples exist. Flag anything >500 ms, any 4xx/5xx, and any \
chain of retries.

3. **Error chain identification** — trace how initial failures cascade into downstream effects. \
Distinguish root cause from symptoms.

4. **Connection and resource analysis** — look for pool exhaustion, file-descriptor leaks, \
thread contention, OOM signals, or GC pauses.

5. **Signal vs. noise** — distinguish actionable issues (CRITICAL/WARNING) from expected \
transient behaviour (INFO).

6. **Quantitative evidence** — back every claim with specific log lines, timestamps, trace IDs, \
and numeric metrics. No vague statements.

## Output format

Write a complete RCA markdown document with this exact structure:

```
# RCA: <container-name> — <date>

**Container:** `<container>`
**Observation window:** `<earliest timestamp>` – `<latest timestamp> UTC`
**Total log lines analyzed:** <N>
**Environment:** <inferred from logs, e.g. Pre-Production, Production>

---

## Executive Summary

<2–4 sentences. State the critical issues and user-visible impact. Use inline severity tags.>

| # | Issue | Severity | Count/Scope |
|---|---|---|---|
| 1 | ... | CRITICAL | ... |
| 2 | ... | WARNING | ... |

---

## Timeline of Events

### Phase 1 — <name> (<HH:MM:SS – HH:MM:SS UTC>)

| Time (UTC) | Event | Trace ID | Latency |
|---|---|---|---|
| HH:MM:SS | Description | `<trace>` | Xms |

### Phase 2 — ...

---

## API Latency Profile

| Endpoint | Method | Status | Latency (observed) | Count | Notes |
|---|---|---|---|---|---|
| `/path` | GET | 200 | Xms | N | |

---

## Issues Found

### Issue 1 — <Title> [CRITICAL|WARNING|INFO]

- **Affected:** <components, trace IDs, job IDs>
- **Root Cause:** <precise technical explanation>
- **Evidence:**
  ```
  <exact log snippet or metric>
  ```
- **Impact:** <downstream / user-visible effects>
- **Contributing Factors:**
  - <factor>

---

## Observations

| # | Observation | Severity | Evidence |
|---|---|---|---|
| 1 | ... | High | log excerpt |

---

## Recommendations

### Immediate (fix before next deploy)
1. **<Title>** — <specific action, include config values, code patterns, or thresholds where applicable>

### Short-term (this sprint)
1. **<Title>** — <recommendation>

### Long-term (architectural)
1. **<Title>** — <recommendation>
```

Be specific, technical, and direct. Every recommendation must cite the exact issue it resolves. \
Include trace IDs wherever present in the logs. Express latencies in milliseconds. \
Never omit the Recommendations section — it is the most important deliverable of this analysis.\
"""


async def handle_analyze_and_write_rca(arguments: dict) -> list[TextContent]:
    from openai import OpenAI

    container_id = arguments["container_id"]
    tail = arguments.get("tail", 1000)
    since = arguments.get("since")
    stream_duration = arguments.get("stream_duration_seconds", 0)
    output_file = arguments.get("output_file")

    # ── fetch historical logs ────────────────────────────────────────────────
    docker = get_docker_client()
    container = docker.containers.get(container_id)
    container_name = container.name

    log_kwargs = {"stdout": True, "stderr": True, "tail": tail, "stream": False, "timestamps": True}
    if since:
        log_kwargs["since"] = since

    raw = container.logs(**log_kwargs)
    log_text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw

    # ── optionally stream live logs ──────────────────────────────────────────
    if stream_duration > 0:
        live_lines: list[str] = []
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, _stream_blocking, container, stream_duration, 0, live_lines),
                timeout=stream_duration + 5,
            )
        except asyncio.TimeoutError:
            pass
        if live_lines:
            log_text = log_text + "\n" + "".join(live_lines)

    # ── apply keyword filters ────────────────────────────────────────────────
    filters = _extract_filters(arguments)
    if filters:
        log_text = _apply_filters(log_text, filters)

    line_count = len([l for l in log_text.splitlines() if l.strip()])
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── determine output path ────────────────────────────────────────────────
    if not output_file:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", container_name)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_file = f"rca_{safe}_{date_str}"

    os.makedirs(_DOCS_DIR, exist_ok=True)
    output_path = os.path.join(_DOCS_DIR, f"{output_file}.md")

    # ── call OpenAI ──────────────────────────────────────────────────────────
    user_message = (
        f"Analyze the following container logs and write a comprehensive RCA report.\n\n"
        f"**Container:** `{container_name}`\n"
        f"**Log lines captured:** {line_count}\n"
        f"**Analysis requested at:** {now_utc}\n\n"
        f"--- LOGS START ---\n{log_text}\n--- LOGS END ---\n\n"
        f"Write the complete RCA markdown document now."
    )

    openai_client = OpenAI()
    rca_content = ""

    stream = openai_client.chat.completions.create(
        model="gpt-4o",
        max_tokens=16000,
        stream=True,
        messages=[
            {"role": "system", "content": _RCA_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            rca_content += delta

    if not rca_content.strip():
        return [TextContent(type="text", text="OpenAI returned an empty response. Check OPENAI_API_KEY and retry.")]

    # ── write to docs/ ───────────────────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rca_content)

    preview = rca_content[:1500]
    tail_note = "\n\n...(truncated — see full file)" if len(rca_content) > 1500 else ""
    return [
        TextContent(
            type="text",
            text=(
                f"RCA written to `{output_path}`\n\n"
                f"Analyzed **{line_count}** log lines from `{container_name}`.\n\n"
                f"---\n\n"
                f"{preview}{tail_note}"
            ),
        )
    ]

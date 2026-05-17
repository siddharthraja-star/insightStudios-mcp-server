import os
from mcp.types import Tool, TextContent

_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

EXPORT_DOCS_TOOL_DEF = Tool(
    name="export_rca_docs",
    description=(
        "List and export all generated RCA markdown files from the docs/ directory. "
        "Returns filenames, sizes, and optionally the full content of each file."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "include_content": {
                "type": "boolean",
                "description": "Include the full markdown content of each file. Default: true",
                "default": True,
            },
            "filename_filter": {
                "type": "string",
                "description": "Only return files whose names contain this substring (case-insensitive). Default: all files.",
            },
        },
    },
)


async def handle_export_rca_docs(arguments: dict) -> list[TextContent]:
    include_content = arguments.get("include_content", True)
    filename_filter = (arguments.get("filename_filter") or "").lower()

    if not os.path.isdir(_DOCS_DIR):
        return [TextContent(type="text", text="docs/ directory does not exist yet — run analyze_and_write_rca first.")]

    md_files = sorted(
        f for f in os.listdir(_DOCS_DIR)
        if f.endswith(".md") and (not filename_filter or filename_filter in f.lower())
    )

    if not md_files:
        query = f" matching '{filename_filter}'" if filename_filter else ""
        return [TextContent(type="text", text=f"No markdown files found in docs/{query}.")]

    parts: list[str] = [f"**{len(md_files)} RCA document(s) in docs/**\n"]

    for filename in md_files:
        path = os.path.join(_DOCS_DIR, filename)
        size = os.path.getsize(path)
        parts.append(f"### {filename}  _(~{size // 1024} KB)_")

        if include_content:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            parts.append(content)
        else:
            # Preview: first 3 non-empty lines
            with open(path, encoding="utf-8") as f:
                preview_lines = [l.rstrip() for l in f if l.strip()][:3]
            parts.append("\n".join(preview_lines))

        parts.append("\n---\n")

    return [TextContent(type="text", text="\n".join(parts))]

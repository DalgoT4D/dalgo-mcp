#!/usr/bin/env python3
"""Generate the tool reference table for README.md.

Run: python scripts/generate_tool_table.py
     (or: uv run python scripts/generate_tool_table.py)

Updates the ## Tools section in README.md automatically between sentinel
comments.  Re-running is idempotent — the section is replaced in place.
"""
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SENTINEL_START = "<!-- TOOLS_TABLE_START -->"
SENTINEL_END = "<!-- TOOLS_TABLE_END -->"

# Maps keywords found in a tool name to a display category.
# Order matters: first match wins.
CATEGORY_MAP: list[tuple[tuple[str, ...], str]] = [
    (("current_user", "org_user", "feature_flag"), "Organization"),
    (("schema", "table", "row"), "Warehouse"),
    (("pipeline", "flow_run", "trigger_pipeline"), "Pipelines"),
    (("source_definition", "list_sources", "get_source", "delete_source"), "Sources"),
    (("connection", "sync_history", "catalog"), "Connections"),
    (("dashboard",), "Dashboards"),
    (("chart",), "Charts"),
    (("report",), "Reports"),
    (
        (
            "dbt",
            "transform",
            "sources_models",
            "git_status",
            "canvas",
            "operation",
            "terminate_chain",
            "publish_changes",
            "node",
            "data_type",
            "run_dbt",
            "sync_sources",
        ),
        "Transforms",
    ),
    (("notification", "unread"), "Notifications"),
    (("doc",), "Documentation"),
]

# Preferred display order for categories in the output table.
CATEGORY_ORDER = [
    "Organization",
    "Warehouse",
    "Pipelines",
    "Sources",
    "Connections",
    "Dashboards",
    "Charts",
    "Reports",
    "Transforms",
    "Notifications",
    "Documentation",
    "Other",
]


def get_category(tool_name: str) -> str:
    """Infer display category from the tool name."""
    # Strip the common prefix so matching is against the functional part only.
    name = tool_name.removeprefix("dalgo_")
    for keywords, category in CATEGORY_MAP:
        if any(kw in name for kw in keywords):
            return category
    return "Other"


def build_table(tools: list) -> str:
    """Return a markdown table string grouped by category."""
    # Group tools by category, preserving CATEGORY_ORDER.
    grouped: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}
    for tool in tools:
        cat = get_category(tool.name)
        grouped.setdefault(cat, []).append(tool)

    lines: list[str] = [
        "| Tool | Description | Category |",
        "|------|-------------|----------|",
    ]
    for cat in CATEGORY_ORDER:
        for tool in grouped.get(cat, []):
            # Use the full description (first sentence / first line only).
            desc = (tool.description or "").strip()
            first_line = desc.split("\n")[0].rstrip(".")
            lines.append(f"| `{tool.name}` | {first_line} | {cat} |")

    # Any categories that appeared but weren't in the order list.
    for cat, cat_tools in grouped.items():
        if cat not in CATEGORY_ORDER:
            for tool in cat_tools:
                desc = (tool.description or "").strip()
                first_line = desc.split("\n")[0].rstrip(".")
                lines.append(f"| `{tool.name}` | {first_line} | {cat} |")

    return "\n".join(lines)


def update_readme(table: str, readme_path: str, tool_count: int) -> None:
    """Insert or replace the tool table in README.md between sentinels."""
    with open(readme_path) as f:
        content = f.read()

    new_section = f"{SENTINEL_START}\n{table}\n{SENTINEL_END}"
    count_line = f"\n\n**{tool_count} tools total.**"

    if SENTINEL_START in content and SENTINEL_END in content:
        # Replace between sentinels.
        content = re.sub(
            re.escape(SENTINEL_START) + ".*?" + re.escape(SENTINEL_END),
            new_section,
            content,
            flags=re.DOTALL,
        )
        # Update the "N tools total" line if present.
        content = re.sub(
            r"\n\n\*\*\d+ tools total\.\*\*",
            count_line,
            content,
        )
    else:
        # Replace the existing static ## Tools section if present, otherwise append.
        tools_section_re = re.compile(
            r"## Tools\n\n(\|.*?\n)+\*\*\d+ tools total\.\*\*\n?",
            re.DOTALL,
        )
        replacement = f"## Tools\n\n{new_section}{count_line}\n"
        if tools_section_re.search(content):
            content = tools_section_re.sub(replacement, content)
        else:
            content += f"\n\n## Tools\n\n{new_section}{count_line}\n"

    with open(readme_path, "w") as f:
        f.write(content)


async def main() -> None:
    # Provide stub env vars so config validation passes without real credentials.
    os.environ.setdefault("DALGO_API_URL", "http://localhost")
    os.environ.setdefault("DALGO_USERNAME", "x")
    os.environ.setdefault("DALGO_PASSWORD", "x")

    from dalgo_mcp.server import app  # noqa: PLC0415 — deferred import intentional

    tools = await app.list_tools()
    tools_sorted = sorted(tools, key=lambda t: (get_category(t.name), t.name))

    table = build_table(tools_sorted)

    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    readme_path = os.path.normpath(readme_path)

    # Replace the count placeholder in the replacement if needed.
    update_readme(table, readme_path, len(tools))

    print(f"Updated {readme_path} with {len(tools)} tools.")

    # Also print a summary by category for quick verification.
    from collections import Counter

    counts = Counter(get_category(t.name) for t in tools)
    for cat in CATEGORY_ORDER:
        if counts.get(cat):
            print(f"  {cat}: {counts[cat]}")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Measure the context window token cost of all registered dalgo-mcp tools.

Run from the repo root:
    python scripts/measure_token_cost.py

Requires no live Dalgo server — only the tool metadata (names + descriptions)
is inspected, so dummy environment variables are sufficient.
"""
import os
import sys

# Ensure src/ is on the path when run directly from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Supply the minimum env vars needed to instantiate the app without a server
os.environ.setdefault("DALGO_API_URL", "http://localhost")
os.environ.setdefault("DALGO_TRANSPORT", "stdio")


def main():
    # Token counter: prefer tiktoken, fall back to rough char/4 estimate
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")

        def count_tokens(text: str) -> int:
            return len(enc.encode(text))

        method = "tiktoken (cl100k_base)"
    except ImportError:
        def count_tokens(text: str) -> int:
            return len(text) // 4

        method = "estimate (chars/4 — install tiktoken for accurate counts)"

    # Import the app — this triggers all tool registrations
    from dalgo_mcp.server import app  # noqa: E402

    # Extract tools from FastMCP's internal tool manager
    raw_tools = app._tool_manager._tools  # dict[str, Tool]
    tools = [(name, tool.description or "") for name, tool in raw_tools.items()]

    if not tools:
        print("No tools found — something went wrong with tool registration.")
        sys.exit(1)

    # Count tokens per tool (name + description, as typically sent to the model)
    tool_tokens = []
    for name, desc in tools:
        text = f"{name}: {desc}" if desc else name
        tokens = count_tokens(text)
        tool_tokens.append((name, desc, tokens))

    # Sort highest token cost first
    tool_tokens.sort(key=lambda x: -x[2])

    total = sum(t for _, _, t in tool_tokens)
    col_width = max(len(name) for name, _, _ in tool_tokens) + 2

    print(f"\nToken cost measurement ({method})")
    print("=" * (col_width + 12))
    print(f"{'Tool':<{col_width}} {'Tokens':>8}")
    print("-" * (col_width + 12))

    cumulative = 0
    for name, _desc, tokens in tool_tokens:
        cumulative += tokens
        print(f"{name:<{col_width}} {tokens:>8,}   (cumulative: {cumulative:,})")

    print("=" * (col_width + 12))
    print(f"{'TOTAL':<{col_width}} {total:>8,}")
    print()
    print(f"Tool count:                    {len(tools)}")
    print(f"Context usage (128k window):   {total / 128_000 * 100:.1f}%")
    print(f"Context usage (200k window):   {total / 200_000 * 100:.1f}%")
    print()


if __name__ == "__main__":
    main()

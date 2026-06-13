"""MCP Apps (SEP-1865) — interactive UI resources rendered inside MCP hosts.

Each app registers a ``ui://`` resource serving self-contained HTML plus one or
more tools annotated with ``_meta.ui.resourceUri`` so hosts that support the
MCP Apps extension render the tool result as an interactive view. Hosts without
the extension fall back to the tool's text/structured content unchanged.
"""

from dalgo_mcp.apps import chart_app

__all__ = ["register"]


def register(app):
    """Register all MCP App UI resources and their tools."""
    chart_app.register(app)

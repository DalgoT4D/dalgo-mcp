"""Chart MCP App — renders a Dalgo chart as an interactive view in the host.

Proof of concept for the MCP Apps extension (SEP-1865). It registers:

- a ``ui://dalgo/chart`` resource serving the self-contained chart view, and
- ``dalgo_render_chart``, a tool annotated with ``_meta.ui.resourceUri`` that
  returns the chart's type and data as ``structuredContent`` for the view.

We add a dedicated tool rather than annotating ``dalgo_get_chart_data`` so the
existing text-only tool stays unchanged for non-App clients. The progressive
enhancement alternative (annotate the existing tool, return both text and
structuredContent) is noted in docs/mcp-apps.md.
"""

from importlib import resources

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import ChartId
from dalgo_mcp.pii import mask_pii_in_rows

CHART_UI_URI = "ui://dalgo/chart"
UI_MIME_TYPE = "text/html;profile=mcp-app"

# Origins the sandboxed view may load from. The view is self-contained, so the
# default-deny policy is fine; declared here for clarity and future use.
_UI_META = {"ui": {"csp": {"connect-src": [], "img-src": []}, "prefersBorder": True}}


def _load_view() -> str:
    return resources.files(__package__).joinpath("chart_view.html").read_text(encoding="utf-8")


def _rows_from_body(body):
    """Pull the list of row dicts out of a chart-data response."""
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in ("data", "rows", "results"):
            value = body.get(key)
            if isinstance(value, list):
                return value
    return []


def register(app: FastMCP):
    @app.resource(
        CHART_UI_URI,
        name="Dalgo chart view",
        description="Interactive chart renderer for Dalgo chart data.",
        mime_type=UI_MIME_TYPE,
        meta=_UI_META,
    )
    def chart_view() -> str:
        return _load_view()

    @app.tool(
        annotations=ToolAnnotations(readOnlyHint=True),
        meta={"ui": {"resourceUri": CHART_UI_URI}},
    )
    async def dalgo_render_chart(chart_id: ChartId) -> dict:
        """Render a chart as an interactive visualization.

        Fetches the chart's configuration and executed data and returns them as
        structured content for the chart view. PII columns are masked. On hosts
        without MCP Apps support, the structured content is shown directly.

        Args:
            chart_id: The chart ID.
        """
        client = await adapt_context()

        meta_resp = await client.get(f"/api/charts/{chart_id}/")
        config = meta_resp.json() if meta_resp.status_code < 400 else {}

        data_resp = await client.get(f"/api/charts/{chart_id}/data/")
        rows = mask_pii_in_rows(_rows_from_body(data_resp.json())) if data_resp.status_code < 400 else []

        chart_type = config.get("chart_type") or config.get("type") or "bar"
        extras = config.get("extra_config") or config.get("config") or {}

        return {
            "title": config.get("title") or config.get("name") or f"Chart {chart_id}",
            "chart_type": chart_type,
            "x_axis": extras.get("xAxis") or extras.get("x_axis"),
            "y_axis": extras.get("yAxis") or extras.get("y_axis"),
            "rows": rows,
            "row_count": len(rows),
        }

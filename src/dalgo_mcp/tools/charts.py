import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import ChartId
from dalgo_mcp.pii import mask_pii_in_rows


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_charts() -> str:
        """List all charts in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/charts/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_chart(chart_id: ChartId) -> str:
        """Get details of a specific chart.

        Args:
            chart_id: The chart ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/charts/{chart_id}/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_create_chart(chart_data: dict) -> str:
        """Create a new chart.

        Args:
            chart_data: Chart configuration dict with title, SQL query, chart type, and dashboard assignment.
        """
        client = await adapt_context()
        resp = await client.post("/api/charts/", json=chart_data)
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
    async def dalgo_update_chart(chart_id: ChartId, chart_data: dict) -> str:
        """Update an existing chart.

        Args:
            chart_data: Updated chart configuration dict.
        """
        client = await adapt_context()
        resp = await client.put(f"/api/charts/{chart_id}/", json=chart_data)
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
    async def dalgo_delete_chart(chart_id: ChartId) -> str:
        """Delete a chart.

        Args:
            chart_id: The chart ID.
        """
        client = await adapt_context()
        resp = await client.delete(f"/api/charts/{chart_id}/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_chart_data(chart_id: ChartId) -> str:
        """Execute a chart's query and return the resulting data.
        PII columns (name, email, phone, address, etc.) are automatically masked.

        Args:
            chart_id: The chart ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/charts/{chart_id}/data/")
        if resp.status_code < 400:
            try:
                body = resp.json()
                if isinstance(body, list):
                    return json.dumps(mask_pii_in_rows(body), indent=2, default=str)
                if isinstance(body, dict):
                    for key in ("data", "rows", "results"):
                        if key in body and isinstance(body[key], list):
                            body[key] = mask_pii_in_rows(body[key])
                            return json.dumps(body, indent=2, default=str)
            except Exception:
                pass
        return format_response(resp)

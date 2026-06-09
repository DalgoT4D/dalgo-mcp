from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import DashboardId


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_dashboards() -> str:
        """List all dashboards in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/dashboards/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_dashboard(dashboard_id: DashboardId) -> str:
        """Get details of a specific dashboard including its charts.

        Args:
            dashboard_id: The dashboard ID (get from dalgo_list_dashboards).
        """
        client = await adapt_context()
        resp = await client.get(f"/api/dashboards/{dashboard_id}/")
        return format_response(resp)

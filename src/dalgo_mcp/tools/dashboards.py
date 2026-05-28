from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import DashboardId


def register(app: FastMCP):

    @app.tool()
    async def dalgo_list_dashboards() -> str:
        """List all dashboards in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/dashboards/")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_dashboard(dashboard_id: DashboardId) -> str:
        """Get details of a specific dashboard including its charts.

        Args:
            dashboard_id: The dashboard ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/dashboards/{dashboard_id}/")
        return format_response(resp)

    @app.tool()
    async def dalgo_create_dashboard(dashboard_data: dict) -> str:
        """Create a new dashboard.

        Args:
            dashboard_data: Dashboard configuration dict with title and optional description.
        """
        client = await adapt_context()
        resp = await client.post("/api/dashboards/", json=dashboard_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_update_dashboard(dashboard_id: DashboardId, dashboard_data: dict) -> str:
        """Update an existing dashboard.

        Args:
            dashboard_data: Updated dashboard configuration dict.
        """
        client = await adapt_context()
        resp = await client.put(f"/api/dashboards/{dashboard_id}/", json=dashboard_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_delete_dashboard(dashboard_id: DashboardId) -> str:
        """Delete a dashboard.

        Args:
            dashboard_id: The dashboard ID.
        """
        client = await adapt_context()
        resp = await client.delete(f"/api/dashboards/{dashboard_id}/")
        return format_response(resp)

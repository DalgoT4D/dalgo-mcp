from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import DalgoClient, format_response
from dalgo_mcp.params import ChartId


def register(app: FastMCP, get_client):

    @app.tool()
    async def dalgo_list_charts() -> str:
        """List all charts in the organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/charts/")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_chart(chart_id: ChartId) -> str:
        """Get details of a specific chart."""
        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/charts/{chart_id}/")
        return format_response(resp)

    @app.tool()
    async def dalgo_create_chart(chart_data: dict) -> str:
        """Create a new chart.

        Args:
            chart_data: Chart configuration dict with title, SQL query, chart type, and dashboard assignment.
        """
        client: DalgoClient = await get_client()
        resp = await client.post("/api/charts/", json=chart_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_update_chart(chart_id: ChartId, chart_data: dict) -> str:
        """Update an existing chart.

        Args:
            chart_data: Updated chart configuration dict.
        """
        client: DalgoClient = await get_client()
        resp = await client.put(f"/api/charts/{chart_id}/", json=chart_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_delete_chart(chart_id: ChartId) -> str:
        """Delete a chart."""
        client: DalgoClient = await get_client()
        resp = await client.delete(f"/api/charts/{chart_id}/")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_chart_data(chart_id: ChartId) -> str:
        """Execute a chart's query and return the resulting data."""
        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/charts/{chart_id}/data/")
        return format_response(resp)

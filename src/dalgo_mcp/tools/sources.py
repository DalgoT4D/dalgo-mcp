from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import DalgoClient, format_response
from dalgo_mcp.params import SourceId


def register(app: FastMCP, get_client):

    @app.tool()
    async def dalgo_list_sources() -> str:
        """List all configured data sources (Airbyte sources) in the organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/airbyte/sources")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_source(source_id: SourceId) -> str:
        """Get details of a specific data source."""
        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/airbyte/sources/{source_id}")
        return format_response(resp)

    @app.tool()
    async def dalgo_list_source_definitions() -> str:
        """List all available Airbyte source definitions (connector types)."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/airbyte/source_definitions")
        return format_response(resp)

    @app.tool()
    async def dalgo_delete_source(source_id: SourceId) -> str:
        """Delete a data source."""
        client: DalgoClient = await get_client()
        resp = await client.delete(f"/api/airbyte/sources/{source_id}")
        return format_response(resp)

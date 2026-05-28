from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_connections() -> str:
        """List all Airbyte connections (source-to-destination syncs) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/airbyte/v1/connections")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_connection(connection_id: str) -> str:
        """Get details of a specific Airbyte connection.

        Args:
            connection_id: The Airbyte connection ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_sync_history(connection_id: str) -> str:
        """Get sync run history for an Airbyte connection.

        Args:
            connection_id: The Airbyte connection ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}/sync/history")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_connection_catalog(connection_id: str) -> str:
        """Get the stream catalog for an Airbyte connection (selected streams and sync modes).

        Args:
            connection_id: The Airbyte connection ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}/catalog")
        return format_response(resp)

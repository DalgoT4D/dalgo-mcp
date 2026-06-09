import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import SourceId


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_sources() -> str:
        """List all configured data sources (Airbyte sources) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/airbyte/sources")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_source_details(source_id: SourceId) -> str:
        """Get detailed information for a data source, including its sync connections
        and recent sync history.

        Use dalgo_list_sources first to get source IDs.

        Args:
            source_id: The Airbyte source ID.
        """
        client = await adapt_context()
        result: dict = {}

        source_resp = await client.get(f"/api/airbyte/sources/{source_id}")
        if source_resp.status_code < 400:
            try:
                result["source"] = source_resp.json()
            except Exception:
                result["source"] = source_resp.text

        # Fetch all connections and filter to those belonging to this source
        connections_resp = await client.get("/api/airbyte/v1/connections")
        if connections_resp.status_code < 400:
            try:
                all_connections = connections_resp.json()
                if isinstance(all_connections, list):
                    source_connections = [
                        c for c in all_connections
                        if c.get("source_id") == source_id or c.get("sourceId") == source_id
                    ]
                    result["connections"] = source_connections
                    # Fetch sync history for each connection
                    histories = []
                    for conn in source_connections:
                        conn_id = conn.get("id") or conn.get("connectionId")
                        if conn_id:
                            hist_resp = await client.get(
                                f"/api/airbyte/v1/connections/{conn_id}/sync/history"
                            )
                            if hist_resp.status_code < 400:
                                try:
                                    histories.append({"connection_id": conn_id, "history": hist_resp.json()})
                                except Exception:
                                    pass
                    if histories:
                        result["sync_history"] = histories
            except Exception:
                pass

        return json.dumps(result, indent=2, default=str)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_source_definitions() -> str:
        """List all available Airbyte source definitions (connector types)."""
        client = await adapt_context()
        resp = await client.get("/api/airbyte/source_definitions")
        return format_response(resp)

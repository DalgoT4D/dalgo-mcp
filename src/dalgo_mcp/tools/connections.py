from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import ConnectionId

# Connection tools are internal — not registered as MCP tools.
# Use dalgo_get_source_details (in sources.py) to access connection and sync history data.
# These helpers are available for internal use by other tool modules.


async def _get_connection(connection_id: ConnectionId) -> str:
    client = await adapt_context()
    resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}")
    return format_response(resp)


async def _get_sync_history(connection_id: ConnectionId) -> str:
    client = await adapt_context()
    resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}/sync/history")
    return format_response(resp)


async def _get_connection_catalog(connection_id: ConnectionId) -> str:
    client = await adapt_context()
    resp = await client.get(f"/api/airbyte/v1/connections/{connection_id}/catalog")
    return format_response(resp)


def register(app: FastMCP):
    # No tools registered — connection data is surfaced via dalgo_get_source_details.
    pass

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_reports() -> str:
        """List all saved reports (point-in-time dashboard snapshots) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/reports/")
        return format_response(resp)

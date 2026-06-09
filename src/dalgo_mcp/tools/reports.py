from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_reports() -> str:
        """List all saved reports (data snapshots) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/reports/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_report(snapshot_id: str) -> str:
        """View a specific report's data.

        Args:
            snapshot_id: The report snapshot ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/reports/{snapshot_id}/view/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_create_report(report_data: dict) -> str:
        """Create a new report (data snapshot).

        Args:
            report_data: Report configuration dict with query and schedule settings.
        """
        client = await adapt_context()
        resp = await client.post("/api/reports/", json=report_data)
        return format_response(resp)


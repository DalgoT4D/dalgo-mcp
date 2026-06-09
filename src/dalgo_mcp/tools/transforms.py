from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_dbt_workspace() -> str:
        """Get the dbt workspace configuration for the organization."""
        client = await adapt_context()
        resp = await client.get("/api/dbt/dbt_workspace")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_run_dbt(run_params: dict | None = None) -> str:
        """Trigger a dbt run via Celery (async task). Optionally pass command and flags.

        WARNING: This executes dbt models in the warehouse. Confirm with the user before calling.

        Args:
            run_params: Optional dict with dbt run parameters (e.g. command, select, exclude).
        """
        client = await adapt_context()
        resp = await client.post("/api/dbt/run_dbt_via_celery/", json=run_params or {})
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_transform_graph() -> str:
        """Get the dbt project DAG (directed acyclic graph) showing model dependencies."""
        client = await adapt_context()
        resp = await client.get("/api/transform/v2/dbt_project/graph/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_sync_sources() -> str:
        """Sync dbt sources from the connected warehouse, updating the dbt project's source definitions."""
        client = await adapt_context()
        resp = await client.post("/api/transform/dbt_project/sync_sources/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_publish_changes(commit_message: str) -> str:
        """Commit and push dbt project changes to git.

        Args:
            commit_message: Git commit message describing the changes.
        """
        client = await adapt_context()
        resp = await client.post(
            "/api/dbt/publish_changes/",
            json={"commit_message": commit_message},
        )
        return format_response(resp)

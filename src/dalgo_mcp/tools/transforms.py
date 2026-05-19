from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import DalgoClient, format_response


def register(app: FastMCP, get_client):

    @app.tool()
    async def dalgo_get_dbt_workspace() -> str:
        """Get the dbt workspace configuration for the organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/dbt/dbt_workspace")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_git_status() -> str:
        """Get the git status of the dbt project repository (modified/untracked files)."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/dbt/git_status/")
        return format_response(resp)

    @app.tool()
    async def dalgo_run_dbt(run_params: dict | None = None) -> str:
        """Trigger a dbt run via Celery (async task). Optionally pass command and flags.

        Args:
            run_params: Optional dict with dbt run parameters (e.g. command, select, exclude).
        """
        client: DalgoClient = await get_client()
        resp = await client.post("/api/dbt/run_dbt_via_celery/", json=run_params or {})
        return format_response(resp)

    @app.tool()
    async def dalgo_get_transform_graph() -> str:
        """Get the dbt project DAG (directed acyclic graph) showing model dependencies."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/transform/v2/dbt_project/graph/")
        return format_response(resp)

    @app.tool()
    async def dalgo_sync_sources() -> str:
        """Sync dbt sources from the connected warehouse, updating the dbt project's source definitions."""
        client: DalgoClient = await get_client()
        resp = await client.post("/api/transform/dbt_project/sync_sources/")
        return format_response(resp)

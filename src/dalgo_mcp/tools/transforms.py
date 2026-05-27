from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import DalgoClient, format_response


def register(app: FastMCP, get_client):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_dbt_workspace() -> str:
        """Get the dbt workspace configuration for the organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/dbt/dbt_workspace")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_git_status() -> str:
        """Get the git status of the dbt project repository (modified/untracked files)."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/dbt/git_status/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_run_dbt(run_params: dict | None = None) -> str:
        """Trigger a dbt run via Celery (async task). Optionally pass command and flags.

        Args:
            run_params: Optional dict with dbt run parameters (e.g. command, select, exclude).
        """
        client: DalgoClient = await get_client()
        resp = await client.post("/api/dbt/run_dbt_via_celery/", json=run_params or {})
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_transform_graph() -> str:
        """Get the dbt project DAG (directed acyclic graph) showing model dependencies."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/transform/v2/dbt_project/graph/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_sync_sources() -> str:
        """Sync dbt sources from the connected warehouse, updating the dbt project's source definitions."""
        client: DalgoClient = await get_client()
        resp = await client.post("/api/transform/dbt_project/sync_sources/")
        return format_response(resp)

    # ── Read Tools ──────────────────────────────────────────────────────

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_sources_models(schema_name: str | None = None) -> str:
        """Get all available sources and models with their columns.

        Args:
            schema_name: Optional schema name to filter results.
        """
        client: DalgoClient = await get_client()
        params = {}
        if schema_name:
            params["schema_name"] = schema_name
        resp = await client.get(
            "/api/transform/v2/dbt_project/sources_models/",
            params=params or None,
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_node_details(node_uuid: str) -> str:
        """Get full details of a canvas node including its operation config and input nodes.

        Args:
            node_uuid: UUID of the canvas node.
        """
        client: DalgoClient = await get_client()
        resp = await client.get(
            f"/api/transform/v2/dbt_project/nodes/{node_uuid}/",
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_node_columns(node_uuid: str) -> str:
        """Get column names and data types for a specific canvas node.

        Args:
            node_uuid: UUID of the canvas node.
        """
        client: DalgoClient = await get_client()
        resp = await client.get(
            f"/api/transform/v2/dbt_project/nodes/{node_uuid}/columns/",
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_data_types() -> str:
        """Get the list of warehouse-specific data types (used for cast operations)."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/transform/dbt_project/data_type/")
        return format_response(resp)

    # ── Write Tools ─────────────────────────────────────────────────────

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_acquire_canvas_lock() -> str:
        """Acquire a lock on the transform canvas. Required before making any canvas modifications.

        Returns lock_token, expires_at, and locked_by.
        """
        client: DalgoClient = await get_client()
        resp = await client.post("/api/transform/dbt_project/canvas/lock/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
    async def dalgo_release_canvas_lock() -> str:
        """Release the lock on the transform canvas after modifications are complete."""
        client: DalgoClient = await get_client()
        resp = await client.delete("/api/transform/dbt_project/canvas/lock/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_add_source_to_canvas(dbtmodel_uuid: str) -> str:
        """Add an existing source or model to the canvas as a node.

        Args:
            dbtmodel_uuid: UUID of the dbt source/model to add.
        """
        client: DalgoClient = await get_client()
        resp = await client.post(
            f"/api/transform/v2/dbt_project/models/{dbtmodel_uuid}/nodes/",
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_create_operation(
        input_node_uuid: str,
        op_type: str,
        config: dict,
        source_columns: list[str],
        other_inputs: list[dict] | None = None,
    ) -> str:
        """Create a new operation node on the canvas (join, filter, rename, aggregate, etc.).

        Args:
            input_node_uuid: UUID of the input canvas node.
            op_type: Operation type. One of: aggregate, arithmetic, casewhen,
                castdatatypes, coalescecolumns, dropcolumns, renamecolumns,
                flattenjson, groupby, join, unionall, pivot, unpivot, where,
                rawsql, replace, concat, generic, regexextraction.
            config: Operation-specific configuration dict.
            source_columns: List of column names from the input node to use.
            other_inputs: Optional list of additional input nodes (used for join/unionall).
        """
        client: DalgoClient = await get_client()
        body = {
            "input_node_uuid": input_node_uuid,
            "op_type": op_type,
            "config": config,
            "source_columns": source_columns,
        }
        if other_inputs is not None:
            body["other_inputs"] = other_inputs
        resp = await client.post(
            "/api/transform/v2/dbt_project/operations/nodes/",
            json=body,
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
    async def dalgo_edit_operation(
        node_uuid: str,
        op_type: str,
        config: dict,
        source_columns: list[str],
        other_inputs: list[dict] | None = None,
    ) -> str:
        """Edit an existing operation node on the canvas.

        Args:
            node_uuid: UUID of the operation node to edit.
            op_type: Operation type. One of: aggregate, arithmetic, casewhen,
                castdatatypes, coalescecolumns, dropcolumns, renamecolumns,
                flattenjson, groupby, join, unionall, pivot, unpivot, where,
                rawsql, replace, concat, generic, regexextraction.
            config: Updated operation-specific configuration dict.
            source_columns: Updated list of column names from the input node.
            other_inputs: Optional list of additional input nodes (used for join/unionall).
        """
        client: DalgoClient = await get_client()
        body = {
            "op_type": op_type,
            "config": config,
            "source_columns": source_columns,
        }
        if other_inputs is not None:
            body["other_inputs"] = other_inputs
        resp = await client.put(
            f"/api/transform/v2/dbt_project/operations/nodes/{node_uuid}/",
            json=body,
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_terminate_chain(
        node_uuid: str,
        name: str,
        display_name: str,
        dest_schema: str,
    ) -> str:
        """Materialize an operation chain into a dbt model.

        Args:
            node_uuid: UUID of the last operation node in the chain.
            name: Technical name for the dbt model (snake_case).
            display_name: Human-readable display name.
            dest_schema: Destination schema in the warehouse.
        """
        client: DalgoClient = await get_client()
        resp = await client.post(
            f"/api/transform/v2/dbt_project/operations/nodes/{node_uuid}/terminate/",
            json={
                "name": name,
                "display_name": display_name,
                "dest_schema": dest_schema,
            },
        )
        return format_response(resp)

    # ── Execute Tool ────────────────────────────────────────────────────

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_publish_changes(commit_message: str) -> str:
        """Commit and push dbt project changes to git.

        Args:
            commit_message: Git commit message describing the changes.
        """
        client: DalgoClient = await get_client()
        resp = await client.post(
            "/api/dbt/publish_changes/",
            json={"commit_message": commit_message},
        )
        return format_response(resp)

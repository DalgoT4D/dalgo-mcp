from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import DalgoClient, format_response


def register(app: FastMCP, get_client):

    @app.tool()
    async def dalgo_list_pipelines() -> str:
        """List all orchestration pipelines (Prefect deployments) in the organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/prefect/v1/flows/")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_pipeline(deployment_id: str) -> str:
        """Get details of a specific pipeline by its deployment ID.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/prefect/v1/flows/{deployment_id}")
        return format_response(resp)

    @app.tool()
    async def dalgo_create_pipeline(pipeline_data: dict) -> str:
        """Create a new orchestration pipeline.

        Args:
            pipeline_data: Pipeline configuration dict with connection_id, cron schedule, and transform settings.
        """
        client: DalgoClient = await get_client()
        resp = await client.post("/api/prefect/v1/flows/", json=pipeline_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_update_pipeline(deployment_id: str, pipeline_data: dict) -> str:
        """Update an existing pipeline's configuration.

        Args:
            deployment_id: The Prefect deployment ID.
            pipeline_data: Updated pipeline configuration dict.
        """
        client: DalgoClient = await get_client()
        resp = await client.put(f"/api/prefect/v1/flows/{deployment_id}", json=pipeline_data)
        return format_response(resp)

    @app.tool()
    async def dalgo_delete_pipeline(deployment_id: str) -> str:
        """Delete a pipeline by its deployment ID.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client: DalgoClient = await get_client()
        resp = await client.delete(f"/api/prefect/v1/flows/{deployment_id}")
        return format_response(resp)

    @app.tool()
    async def dalgo_trigger_pipeline_run(deployment_id: str) -> str:
        """Trigger an immediate run of a pipeline.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client: DalgoClient = await get_client()
        resp = await client.post(f"/api/prefect/v1/flows/{deployment_id}/flow_run/")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_pipeline_run_history(deployment_id: str, limit: int = 10) -> str:
        """Get the run history for a specific pipeline.

        Args:
            deployment_id: The Prefect deployment ID.
            limit: Maximum number of runs to return (default 10).
        """
        client: DalgoClient = await get_client()
        resp = await client.get(
            f"/api/prefect/v1/flows/{deployment_id}/flow_runs/history",
            params={"limit": limit},
        )
        return format_response(resp)

    @app.tool()
    async def dalgo_get_flow_run(flow_run_id: str) -> str:
        """Get details of a specific flow run.

        Args:
            flow_run_id: The Prefect flow run ID.
        """
        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_flow_run_logs(flow_run_id: str) -> str:
        """Get logs for a specific flow run. Large logs are truncated to avoid context overflow —
        the response includes metadata showing how many lines were omitted.

        Args:
            flow_run_id: The Prefect flow run ID.
        """
        import json
        from dalgo_mcp.truncate import truncate_log_text

        client: DalgoClient = await get_client()
        resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}/logs")

        if resp.status_code < 400:
            try:
                data = resp.json()
                # logs might be a string, a list of strings, or a dict with a 'logs' key
                if isinstance(data, str):
                    result = truncate_log_text(data)
                    return json.dumps(result, indent=2)
                elif isinstance(data, list):
                    text = "\n".join(str(line) for line in data)
                    result = truncate_log_text(text)
                    return json.dumps(result, indent=2)
                elif isinstance(data, dict) and "logs" in data:
                    result = truncate_log_text(str(data["logs"]))
                    data["logs"] = result["content"]
                    data["_meta"] = result["_meta"]
                    return json.dumps(data, indent=2, default=str)
            except Exception:
                pass
        return format_response(resp)

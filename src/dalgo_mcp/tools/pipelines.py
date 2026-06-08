from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import DeploymentId, FlowRunId, Limit


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_pipelines() -> str:
        """List all orchestration pipelines (Prefect deployments) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/prefect/v1/flows/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_pipeline(deployment_id: DeploymentId) -> str:
        """Get details of a specific pipeline by its deployment ID.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/prefect/v1/flows/{deployment_id}")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_create_pipeline(pipeline_data: dict) -> str:
        """Create a new orchestration pipeline.

        Args:
            pipeline_data: Pipeline configuration dict with connection_id, cron schedule, and transform settings.
        """
        client = await adapt_context()
        resp = await client.post("/api/prefect/v1/flows/", json=pipeline_data)
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True))
    async def dalgo_update_pipeline(deployment_id: DeploymentId, pipeline_data: dict) -> str:
        """Update an existing pipeline's configuration.

        Args:
            pipeline_data: Updated pipeline configuration dict.
        """
        client = await adapt_context()
        resp = await client.put(f"/api/prefect/v1/flows/{deployment_id}", json=pipeline_data)
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False))
    async def dalgo_delete_pipeline(deployment_id: DeploymentId) -> str:
        """Delete a pipeline by its deployment ID.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client = await adapt_context()
        resp = await client.delete(f"/api/prefect/v1/flows/{deployment_id}")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_trigger_pipeline_run(deployment_id: DeploymentId) -> str:
        """Trigger an immediate run of a pipeline.

        Args:
            deployment_id: The Prefect deployment ID.
        """
        client = await adapt_context()
        resp = await client.post(f"/api/prefect/v1/flows/{deployment_id}/flow_run/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_pipeline_run_history(deployment_id: DeploymentId, limit: Limit = 10) -> str:
        """Get the run history for a specific pipeline.

        Args:
            deployment_id: The Prefect deployment ID.
            limit: Maximum number of runs to return (default 10).
        """
        client = await adapt_context()
        resp = await client.get(
            f"/api/prefect/v1/flows/{deployment_id}/flow_runs/history",
            params={"limit": limit},
        )
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_flow_run(flow_run_id: FlowRunId) -> str:
        """Get details of a specific flow run.

        Args:
            flow_run_id: The Prefect flow run ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_flow_run_logs(flow_run_id: FlowRunId) -> str:
        """Get logs for a specific flow run.

        Args:
            flow_run_id: The Prefect flow run ID.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}/logs")
        return format_response(resp)

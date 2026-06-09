import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import DeploymentId, FlowRunId


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_pipelines() -> str:
        """List all orchestration pipelines (Prefect deployments) in the organization."""
        client = await adapt_context()
        resp = await client.get("/api/prefect/v1/flows/")
        return format_response(resp)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_run_status(
        deployment_id: DeploymentId | None = None,
        flow_run_id: FlowRunId | None = None,
    ) -> str:
        """Get pipeline run status and logs. Dispatches based on what is provided:
        - deployment_id only → pipeline details + recent run history (last 5 runs)
        - flow_run_id only → flow run details + logs (use this to debug a specific failing run)
        - both → pipeline details, recent history, and the specific flow run with logs

        This is the primary tool for debugging pipeline failures. Get deployment_id from
        dalgo_list_pipelines. Get flow_run_id from a run history response.

        Args:
            deployment_id: Prefect deployment ID.
            flow_run_id: Prefect flow run ID.
        """
        from dalgo_mcp.truncate import truncate_log_text

        if deployment_id is None and flow_run_id is None:
            return json.dumps({"error": "Provide at least one of deployment_id or flow_run_id"})

        client = await adapt_context()
        result: dict = {}

        if deployment_id:
            pipeline_resp = await client.get(f"/api/prefect/v1/flows/{deployment_id}")
            if pipeline_resp.status_code < 400:
                try:
                    result["pipeline"] = pipeline_resp.json()
                except Exception:
                    result["pipeline"] = pipeline_resp.text

            history_resp = await client.get(
                f"/api/prefect/v1/flows/{deployment_id}/flow_runs/history",
                params={"limit": 5},
            )
            if history_resp.status_code < 400:
                try:
                    result["recent_runs"] = history_resp.json()
                except Exception:
                    result["recent_runs"] = history_resp.text

        if flow_run_id:
            run_resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}")
            if run_resp.status_code < 400:
                try:
                    result["flow_run"] = run_resp.json()
                except Exception:
                    result["flow_run"] = run_resp.text

            logs_resp = await client.get(f"/api/prefect/flow_runs/{flow_run_id}/logs")
            if logs_resp.status_code < 400:
                try:
                    data = logs_resp.json()
                    if isinstance(data, str):
                        result["logs"] = truncate_log_text(data)
                    elif isinstance(data, list):
                        text = "\n".join(str(line) for line in data)
                        result["logs"] = truncate_log_text(text)
                    elif isinstance(data, dict) and "logs" in data:
                        truncated = truncate_log_text(str(data["logs"]))
                        data["logs"] = truncated["content"]
                        data["_meta"] = truncated["_meta"]
                        result["logs"] = data
                    else:
                        result["logs"] = data
                except Exception:
                    result["logs"] = logs_resp.text

        return json.dumps(result, indent=2, default=str)

    @app.tool(annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False))
    async def dalgo_trigger_pipeline_run(deployment_id: DeploymentId) -> str:
        """Trigger an immediate run of a pipeline.

        WARNING: This starts an actual pipeline execution. Confirm with the user before calling.

        Args:
            deployment_id: The Prefect deployment ID (get from dalgo_list_pipelines).
        """
        client = await adapt_context()
        resp = await client.post(f"/api/prefect/v1/flows/{deployment_id}/flow_run/")
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

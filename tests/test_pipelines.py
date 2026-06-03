"""Unit tests for pipelines tool module."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from tests.conftest import make_response


def register_tools():
    """Register pipeline tools and capture the inner functions for direct testing."""
    from dalgo_mcp.tools import pipelines

    app = FastMCP("test")
    captured = {}
    original_tool = app.tool

    def capturing_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            captured[fn.__name__] = fn
            return decorator(fn)

        return wrapper

    app.tool = capturing_tool
    pipelines.register(app)
    return captured


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def tools(mock_client):
    with patch("dalgo_mcp.tools.pipelines.adapt_context", new=AsyncMock(return_value=mock_client)):
        yield register_tools()


class TestDalgoListPipelines:
    @pytest.mark.asyncio
    async def test_returns_formatted_list(self, tools, mock_client):
        pipeline_list = [
            {"id": "abc", "name": "Ingest NGO data"},
            {"id": "def", "name": "Transform pipeline"},
        ]
        mock_client.get.return_value = make_response(200, pipeline_list)

        result = await tools["dalgo_list_pipelines"]()
        data = json.loads(result)

        assert data == pipeline_list
        mock_client.get.assert_called_once_with("/api/prefect/v1/flows/")

    @pytest.mark.asyncio
    async def test_error_response_includes_status_code(self, tools, mock_client):
        mock_client.get.return_value = make_response(500, {"detail": "Internal error"})

        result = await tools["dalgo_list_pipelines"]()
        data = json.loads(result)

        assert data["error"] is True
        assert data["status_code"] == 500


class TestDalgoTriggerPipelineRun:
    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, tools, mock_client):
        mock_client.post.return_value = make_response(200, {"flow_run_id": "run-123"})

        result = await tools["dalgo_trigger_pipeline_run"](deployment_id="deploy-abc")
        data = json.loads(result)

        assert data["flow_run_id"] == "run-123"
        mock_client.post.assert_called_once_with("/api/prefect/v1/flows/deploy-abc/flow_run/")

    @pytest.mark.asyncio
    async def test_error_on_bad_deployment_id(self, tools, mock_client):
        mock_client.post.return_value = make_response(404, {"detail": "Not found"})

        result = await tools["dalgo_trigger_pipeline_run"](deployment_id="bad-id")
        data = json.loads(result)

        assert data["error"] is True
        assert data["status_code"] == 404


class TestDalgoGetFlowRunLogs:
    @pytest.mark.asyncio
    async def test_returns_logs(self, tools, mock_client):
        logs = [
            {"level": "INFO", "message": "Task started"},
            {"level": "INFO", "message": "Task completed"},
        ]
        mock_client.get.return_value = make_response(200, logs)

        result = await tools["dalgo_get_flow_run_logs"](flow_run_id="run-999")
        data = json.loads(result)

        assert data == logs
        mock_client.get.assert_called_once_with("/api/prefect/flow_runs/run-999/logs")

    @pytest.mark.asyncio
    async def test_error_response(self, tools, mock_client):
        mock_client.get.return_value = make_response(404, {"detail": "Run not found"})

        result = await tools["dalgo_get_flow_run_logs"](flow_run_id="missing-run")
        data = json.loads(result)

        assert data["error"] is True
        assert data["status_code"] == 404

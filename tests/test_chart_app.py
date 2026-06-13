"""Unit tests for the chart MCP App (SEP-1865)."""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from tests.conftest import make_response


def register_app():
    """Register the chart app and capture its tool fns and resource registration."""
    from dalgo_mcp.apps import chart_app

    app = FastMCP("test")
    captured = {"tools": {}, "resources": {}}

    original_tool = app.tool
    original_resource = app.resource

    def capturing_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(fn):
            captured["tools"][fn.__name__] = {"fn": fn, "meta": kwargs.get("meta")}
            return decorator(fn)

        return wrapper

    def capturing_resource(uri, *args, **kwargs):
        decorator = original_resource(uri, *args, **kwargs)

        def wrapper(fn):
            captured["resources"][uri] = {"fn": fn, "mime_type": kwargs.get("mime_type"), "meta": kwargs.get("meta")}
            return decorator(fn)

        return wrapper

    app.tool = capturing_tool
    app.resource = capturing_resource
    chart_app.register(app)
    return captured


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def app(mock_client):
    with patch("dalgo_mcp.apps.chart_app.adapt_context", new=AsyncMock(return_value=mock_client)):
        yield register_app()


class TestChartUIResource:
    def test_resource_registered_with_mcp_app_mime(self, app):
        res = app["resources"]["ui://dalgo/chart"]
        assert res["mime_type"] == "text/html;profile=mcp-app"
        assert res["meta"]["ui"]["prefersBorder"] is True

    def test_resource_serves_self_contained_view(self, app):
        html = app["resources"]["ui://dalgo/chart"]["fn"]()
        assert "<!DOCTYPE html>" in html
        # Implements the MCP Apps handshake and result handling.
        assert "ui/initialize" in html
        assert "ui/notifications/tool-result" in html


class TestRenderChartTool:
    def test_tool_links_to_ui_resource(self, app):
        meta = app["tools"]["dalgo_render_chart"]["meta"]
        assert meta["ui"]["resourceUri"] == "ui://dalgo/chart"

    @pytest.mark.asyncio
    async def test_returns_structured_content_with_masked_rows(self, app, mock_client):
        config = {"title": "Donors by region", "chart_type": "bar"}
        rows = [{"region": "North", "donor_name": "Alice", "count": 12}]
        mock_client.get.side_effect = [
            make_response(200, config),
            make_response(200, {"data": rows}),
        ]

        result = await app["tools"]["dalgo_render_chart"]["fn"](chart_id=7)

        assert result["title"] == "Donors by region"
        assert result["chart_type"] == "bar"
        assert result["row_count"] == 1
        # PII column masked, non-PII preserved.
        assert result["rows"][0]["donor_name"] == "***MASKED***"
        assert result["rows"][0]["count"] == 12

    @pytest.mark.asyncio
    async def test_handles_data_fetch_failure(self, app, mock_client):
        mock_client.get.side_effect = [
            make_response(200, {"title": "X", "chart_type": "line"}),
            make_response(500, {"detail": "boom"}),
        ]

        result = await app["tools"]["dalgo_render_chart"]["fn"](chart_id=1)

        assert result["rows"] == []
        assert result["row_count"] == 0
        assert result["chart_type"] == "line"

"""Unit tests for warehouse tool module."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from tests.conftest import make_response


def register_tools():
    """Register warehouse tools and capture the inner functions for direct testing."""
    from dalgo_mcp.tools import warehouse

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
    warehouse.register(app)
    return captured


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def tools(mock_client):
    with patch("dalgo_mcp.tools.warehouse.adapt_context", new=AsyncMock(return_value=mock_client)):
        yield register_tools()


class TestDalgoGetTableData:
    @pytest.mark.asyncio
    async def test_masks_pii_column(self, tools, mock_client):
        rows = [{"name": "Alice", "revenue": 100}]
        mock_client.get.return_value = make_response(200, rows)

        result = await tools["dalgo_get_table_data"](schema="public", table="donors")
        data = json.loads(result)

        assert data[0]["name"] == "***MASKED***"
        assert data[0]["revenue"] == 100

    @pytest.mark.asyncio
    async def test_no_pii_columns_returned_unchanged(self, tools, mock_client):
        rows = [{"revenue": 500, "count": 3}]
        mock_client.get.return_value = make_response(200, rows)

        result = await tools["dalgo_get_table_data"](schema="public", table="summary")
        data = json.loads(result)

        assert data == rows

    @pytest.mark.asyncio
    async def test_non_list_response_falls_back_to_format_response(self, tools, mock_client):
        payload = {"error": "table not found"}
        mock_client.get.return_value = make_response(404, payload)

        result = await tools["dalgo_get_table_data"](schema="public", table="missing")
        data = json.loads(result)

        assert data["error"] is True
        assert data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_non_list_200_falls_back_to_format_response(self, tools, mock_client):
        # A 200 response that is not a list (e.g. a dict) should use format_response
        payload = {"rows": [], "total": 0}
        mock_client.get.return_value = make_response(200, payload)

        result = await tools["dalgo_get_table_data"](schema="public", table="summary")
        data = json.loads(result)

        assert data == payload

    @pytest.mark.asyncio
    async def test_passes_limit_and_offset_params(self, tools, mock_client):
        mock_client.get.return_value = make_response(200, [])

        await tools["dalgo_get_table_data"](schema="s", table="t", limit=5, offset=20)
        mock_client.get.assert_called_once_with(
            "/api/warehouse/table_data/s/t",
            params={"limit": 5, "offset": 20},
        )


class TestDalgoListSchemas:
    @pytest.mark.asyncio
    async def test_returns_formatted_json(self, tools, mock_client):
        schemas = ["public", "analytics", "raw"]
        mock_client.get.return_value = make_response(200, schemas)

        result = await tools["dalgo_list_schemas"]()
        data = json.loads(result)

        assert data == schemas
        mock_client.get.assert_called_once_with("/api/warehouse/schemas")


class TestDalgoGetTableRowCount:
    @pytest.mark.asyncio
    async def test_returns_count(self, tools, mock_client):
        mock_client.get.return_value = make_response(200, {"count": 42})

        result = await tools["dalgo_get_table_row_count"](schema="public", table="donors")
        data = json.loads(result)

        assert data["count"] == 42
        mock_client.get.assert_called_once_with("/api/warehouse/table_count/public/donors")

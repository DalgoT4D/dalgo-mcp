from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


@pytest.fixture
def get_client(mock_client):
    async def _get_client():
        return mock_client

    return _get_client


def make_response(status_code: int, json_data) -> httpx.Response:
    """Helper to create mock httpx.Response objects."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    return response

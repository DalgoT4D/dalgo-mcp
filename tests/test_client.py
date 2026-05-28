"""Unit tests for format_response in dalgo_mcp.client."""

import json
from unittest.mock import MagicMock

import httpx

from dalgo_mcp.client import format_response
from tests.conftest import make_response


class TestFormatResponse:
    def test_200_with_json_returns_formatted_json(self):
        data = {"pipelines": [{"id": "1", "name": "test"}]}
        resp = make_response(200, data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed == data

    def test_204_returns_success_message(self):
        resp = make_response(204, None)
        # 204 responses have no body — format_response handles this before calling .json()
        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed["status"] == "success"
        assert "message" in parsed

    def test_400_returns_error_with_status_code(self):
        error_data = {"detail": "Bad request"}
        resp = make_response(400, error_data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed["error"] is True
        assert parsed["status_code"] == 400
        assert parsed["detail"] == error_data

    def test_500_returns_error_with_status_code(self):
        error_data = {"detail": "Internal server error"}
        resp = make_response(500, error_data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed["error"] is True
        assert parsed["status_code"] == 500

    def test_200_with_list_json(self):
        data = [{"id": "1"}, {"id": "2"}]
        resp = make_response(200, data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed == data

    def test_201_with_json(self):
        data = {"id": "new-123", "created": True}
        resp = make_response(201, data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed == data

    def test_403_returns_error(self):
        error_data = {"detail": "Forbidden"}
        resp = make_response(403, error_data)

        result = format_response(resp)
        parsed = json.loads(result)

        assert parsed["error"] is True
        assert parsed["status_code"] == 403

    def test_json_parse_failure_falls_back_to_text(self):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.json.side_effect = ValueError("Not JSON")
        resp.text = "plain text response"

        result = format_response(resp)
        # Should still return something (the text as-is in JSON)
        assert "plain text response" in result

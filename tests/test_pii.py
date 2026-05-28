"""Unit tests for PII detection and masking logic in dalgo_mcp.pii."""

from dalgo_mcp.pii import is_pii_column, mask_pii_in_rows


class TestIsPiiColumn:
    def test_name_is_pii(self):
        assert is_pii_column("name") is True

    def test_email_is_pii(self):
        assert is_pii_column("email") is True

    def test_aadhaar_no_is_pii(self):
        assert is_pii_column("aadhaar_no") is True

    def test_phone_is_pii(self):
        assert is_pii_column("phone") is True

    def test_revenue_is_not_pii(self):
        assert is_pii_column("revenue") is False

    def test_amount_is_not_pii(self):
        assert is_pii_column("amount") is False

    def test_id_is_not_pii(self):
        assert is_pii_column("id") is False

    def test_created_at_is_not_pii(self):
        assert is_pii_column("created_at") is False

    def test_address_is_pii(self):
        assert is_pii_column("address") is True

    def test_mobile_is_pii(self):
        assert is_pii_column("mobile") is True

    def test_dob_is_pii(self):
        assert is_pii_column("dob") is True

    def test_first_name_is_pii(self):
        assert is_pii_column("first_name") is True

    def test_last_name_is_pii(self):
        assert is_pii_column("last_name") is True

    def test_pan_number_is_pii(self):
        assert is_pii_column("pan_number") is True

    def test_case_insensitive(self):
        assert is_pii_column("EMAIL") is True
        assert is_pii_column("Name") is True
        assert is_pii_column("PHONE") is True


class TestMaskPiiInRows:
    def test_masks_pii_column(self):
        rows = [{"name": "Alice", "revenue": 100}]
        result = mask_pii_in_rows(rows)
        assert result == [{"name": "***MASKED***", "revenue": 100}]

    def test_empty_list_returns_empty(self):
        result = mask_pii_in_rows([])
        assert result == []

    def test_no_pii_columns_returns_unchanged(self):
        rows = [{"revenue": 100, "count": 5}]
        result = mask_pii_in_rows(rows)
        assert result == [{"revenue": 100, "count": 5}]

    def test_masks_multiple_pii_columns(self):
        rows = [{"name": "Bob", "email": "bob@example.com", "amount": 200}]
        result = mask_pii_in_rows(rows)
        assert result[0]["name"] == "***MASKED***"
        assert result[0]["email"] == "***MASKED***"
        assert result[0]["amount"] == 200

    def test_masks_across_all_rows(self):
        rows = [
            {"name": "Alice", "score": 90},
            {"name": "Bob", "score": 85},
        ]
        result = mask_pii_in_rows(rows)
        assert result[0]["name"] == "***MASKED***"
        assert result[1]["name"] == "***MASKED***"
        assert result[0]["score"] == 90
        assert result[1]["score"] == 85

    def test_none_value_stays_none(self):
        rows = [{"name": None, "revenue": 50}]
        result = mask_pii_in_rows(rows)
        assert result[0]["name"] is None

    def test_non_list_input_returned_as_is(self):
        result = mask_pii_in_rows({"name": "Alice"})
        assert result == {"name": "Alice"}

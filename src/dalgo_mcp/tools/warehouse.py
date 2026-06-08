import json

from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import Limit, Offset, SchemaName, TableName
from dalgo_mcp.pii import mask_pii_in_rows


def register(app: FastMCP):

    @app.tool()
    async def dalgo_list_schemas() -> str:
        """List all schemas in the connected data warehouse."""
        client = await adapt_context()
        resp = await client.get("/api/warehouse/schemas")
        return format_response(resp)

    @app.tool()
    async def dalgo_list_tables(schema_name: str) -> str:
        """List all tables in a specific warehouse schema.

        Args:
            schema_name: Name of the schema to list tables from.
        """
        client = await adapt_context()
        resp = await client.get(f"/api/warehouse/tables/{schema_name}")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_table_columns(schema: SchemaName, table: TableName) -> str:
        """Get column names and types for a specific warehouse table."""
        client = await adapt_context()
        resp = await client.get(f"/api/warehouse/table_columns/{schema}/{table}")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_table_data(schema: SchemaName, table: TableName, limit: Limit = 10, offset: Offset = 0) -> str:
        """Fetch rows from a warehouse table. Defaults to 10 rows to avoid context overflow.
        PII columns (name, email, phone, address, etc.) are automatically masked.
        """
        client = await adapt_context()
        resp = await client.get(
            f"/api/warehouse/table_data/{schema}/{table}",
            params={"limit": limit, "offset": offset},
        )
        if resp.status_code < 400:
            try:
                rows = resp.json()
                if isinstance(rows, list):
                    return json.dumps(mask_pii_in_rows(rows), indent=2, default=str)
            except Exception:
                pass
        return format_response(resp)

    @app.tool()
    async def dalgo_get_table_row_count(schema: SchemaName, table: TableName) -> str:
        """Get the total row count of a warehouse table."""
        client = await adapt_context()
        resp = await client.get(f"/api/warehouse/table_count/{schema}/{table}")
        return format_response(resp)

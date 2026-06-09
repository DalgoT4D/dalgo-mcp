import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context
from dalgo_mcp.params import Limit, Offset, SchemaName, TableName
from dalgo_mcp.pii import mask_pii_in_rows


def register(app: FastMCP):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_explore_warehouse(schema: str | None = None, table: str | None = None) -> str:
        """Explore the connected data warehouse. Dispatches based on what is provided:
        - No args → lists all schemas
        - schema only → lists tables in that schema
        - schema + table → returns column definitions and row count for that table

        Use this for all warehouse exploration. Do not call dalgo_list_schemas or
        dalgo_list_tables separately — this tool handles the full exploration sequence.

        Args:
            schema: Schema name (optional). If omitted, lists all schemas.
            table: Table name (optional). Requires schema. If omitted, lists tables in schema.
        """
        client = await adapt_context()
        if schema is None:
            resp = await client.get("/api/warehouse/schemas")
            return format_response(resp)
        elif table is None:
            resp = await client.get(f"/api/warehouse/tables/{schema}")
            return format_response(resp)
        else:
            cols_resp = await client.get(f"/api/warehouse/table_columns/{schema}/{table}")
            count_resp = await client.get(f"/api/warehouse/table_count/{schema}/{table}")
            result: dict = {}
            if cols_resp.status_code < 400:
                try:
                    result["columns"] = cols_resp.json()
                except Exception:
                    result["columns"] = cols_resp.text
            if count_resp.status_code < 400:
                try:
                    result["row_count"] = count_resp.json()
                except Exception:
                    result["row_count"] = count_resp.text
            return json.dumps(result, indent=2, default=str)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_table_data(
        schema: SchemaName,
        table: TableName,
        limit: Limit = 10,
        offset: Offset = 0,
    ) -> str:
        """Fetch rows from a warehouse table. Defaults to 10 rows to avoid context overflow.
        PII columns (name, email, phone, address, etc.) are automatically masked.

        Use dalgo_explore_warehouse first to discover available schemas and tables.

        Args:
            schema: Schema name.
            table: Table name.
            limit: Number of rows to return (default 10, max 500).
            offset: Number of rows to skip for pagination.
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

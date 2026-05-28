from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool()
    async def dalgo_list_notifications() -> str:
        """List recent notifications for the current user."""
        client = await adapt_context()
        resp = await client.get("/api/notifications/v1")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_unread_count() -> str:
        """Get the count of unread notifications."""
        client = await adapt_context()
        resp = await client.get("/api/notifications/unread_count")
        return format_response(resp)

    @app.tool()
    async def dalgo_mark_notifications_read(notification_ids: list[str] | None = None) -> str:
        """Mark notifications as read.

        Args:
            notification_ids: Optional list of notification IDs to mark as read. If not provided, marks all as read.
        """
        client = await adapt_context()
        payload = {}
        if notification_ids:
            payload["notification_ids"] = notification_ids
        resp = await client.put("/api/notifications/v1", json=payload)
        return format_response(resp)

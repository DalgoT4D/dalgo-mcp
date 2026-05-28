from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import format_response
from dalgo_mcp.context import adapt_context


def register(app: FastMCP):

    @app.tool()
    async def dalgo_get_current_user() -> str:
        """Get the currently authenticated Dalgo user's profile information."""
        client = await adapt_context()
        resp = await client.get("/api/currentuserv2")
        return format_response(resp)

    @app.tool()
    async def dalgo_list_org_users() -> str:
        """List all users in the current Dalgo organization."""
        client = await adapt_context()
        resp = await client.get("/api/organizations/users")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_feature_flags() -> str:
        """Get feature flags enabled for the current Dalgo organization."""
        client = await adapt_context()
        resp = await client.get("/api/organizations/flags")
        return format_response(resp)

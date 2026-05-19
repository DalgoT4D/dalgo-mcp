from mcp.server.fastmcp import FastMCP

from dalgo_mcp.client import DalgoClient, format_response


def register(app: FastMCP, get_client):

    @app.tool()
    async def dalgo_get_current_user() -> str:
        """Get the currently authenticated Dalgo user's profile information."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/currentuserv2")
        return format_response(resp)

    @app.tool()
    async def dalgo_list_org_users() -> str:
        """List all users in the current Dalgo organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/organizations/users")
        return format_response(resp)

    @app.tool()
    async def dalgo_get_feature_flags() -> str:
        """Get feature flags enabled for the current Dalgo organization."""
        client: DalgoClient = await get_client()
        resp = await client.get("/api/organizations/flags")
        return format_response(resp)

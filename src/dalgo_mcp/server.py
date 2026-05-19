import logging

from mcp.server.fastmcp import FastMCP

from dalgo_mcp.config import config
from dalgo_mcp.client import DalgoClient, get_client_for_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_app() -> FastMCP:
    """Create the FastMCP app with transport-appropriate settings."""
    if config.transport == "streamable-http":
        from mcp.server.auth.provider import TokenVerifier
        from mcp.server.auth.settings import AuthSettings
        from dalgo_mcp.auth import DalgoTokenVerifier

        return FastMCP(
            "Dalgo",
            instructions="MCP server for managing Dalgo ELT pipelines, warehouse data, dashboards, and more",
            token_verifier=DalgoTokenVerifier(),
            auth=AuthSettings(
                issuer_url=config.api_url,
                resource_server_url=f"http://{config.host}:{config.port}",
            ),
            host=config.host,
            port=config.port,
        )
    else:
        return FastMCP(
            "Dalgo",
            instructions="MCP server for managing Dalgo ELT pipelines, warehouse data, dashboards, and more",
        )


app = _create_app()

_client: DalgoClient | None = None


async def get_client() -> DalgoClient:
    """Get the appropriate DalgoClient for the current context.

    In stdio mode: returns a global singleton (username/password auth).
    In HTTP mode: returns a per-token client based on the request's Bearer token.
    """
    global _client

    if config.transport == "streamable-http":
        from mcp.server.auth.middleware.auth_context import get_access_token

        access_token = get_access_token()
        if access_token is None:
            raise RuntimeError("No access token in request context (HTTP mode requires authentication)")
        return await get_client_for_token(access_token.token)
    else:
        if _client is None:
            _client = DalgoClient()
        return _client


# Register all tool modules
from dalgo_mcp.tools import organization
from dalgo_mcp.tools import warehouse
from dalgo_mcp.tools import pipelines
from dalgo_mcp.tools import sources
from dalgo_mcp.tools import connections
from dalgo_mcp.tools import dashboards
from dalgo_mcp.tools import charts
from dalgo_mcp.tools import reports
from dalgo_mcp.tools import transforms
from dalgo_mcp.tools import notifications

organization.register(app, get_client)
warehouse.register(app, get_client)
pipelines.register(app, get_client)
sources.register(app, get_client)
connections.register(app, get_client)
dashboards.register(app, get_client)
charts.register(app, get_client)
reports.register(app, get_client)
transforms.register(app, get_client)
notifications.register(app, get_client)


def main():
    config.validate()
    app.run(transport=config.transport)


if __name__ == "__main__":
    main()

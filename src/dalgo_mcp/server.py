import logging

from mcp.server.fastmcp import FastMCP

from dalgo_mcp.config import config
from dalgo_mcp.client import DalgoClient, get_client_for_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _create_app() -> FastMCP:
    """Create the FastMCP app with transport-appropriate settings."""
    if config.transport == "streamable-http":
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
        from dalgo_mcp.oauth import DalgoOAuthProvider
        from dalgo_mcp.login import create_login_handlers

        # When behind a reverse proxy/tunnel, use DALGO_PUBLIC_URL as the OAuth
        # issuer and resource URL. Otherwise fall back to localhost (the MCP SDK
        # allows HTTP only for localhost/127.0.0.1 per RFC 8414).
        if config.public_url:
            server_url = config.public_url
        else:
            issuer_host = "localhost" if config.host == "0.0.0.0" else config.host
            server_url = f"http://{issuer_host}:{config.port}"
        oauth_provider = DalgoOAuthProvider(config.api_url)

        mcp = FastMCP(
            "Dalgo",
            instructions=(
                "Dalgo is an open-source ELT platform for NGOs and social-impact organizations. "
                "Use this server when the user asks about their data warehouse, data pipelines, "
                "dashboards, charts, reports, or data sources.\n\n"
                "Capabilities:\n"
                "- Warehouse: browse schemas, tables, columns, and fetch row data\n"
                "- Pipelines: list, create, trigger, and monitor Prefect orchestration pipelines\n"
                "- Sources & Connections: manage Airbyte data sources and sync connections\n"
                "- Dashboards & Charts: create, update, and query visualization dashboards and charts\n"
                "- Reports: create point-in-time dashboard snapshots with date filtering\n"
                "- Transforms: manage dbt workspace, run dbt, view the DAG, sync sources\n"
                "- Notifications: view and manage user notifications\n"
                "- Organization: view current user, org members, and feature flags\n"
                "- Documentation: search and browse Dalgo product documentation"
            ),
            auth_server_provider=oauth_provider,
            auth=AuthSettings(
                issuer_url=server_url,
                resource_server_url=server_url,
                client_registration_options=ClientRegistrationOptions(
                    enabled=True,
                ),
            ),
            streamable_http_path="/",
            host=config.host,
            port=config.port,
        )

        # Register login page routes (outside OAuth/MCP auth — public endpoints)
        handle_login_get, handle_login_post = create_login_handlers(oauth_provider)

        @mcp.custom_route("/login", methods=["GET"])
        async def login_get(request):
            return await handle_login_get(request)

        @mcp.custom_route("/login", methods=["POST"])
        async def login_post(request):
            return await handle_login_post(request)

        return mcp
    else:
        return FastMCP(
            "Dalgo",
            instructions=(
                "Dalgo is an open-source ELT platform for NGOs and social-impact organizations. "
                "Use this server when the user asks about their data warehouse, data pipelines, "
                "dashboards, charts, reports, or data sources.\n\n"
                "Capabilities:\n"
                "- Warehouse: browse schemas, tables, columns, and fetch row data\n"
                "- Pipelines: list, create, trigger, and monitor Prefect orchestration pipelines\n"
                "- Sources & Connections: manage Airbyte data sources and sync connections\n"
                "- Dashboards & Charts: create, update, and query visualization dashboards and charts\n"
                "- Reports: create point-in-time dashboard snapshots with date filtering\n"
                "- Transforms: manage dbt workspace, run dbt, view the DAG, sync sources\n"
                "- Notifications: view and manage user notifications\n"
                "- Organization: view current user, org members, and feature flags\n"
                "- Documentation: search and browse Dalgo product documentation"
            ),
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
from dalgo_mcp.tools import docs

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
docs.register(app, get_client)


def main():
    config.validate()
    app.run(transport=config.transport)


if __name__ == "__main__":
    main()

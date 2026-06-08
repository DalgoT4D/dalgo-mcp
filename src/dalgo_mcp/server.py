import json
import logging
import time

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from dalgo_mcp.config import config

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logger = logging.getLogger(__name__)

# Module-level start time for uptime tracking
_start_time = time.time()


class DebugRequestMiddleware(BaseHTTPMiddleware):
    """Logs method, path, headers, and body for every incoming request."""

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        logger.debug(
            ">>> %s %s\nHeaders: %s\nBody: %s",
            request.method,
            request.url,
            dict(request.headers),
            body.decode("utf-8", errors="replace")[:2000] if body else "(empty)",
        )
        response = await call_next(request)
        logger.debug(
            "<<< %s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


class ToolCallLoggingMiddleware(BaseHTTPMiddleware):
    """Log MCP tool calls with timing and success/failure status."""

    async def dispatch(self, request: Request, call_next):
        tool_name = None

        if request.method == "POST":
            try:
                body_bytes = await request.body()
                data = json.loads(body_bytes)
                if data.get("method") == "tools/call":
                    tool_name = data.get("params", {}).get("name")
            except Exception:
                pass

        t0 = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - t0) * 1000

        if tool_name:
            success = response.status_code < 400
            logger.info(
                "tool_call tool=%s duration_ms=%.1f success=%s status_code=%d",
                tool_name,
                duration_ms,
                success,
                response.status_code,
            )

        return response


def _create_app() -> FastMCP:
    """Create the FastMCP app with transport-appropriate settings."""
    if config.transport == "streamable-http":
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions

        from dalgo_mcp.login import create_login_handlers
        from dalgo_mcp.oauth import DalgoOAuthProvider

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
            debug=True,
            log_level="DEBUG",
        )

        # Register login page routes (outside OAuth/MCP auth — public endpoints)
        handle_login_get, handle_login_post = create_login_handlers(oauth_provider)

        @mcp.custom_route("/login", methods=["GET"])
        async def login_get(request):
            return await handle_login_get(request)

        @mcp.custom_route("/login", methods=["POST"])
        async def login_post(request):
            return await handle_login_post(request)

        @mcp.custom_route("/health", methods=["GET"])
        async def health(request):
            from starlette.responses import JSONResponse

            from dalgo_mcp.client import _token_clients

            return JSONResponse(
                {
                    "status": "ok",
                    "uptime_seconds": round(time.time() - _start_time, 1),
                    "active_token_clients": len(_token_clients),
                    "tool_count": len(mcp._tool_manager._tools),
                }
            )

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

# Register all tool modules
from dalgo_mcp.tools import (  # noqa: E402
    charts,
    connections,
    dashboards,
    docs,
    notifications,
    organization,
    pipelines,
    reports,
    sources,
    transforms,
    warehouse,
)

organization.register(app)
warehouse.register(app)
pipelines.register(app)
sources.register(app)
connections.register(app)
dashboards.register(app)
charts.register(app)
reports.register(app)
transforms.register(app)
notifications.register(app)
docs.register(app)


def main():
    config.validate()

    if config.debug and config.transport == "streamable-http":
        import anyio
        import uvicorn

        async def _run_debug_http():
            starlette_app = app.streamable_http_app()
            starlette_app.add_middleware(ToolCallLoggingMiddleware)
            starlette_app.add_middleware(DebugRequestMiddleware)
            server = uvicorn.Server(
                uvicorn.Config(
                    starlette_app,
                    host=app.settings.host,
                    port=app.settings.port,
                    log_level="trace",
                )
            )
            await server.serve()

        logger.info("Starting in DEBUG mode — all requests will be logged")
        anyio.run(_run_debug_http)
    elif config.transport == "streamable-http":
        import anyio
        import uvicorn

        async def _run_http():
            starlette_app = app.streamable_http_app()
            starlette_app.add_middleware(ToolCallLoggingMiddleware)
            server = uvicorn.Server(
                uvicorn.Config(
                    starlette_app,
                    host=app.settings.host,
                    port=app.settings.port,
                    log_level=app.settings.log_level.lower(),
                )
            )
            await server.serve()

        anyio.run(_run_http)
    else:
        app.run(transport=config.transport)


if __name__ == "__main__":
    main()

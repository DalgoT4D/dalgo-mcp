"""Client context resolution for dalgo-mcp tools.

adapt_context() returns the correct DalgoClient for the current request,
handling both stdio mode (global singleton) and HTTP mode (per-token client).
"""

import logging

from dalgo_mcp.client import DalgoClient, get_client_for_token
from dalgo_mcp.config import config

logger = logging.getLogger(__name__)

_client: DalgoClient | None = None


async def adapt_context() -> DalgoClient:
    """Get the appropriate DalgoClient for the current request context.

    In stdio mode: returns a global singleton (username/password auth).
    In HTTP mode: returns a per-token client based on the request's Bearer token.

    Call this at the start of every tool function instead of the injected get_client.
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

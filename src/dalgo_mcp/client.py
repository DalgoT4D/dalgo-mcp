import json
import logging
import time

import jwt

import httpx

from dalgo_mcp.config import config

logger = logging.getLogger(__name__)

# Cache of DalgoClient instances keyed by JWT token (for HTTP mode)
_token_clients: dict[str, "DalgoClient"] = {}
_token_expiries: dict[str, float] = {}  # token -> unix timestamp of expiry


class DalgoClient:
    """Async HTTP client for the Dalgo API with JWT auth and auto-refresh."""

    def __init__(self):
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._org_slug: str = config.org_slug
        self._http = httpx.AsyncClient(base_url=config.api_url, timeout=60.0)

    @classmethod
    async def from_token(cls, api_url: str, token: str) -> "DalgoClient":
        """Create a client pre-authenticated with a JWT token.

        Auto-detects the user's org by calling /api/currentuserv2.
        """
        instance = object.__new__(cls)
        instance._token = token
        instance._refresh_token = None
        instance._org_slug = ""
        instance._http = httpx.AsyncClient(base_url=api_url, timeout=60.0)

        # Auto-detect org_slug from the user's profile
        resp = await instance._http.get(
            "/api/currentuserv2",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        # The API may return a list of org-user objects or a single dict
        if isinstance(data, list):
            if data:
                first = data[0]
                instance._org_slug = first.get("org", {}).get("slug", "") if isinstance(first, dict) else ""
        elif isinstance(data, dict):
            orgs = data.get("orguser", data.get("org", []))
            if isinstance(orgs, list) and orgs:
                instance._org_slug = orgs[0].get("org", {}).get("slug", "")
            elif isinstance(orgs, dict):
                instance._org_slug = orgs.get("slug", "")

        if not instance._org_slug:
            raise ValueError("Could not auto-detect org_slug from /api/currentuserv2")

        logger.info("Created token-based client for org: %s", instance._org_slug)
        return instance

    async def _login(self):
        """Authenticate with username/password and store tokens."""
        resp = await self._http.post(
            "/api/login/",
            json={"username": config.username, "password": config.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["token"]
        self._refresh_token = data.get("refresh_token")
        logger.info("Logged in to Dalgo API")

    async def _refresh(self) -> bool:
        """Attempt to refresh the JWT token. Returns True on success."""
        if not self._refresh_token:
            return False
        try:
            resp = await self._http.post(
                "/api/token/refresh",
                json={"refresh": self._refresh_token},
            )
            if resp.status_code == 200:
                data = resp.json()
                self._token = data["token"]
                logger.info("Refreshed Dalgo API token")
                return True
        except Exception:
            logger.warning("Token refresh failed")
        return False

    def _auth_headers(self) -> dict[str, str]:
        headers = {"x-dalgo-org": self._org_slug}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def ensure_auth(self):
        """Ensure we have a valid token, logging in if necessary."""
        if not self._token:
            await self._login()

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an authenticated request with auto-refresh on 401."""
        await self.ensure_auth()

        resp = await self._http.request(method, path, headers=self._auth_headers(), **kwargs)

        if resp.status_code == 401:
            refreshed = await self._refresh()
            if not refreshed:
                await self._login()
            resp = await self._http.request(method, path, headers=self._auth_headers(), **kwargs)

        return resp

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    async def close(self):
        await self._http.aclose()


async def get_client_for_token(token: str) -> DalgoClient:
    """Get or create a cached DalgoClient for the given JWT token."""
    now = time.time()

    # Evict all expired entries on every call to prevent unbounded growth
    expired = [t for t, exp in _token_expiries.items() if exp < now]
    for t in expired:
        _token_clients.pop(t, None)
        _token_expiries.pop(t, None)

    # Return cached client if still valid
    if token in _token_clients and _token_expiries.get(token, 0) > now:
        return _token_clients[token]

    # Create new client
    client = await DalgoClient.from_token(config.api_url, token)

    # Extract expiry from JWT (no signature verification needed)
    try:
        payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        exp = float(payload.get("exp", now + 3600))
    except Exception:
        exp = now + 3600  # default 1h if decode fails

    _token_clients[token] = client
    _token_expiries[token] = exp
    return client


def format_response(resp: httpx.Response) -> str:
    """Format an API response as a string suitable for MCP tool output."""
    if resp.status_code == 204:
        return json.dumps({"status": "success", "message": "Deleted successfully"}, indent=2)

    try:
        data = resp.json()
    except Exception:
        data = resp.text

    if resp.status_code >= 400:
        return json.dumps(
            {"error": True, "status_code": resp.status_code, "detail": data},
            indent=2,
            default=str,
        )

    return json.dumps(data, indent=2, default=str)

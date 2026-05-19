"""OAuth 2.0 Authorization Server Provider for Dalgo MCP.

Wraps Dalgo's username/password + JWT authentication in an OAuth-compatible
flow so that MCP clients (like Claude) can authenticate via browser-based login.
"""

import logging
import secrets
import time
from dataclasses import dataclass

import httpx
import jwt
from pydantic import AnyUrl

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

logger = logging.getLogger(__name__)

AUTH_CODE_EXPIRY_SECONDS = 600  # 10 minutes


@dataclass
class PendingAuth:
    """Stores authorization parameters while the user completes login."""

    client: OAuthClientInformationFull
    params: AuthorizationParams


@dataclass
class StoredAuthCode:
    """An authorization code with its associated Dalgo tokens."""

    auth_code: AuthorizationCode
    dalgo_access_token: str
    dalgo_refresh_token: str | None


class DalgoOAuthProvider(OAuthAuthorizationServerProvider):
    """OAuth provider that delegates authentication to the Dalgo API.

    On /authorize, redirects to a local /login page. After the user enters
    Dalgo credentials, calls Dalgo /api/login/ to verify them, then issues
    an OAuth authorization code. The Dalgo JWT is passed through as the
    OAuth access token so that existing get_client_for_token() logic works.
    """

    def __init__(self, api_url: str):
        self.api_url = api_url

        # In-memory stores (single-process; fine for local MCP server)
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._auth_codes: dict[str, StoredAuthCode] = {}
        self._access_tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        self._dalgo_refresh_tokens: dict[str, str] = {}  # oauth_refresh -> dalgo_refresh
        self._pending_auth: dict[str, PendingAuth] = {}

    # ── Client registration ──────────────────────────────────────────

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(
        self, client_info: OAuthClientInformationFull
    ) -> None:
        self._clients[client_info.client_id] = client_info
        logger.info("Registered OAuth client: %s", client_info.client_id)

    # ── Authorization ────────────────────────────────────────────────

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: AuthorizationParams,
    ) -> str:
        """Store auth params and redirect to the login page."""
        auth_id = secrets.token_urlsafe(16)
        self._pending_auth[auth_id] = PendingAuth(client=client, params=params)
        return f"/login?auth_id={auth_id}"

    def get_pending_auth(self, auth_id: str) -> PendingAuth | None:
        return self._pending_auth.get(auth_id)

    def create_auth_code(
        self,
        auth_id: str,
        dalgo_access_token: str,
        dalgo_refresh_token: str | None,
    ) -> tuple[str, str, str | None]:
        """Create an authorization code after successful Dalgo login.

        Returns (code, redirect_uri, state).
        """
        pending = self._pending_auth.pop(auth_id)
        code = secrets.token_urlsafe(20)  # 160 bits of entropy

        auth_code = AuthorizationCode(
            code=code,
            scopes=pending.params.scopes or [],
            expires_at=time.time() + AUTH_CODE_EXPIRY_SECONDS,
            client_id=pending.client.client_id,
            code_challenge=pending.params.code_challenge,
            redirect_uri=pending.params.redirect_uri,
            redirect_uri_provided_explicitly=pending.params.redirect_uri_provided_explicitly,
            resource=pending.params.resource,
        )

        self._auth_codes[code] = StoredAuthCode(
            auth_code=auth_code,
            dalgo_access_token=dalgo_access_token,
            dalgo_refresh_token=dalgo_refresh_token,
        )

        redirect_uri = construct_redirect_uri(
            str(pending.params.redirect_uri),
            code=code,
            state=pending.params.state,
        )
        return code, redirect_uri, pending.params.state

    # ── Authorization code exchange ──────────────────────────────────

    async def load_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: str,
    ) -> AuthorizationCode | None:
        stored = self._auth_codes.get(authorization_code)
        if stored is None:
            return None
        if stored.auth_code.client_id != client.client_id:
            return None
        if time.time() > stored.auth_code.expires_at:
            self._auth_codes.pop(authorization_code, None)
            return None
        return stored.auth_code

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        stored = self._auth_codes.pop(authorization_code.code, None)
        if stored is None:
            from mcp.server.auth.provider import TokenError

            raise TokenError("invalid_grant", "Authorization code not found or already used")

        dalgo_jwt = stored.dalgo_access_token
        dalgo_refresh = stored.dalgo_refresh_token

        # Decode the Dalgo JWT to get expiry (without verifying signature)
        try:
            payload = jwt.decode(dalgo_jwt, options={"verify_signature": False})
            exp = payload.get("exp")
            user_id = str(payload.get("user_id", payload.get("sub", "unknown")))
        except jwt.DecodeError:
            exp = None
            user_id = "unknown"

        # Store the access token so load_access_token can find it
        access_token = AccessToken(
            token=dalgo_jwt,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
            expires_at=int(exp) if exp else None,
        )
        self._access_tokens[dalgo_jwt] = access_token

        # Build response
        expires_in = int(exp - time.time()) if exp else None

        oauth_refresh_token = None
        if dalgo_refresh:
            oauth_refresh_token = secrets.token_urlsafe(20)
            self._refresh_tokens[oauth_refresh_token] = RefreshToken(
                token=oauth_refresh_token,
                client_id=client.client_id,
                scopes=authorization_code.scopes,
            )
            self._dalgo_refresh_tokens[oauth_refresh_token] = dalgo_refresh

        return OAuthToken(
            access_token=dalgo_jwt,
            token_type="Bearer",
            expires_in=expires_in if expires_in and expires_in > 0 else None,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
            refresh_token=oauth_refresh_token,
        )

    # ── Refresh token exchange ───────────────────────────────────────

    async def load_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: str,
    ) -> RefreshToken | None:
        stored = self._refresh_tokens.get(refresh_token)
        if stored is None:
            return None
        if stored.client_id != client.client_id:
            return None
        return stored

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        dalgo_refresh = self._dalgo_refresh_tokens.get(refresh_token.token)
        if dalgo_refresh is None:
            from mcp.server.auth.provider import TokenError

            raise TokenError("invalid_grant", "Refresh token not found")

        # Call Dalgo's refresh endpoint
        async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0, follow_redirects=True) as http:
            resp = await http.post(
                "/api/token/refresh/",
                json={"refresh": dalgo_refresh},
            )

        if resp.status_code != 200:
            from mcp.server.auth.provider import TokenError

            raise TokenError("invalid_grant", "Dalgo token refresh failed")

        data = resp.json()
        new_dalgo_jwt = data.get("access", data.get("token"))
        if not new_dalgo_jwt:
            from mcp.server.auth.provider import TokenError

            raise TokenError("invalid_grant", "Dalgo refresh response missing access token")

        # Decode new JWT for expiry
        try:
            payload = jwt.decode(new_dalgo_jwt, options={"verify_signature": False})
            exp = payload.get("exp")
        except jwt.DecodeError:
            exp = None

        # Store the new access token
        new_access_token = AccessToken(
            token=new_dalgo_jwt,
            client_id=client.client_id,
            scopes=scopes or refresh_token.scopes,
            expires_at=int(exp) if exp else None,
        )
        self._access_tokens[new_dalgo_jwt] = new_access_token

        # Rotate refresh token
        self._refresh_tokens.pop(refresh_token.token, None)
        self._dalgo_refresh_tokens.pop(refresh_token.token, None)

        new_oauth_refresh = secrets.token_urlsafe(20)
        new_dalgo_refresh = data.get("refresh", dalgo_refresh)
        self._refresh_tokens[new_oauth_refresh] = RefreshToken(
            token=new_oauth_refresh,
            client_id=client.client_id,
            scopes=scopes or refresh_token.scopes,
        )
        self._dalgo_refresh_tokens[new_oauth_refresh] = new_dalgo_refresh

        expires_in = int(exp - time.time()) if exp else None

        return OAuthToken(
            access_token=new_dalgo_jwt,
            token_type="Bearer",
            expires_in=expires_in if expires_in and expires_in > 0 else None,
            scope=" ".join(scopes) if scopes else None,
            refresh_token=new_oauth_refresh,
        )

    # ── Access token verification ────────────────────────────────────

    async def load_access_token(self, token: str) -> AccessToken | None:
        # Check in-memory store first
        stored = self._access_tokens.get(token)
        if stored is not None:
            if stored.expires_at and time.time() > stored.expires_at:
                self._access_tokens.pop(token, None)
                return None
            return stored

        # Fall back to decoding the JWT (handles tokens issued before server restart,
        # though that shouldn't happen with in-memory storage)
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": True},
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Rejected expired JWT")
            return None
        except jwt.DecodeError:
            logger.warning("Rejected malformed JWT")
            return None

        user_id = str(payload.get("user_id", payload.get("sub", "unknown")))
        exp = payload.get("exp")

        access_token = AccessToken(
            token=token,
            client_id=user_id,
            scopes=[],
            expires_at=int(exp) if exp else None,
        )
        self._access_tokens[token] = access_token
        return access_token

    # ── Token revocation ─────────────────────────────────────────────

    async def revoke_token(
        self, token: AccessToken | RefreshToken
    ) -> None:
        if isinstance(token, AccessToken):
            self._access_tokens.pop(token.token, None)
        elif isinstance(token, RefreshToken):
            self._refresh_tokens.pop(token.token, None)
            self._dalgo_refresh_tokens.pop(token.token, None)

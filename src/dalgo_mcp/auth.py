import logging
import time

import jwt

from mcp.server.auth.provider import AccessToken, TokenVerifier

logger = logging.getLogger(__name__)


class DalgoTokenVerifier(TokenVerifier):
    """Verify Dalgo JWT tokens without signature verification.

    The Dalgo backend validates signatures; we just check structure and expiry
    so that the MCP auth middleware can extract user identity.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                },
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Rejected expired JWT")
            return None
        except jwt.DecodeError:
            logger.warning("Rejected malformed JWT")
            return None

        user_id = str(payload.get("user_id", payload.get("sub", "unknown")))
        exp = payload.get("exp")

        return AccessToken(
            token=token,
            client_id=user_id,
            scopes=[],
            expires_at=int(exp) if exp else None,
        )

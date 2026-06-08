"""Typed error hierarchy for dalgo-mcp.

UserInputError      — bad input from the model/user (4xx)
DalgoAPIClientError — 4xx response from Dalgo API
DalgoAPIServerError — 5xx response from Dalgo API
"""


class DalgoError(Exception):
    """Base class for all dalgo-mcp errors."""
    pass


class UserInputError(DalgoError):
    """The model or user provided invalid input.

    Raise this when a required parameter is missing, has wrong type,
    or references a resource that doesn't exist.

    The error message should be actionable — tell the model what to fix.
    """
    pass


class DalgoAPIError(DalgoError):
    """Base class for HTTP errors from the Dalgo API."""

    def __init__(self, status_code: int, detail, endpoint: str = ""):
        self.status_code = status_code
        self.detail = detail
        self.endpoint = endpoint
        super().__init__(f"Dalgo API error {status_code} on {endpoint}: {detail}")


class DalgoAPIClientError(DalgoAPIError):
    """4xx response from the Dalgo API — likely a client/input problem."""
    pass


class DalgoAPIServerError(DalgoAPIError):
    """5xx response from the Dalgo API — server-side failure."""
    pass

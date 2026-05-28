"""Login page handlers for the Dalgo MCP OAuth flow.

Serves a simple HTML form where users enter their Dalgo credentials.
On successful login via the Dalgo API, redirects back to the OAuth client
with an authorization code.
"""

import logging

import httpx
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)

LOGIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dalgo - Sign In</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 2rem;
            width: 100%;
            max-width: 400px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #333;
        }
        p.subtitle {
            color: #666;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }
        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: #555;
            margin-bottom: 0.3rem;
        }
        input[type="email"], input[type="password"] {
            width: 100%;
            padding: 0.6rem 0.8rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        input:focus {
            outline: none;
            border-color: #4a90d9;
            box-shadow: 0 0 0 2px rgba(74,144,217,0.2);
        }
        button {
            width: 100%;
            padding: 0.7rem;
            background: #4a90d9;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #3a7bc8; }
        .error {
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
            border-radius: 4px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Dalgo</h1>
        <p class="subtitle">Sign in with your Dalgo account to continue</p>
        {error}
        <form method="POST" action="/login">
            <input type="hidden" name="auth_id" value="{auth_id}">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" required autofocus>
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>"""


def _render_login(auth_id: str, error: str = "") -> HTMLResponse:
    error_html = f'<div class="error">{error}</div>' if error else ""
    html = LOGIN_PAGE_HTML.replace("{auth_id}", auth_id).replace("{error}", error_html)
    return HTMLResponse(html)


def create_login_handlers(oauth_provider):
    """Create GET and POST handlers for /login that use the given OAuth provider.

    Returns (handle_login_get, handle_login_post) async callables.
    """

    async def handle_login_get(request: Request) -> Response:
        auth_id = request.query_params.get("auth_id", "")
        pending = oauth_provider.get_pending_auth(auth_id)
        if not pending:
            return HTMLResponse("<h1>Invalid or expired login link</h1>", status_code=400)
        return _render_login(auth_id)

    async def handle_login_post(request: Request) -> Response:
        form = await request.form()
        auth_id = str(form.get("auth_id", ""))
        email = str(form.get("email", ""))
        password = str(form.get("password", ""))

        pending = oauth_provider.get_pending_auth(auth_id)
        if not pending:
            return HTMLResponse("<h1>Invalid or expired login link</h1>", status_code=400)

        # Authenticate against the Dalgo API
        try:
            async with httpx.AsyncClient(base_url=oauth_provider.api_url, timeout=30.0) as http:
                resp = await http.post(
                    "/api/login/",
                    json={"username": email, "password": password},
                )
        except httpx.HTTPError:
            logger.exception("Failed to connect to Dalgo API")
            return _render_login(auth_id, error="Unable to reach Dalgo. Please try again.")

        if resp.status_code != 200:
            return _render_login(auth_id, error="Invalid email or password.")

        data = resp.json()
        dalgo_token = data.get("token")
        dalgo_refresh = data.get("refresh_token")

        if not dalgo_token:
            return _render_login(auth_id, error="Unexpected response from Dalgo.")

        # Create authorization code and redirect back to the OAuth client
        _code, redirect_uri, _state = oauth_provider.create_auth_code(
            auth_id=auth_id,
            dalgo_access_token=dalgo_token,
            dalgo_refresh_token=dalgo_refresh,
        )

        return RedirectResponse(url=redirect_uri, status_code=302)

    return handle_login_get, handle_login_post

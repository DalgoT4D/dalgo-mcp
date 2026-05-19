# Dalgo MCP Server

MCP server for the [Dalgo](https://dalgo.in) ELT orchestration platform. Gives AI assistants access to your data warehouse, pipelines, dashboards, charts, reports, and more — via natural language.

Supports two transports:
- **stdio** — for Claude Desktop and Claude Code (local setup)
- **streamable-http** — for the Anthropic Messages API MCP connector (remote, no local setup needed)

## Tools

| Module | Tools | Description |
|--------|-------|-------------|
| Organization | 3 | Current user, org users, feature flags |
| Warehouse | 5 | Schemas, tables, columns, row data, row counts |
| Pipelines | 9 | List, create, update, delete, trigger, run history, logs |
| Sources | 4 | Airbyte sources and source definitions |
| Connections | 4 | Airbyte connections, sync history, catalogs |
| Dashboards | 5 | Dashboard CRUD |
| Charts | 6 | Chart CRUD and data execution |
| Reports | 4 | Report (snapshot) CRUD |
| Transforms | 5 | dbt workspace, git status, run, DAG, sync sources |
| Notifications | 3 | List, unread count, mark read |
| Documentation | 3 | Search and browse Dalgo product documentation |

**51 tools total.**

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/DalgoT4D/dalgo-mcp.git
cd dalgo-mcp
cp .env.example .env
# Edit .env with your Dalgo credentials
uv sync
```

## Quick Install (Claude Code Plugin)

```bash
claude plugin install dalgo
```

You'll be prompted for your Dalgo API URL, username, password, and org slug. That's it — the plugin handles MCP server setup automatically.

## Manual Setup

### stdio mode (Claude Desktop / Claude Code)

Set your credentials in `.env`:

```
DALGO_API_URL=https://your-dalgo-instance.com
DALGO_USERNAME=your-email@example.com
DALGO_PASSWORD=your-password
DALGO_ORG_SLUG=your-org-slug
```

Run:

```bash
uv run dalgo-mcp
```

#### Claude Desktop config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dalgo": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/dalgo-mcp", "dalgo-mcp"],
      "env": {
        "DALGO_API_URL": "https://your-dalgo-instance.com",
        "DALGO_USERNAME": "your-email@example.com",
        "DALGO_PASSWORD": "your-password",
        "DALGO_ORG_SLUG": "your-org-slug"
      }
    }
  }
}
```

#### Claude Code

```bash
claude mcp add --transport stdio dalgo -- uv run --directory /path/to/dalgo-mcp dalgo-mcp
```

### streamable-http mode (Anthropic API)

This mode lets any user connect via a URL and their Dalgo JWT token — no local setup required.

```bash
DALGO_TRANSPORT=streamable-http \
DALGO_API_URL=https://your-dalgo-instance.com \
DALGO_HOST=0.0.0.0 \
DALGO_PORT=8080 \
uv run dalgo-mcp
```

Then use it via the Anthropic Messages API:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    mcp_servers=[
        {
            "type": "url",
            "url": "http://your-server:8080/mcp/",
            "name": "dalgo",
            "authorization_token": "<dalgo-jwt-token>",
        }
    ],
    messages=[{"role": "user", "content": "List my pipelines"}],
)
```

The `authorization_token` is a Dalgo JWT. Each user passes their own token and the server auto-detects their org.

## Auth

| Mode | Auth method |
|------|------------|
| stdio | Username/password from `.env`, single user |
| streamable-http | Bearer JWT per request, multi-user, org auto-detected via `/api/currentuserv2` |

In HTTP mode, the server verifies JWT structure and expiry (the Dalgo backend validates signatures). Per-token clients are cached so org detection only happens once per token.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DALGO_API_URL` | Yes | `http://localhost:8002` | Dalgo API base URL |
| `DALGO_USERNAME` | stdio only | | Dalgo login email |
| `DALGO_PASSWORD` | stdio only | | Dalgo login password |
| `DALGO_ORG_SLUG` | stdio only | | Dalgo organization slug |
| `DALGO_TRANSPORT` | No | `stdio` | `stdio` or `streamable-http` |
| `DALGO_HOST` | No | `0.0.0.0` | HTTP server bind address |
| `DALGO_PORT` | No | `8080` | HTTP server port |

## Project Structure

```
.claude-plugin/
└── plugin.json      # Claude Code plugin manifest
.mcp.json            # MCP server config for plugin mode
src/dalgo_mcp/
├── config.py        # Environment config and validation
├── auth.py          # JWT token verifier for HTTP mode
├── client.py        # Async Dalgo API client with auto-auth
├── server.py        # FastMCP app, dual transport, client resolution
└── tools/
    ├── organization.py
    ├── warehouse.py
    ├── pipelines.py
    ├── sources.py
    ├── connections.py
    ├── dashboards.py
    ├── charts.py
    ├── reports.py
    ├── transforms.py
    ├── notifications.py
    └── docs.py
```

## License

MIT

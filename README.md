# Dalgo MCP Server

[![CI](https://github.com/DalgoT4D/dalgo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/DalgoT4D/dalgo-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2.svg)](https://modelcontextprotocol.io)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for [Dalgo](https://dalgo.in), the open-source data platform for the social sector. It lets AI assistants like Claude work with your data warehouse, ingestion pipelines, dbt transformations, dashboards, charts, and reports through natural language.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Claude Desktop](#claude-desktop)
  - [Claude Code](#claude-code)
  - [Anthropic Messages API (remote)](#anthropic-messages-api-remote)
  - [Docker](#docker)
- [Authentication](#authentication)
- [Tool Reference](#tool-reference)
- [Development](#development)
- [Project Structure](#project-structure)
- [Releases](#releases)
- [Contributing](#contributing)
- [License](#license)

## Features

- **62 tools** covering the full Dalgo platform: warehouse exploration, pipeline orchestration, Airbyte sources and connections, dbt transformations, dashboards, charts, reports, notifications, and documentation search.
- **Dual transport** — run locally over `stdio` for Claude Desktop and Claude Code, or serve remotely over `streamable-http` for the Anthropic Messages API MCP connector.
- **Multi-user HTTP mode** — each request authenticates with the caller's own Dalgo JWT; the server detects their organization automatically.
- **One-command install** as a Claude Code plugin.
- **Docker-ready** for self-hosted deployments.

## Quick Start

The fastest way to get started is the Claude Code plugin:

```bash
claude plugin install dalgo
```

You'll be prompted for your Dalgo API URL, username, password, and organization slug. The plugin configures the MCP server automatically — no further setup needed.

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/DalgoT4D/dalgo-mcp.git
cd dalgo-mcp
cp .env.example .env
# Edit .env with your Dalgo credentials
uv sync
```

Verify the server starts:

```bash
uv run dalgo-mcp
```

## Configuration

All configuration is via environment variables (or a `.env` file — see [`.env.example`](.env.example)).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DALGO_API_URL` | Yes | `http://localhost:8002` | Dalgo API base URL |
| `DALGO_USERNAME` | stdio only | — | Dalgo login email |
| `DALGO_PASSWORD` | stdio only | — | Dalgo login password |
| `DALGO_ORG_SLUG` | stdio only | — | Dalgo organization slug |
| `DALGO_TRANSPORT` | No | `stdio` | `stdio` or `streamable-http` |
| `DALGO_HOST` | No | `0.0.0.0` | HTTP server bind address |
| `DALGO_PORT` | No | `8080` | HTTP server port |

## Usage

### Claude Desktop

Add the server to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

### Claude Code

If you prefer manual setup over the [plugin](#quick-start):

```bash
claude mcp add --transport stdio dalgo -- uv run --directory /path/to/dalgo-mcp dalgo-mcp
```

Credentials are read from the `.env` file in the project directory.

### Anthropic Messages API (remote)

Run the server in `streamable-http` mode so any user can connect with a URL and their own Dalgo JWT — no local setup required:

```bash
DALGO_TRANSPORT=streamable-http \
DALGO_API_URL=https://your-dalgo-instance.com \
DALGO_HOST=0.0.0.0 \
DALGO_PORT=8080 \
uv run dalgo-mcp
```

Then connect via the [MCP connector](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector):

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

The `authorization_token` is a Dalgo JWT. Each user passes their own token and the server detects their organization automatically.

### Docker

The image runs in `streamable-http` mode on port `8079` by default.

```bash
cp .env.example .env
# Edit .env — at minimum, set DALGO_API_URL

docker build -t dalgo-mcp .
docker run --rm -p 8079:8079 --env-file .env dalgo-mcp
```

Or with Docker Compose:

```bash
docker compose up --build
```

The server is then reachable at `http://localhost:8079/`. Point the Anthropic MCP connector at that URL and pass each user's Dalgo JWT as the `authorization_token`.

## Authentication

| Mode | Auth method |
|------|------------|
| `stdio` | Username/password from `.env`; single user |
| `streamable-http` | Bearer JWT per request; multi-user, org auto-detected via `/api/currentuserv2` |

In HTTP mode the server verifies JWT structure and expiry, while the Dalgo backend validates signatures. Per-token clients are cached, so organization detection happens only once per token.

## Tool Reference

<details>
<summary><strong>All 62 tools</strong> — click to expand</summary>

<!-- TOOLS_TABLE_START -->
| Tool | Description | Category |
|------|-------------|----------|
| `dalgo_get_current_user` | Get the currently authenticated Dalgo user's profile information | Organization |
| `dalgo_get_feature_flags` | Get feature flags enabled for the current Dalgo organization | Organization |
| `dalgo_list_org_users` | List all users in the current Dalgo organization | Organization |
| `dalgo_get_table_columns` | Get column names and types for a specific warehouse table | Warehouse |
| `dalgo_get_table_data` | Fetch rows from a warehouse table. Defaults to 10 rows to avoid context overflow | Warehouse |
| `dalgo_get_table_row_count` | Get the total row count of a warehouse table | Warehouse |
| `dalgo_list_schemas` | List all schemas in the connected data warehouse | Warehouse |
| `dalgo_list_tables` | List all tables in a specific warehouse schema | Warehouse |
| `dalgo_create_pipeline` | Create a new orchestration pipeline | Pipelines |
| `dalgo_delete_pipeline` | Delete a pipeline by its deployment ID | Pipelines |
| `dalgo_get_flow_run` | Get details of a specific flow run | Pipelines |
| `dalgo_get_flow_run_logs` | Get logs for a specific flow run. Large logs are truncated to avoid context overflow — | Pipelines |
| `dalgo_get_pipeline` | Get details of a specific pipeline by its deployment ID | Pipelines |
| `dalgo_get_pipeline_run_history` | Get the run history for a specific pipeline | Pipelines |
| `dalgo_list_pipelines` | List all orchestration pipelines (Prefect deployments) in the organization | Pipelines |
| `dalgo_trigger_pipeline_run` | Trigger an immediate run of a pipeline | Pipelines |
| `dalgo_update_pipeline` | Update an existing pipeline's configuration | Pipelines |
| `dalgo_delete_source` | Delete a data source | Sources |
| `dalgo_get_source` | Get details of a specific data source | Sources |
| `dalgo_get_sources_models` | Get all available sources and models with their columns | Sources |
| `dalgo_list_source_definitions` | List all available Airbyte source definitions (connector types) | Sources |
| `dalgo_list_sources` | List all configured data sources (Airbyte sources) in the organization | Sources |
| `dalgo_get_connection` | Get details of a specific Airbyte connection | Connections |
| `dalgo_get_connection_catalog` | Get the stream catalog for an Airbyte connection (selected streams and sync modes) | Connections |
| `dalgo_get_sync_history` | Get sync run history for an Airbyte connection | Connections |
| `dalgo_list_connections` | List all Airbyte connections (source-to-destination syncs) in the organization | Connections |
| `dalgo_create_dashboard` | Create a new dashboard | Dashboards |
| `dalgo_delete_dashboard` | Delete a dashboard | Dashboards |
| `dalgo_get_dashboard` | Get details of a specific dashboard including its charts | Dashboards |
| `dalgo_list_dashboards` | List all dashboards in the organization | Dashboards |
| `dalgo_update_dashboard` | Update an existing dashboard | Dashboards |
| `dalgo_create_chart` | Create a new chart | Charts |
| `dalgo_delete_chart` | Delete a chart | Charts |
| `dalgo_get_chart` | Get details of a specific chart | Charts |
| `dalgo_get_chart_data` | Execute a chart's query and return the resulting data | Charts |
| `dalgo_list_charts` | List all charts in the organization | Charts |
| `dalgo_update_chart` | Update an existing chart | Charts |
| `dalgo_create_report` | Create a new report (data snapshot) | Reports |
| `dalgo_delete_report` | Delete a report | Reports |
| `dalgo_get_report` | View a specific report's data | Reports |
| `dalgo_list_reports` | List all saved reports (data snapshots) in the organization | Reports |
| `dalgo_acquire_canvas_lock` | Acquire a lock on the transform canvas. Required before making any canvas modifications | Transforms |
| `dalgo_add_source_to_canvas` | Add an existing source or model to the canvas as a node | Transforms |
| `dalgo_create_operation` | Create a new operation node on the canvas (join, filter, rename, aggregate, etc.) | Transforms |
| `dalgo_edit_operation` | Edit an existing operation node on the canvas | Transforms |
| `dalgo_get_data_types` | Get the list of warehouse-specific data types (used for cast operations) | Transforms |
| `dalgo_get_dbt_workspace` | Get the dbt workspace configuration for the organization | Transforms |
| `dalgo_get_git_status` | Get the git status of the dbt project repository (modified/untracked files) | Transforms |
| `dalgo_get_node_columns` | Get column names and data types for a specific canvas node | Transforms |
| `dalgo_get_node_details` | Get full details of a canvas node including its operation config and input nodes | Transforms |
| `dalgo_get_transform_graph` | Get the dbt project DAG (directed acyclic graph) showing model dependencies | Transforms |
| `dalgo_publish_changes` | Commit and push dbt project changes to git | Transforms |
| `dalgo_release_canvas_lock` | Release the lock on the transform canvas after modifications are complete | Transforms |
| `dalgo_run_dbt` | Trigger a dbt run via Celery (async task). Optionally pass command and flags | Transforms |
| `dalgo_sync_sources` | Sync dbt sources from the connected warehouse, updating the dbt project's source definitions | Transforms |
| `dalgo_terminate_chain` | Materialize an operation chain into a dbt model | Transforms |
| `dalgo_get_unread_count` | Get the count of unread notifications | Notifications |
| `dalgo_list_notifications` | List recent notifications for the current user | Notifications |
| `dalgo_mark_notifications_read` | Mark notifications as read | Notifications |
| `dalgo_get_doc` | Fetch and return the full content of a Dalgo documentation page | Documentation |
| `dalgo_list_docs` | List all Dalgo documentation pages grouped by section | Documentation |
| `dalgo_search_docs` | Search Dalgo documentation by keyword | Documentation |
<!-- TOOLS_TABLE_END -->

</details>

The table above is auto-generated. After adding or changing tools, regenerate it with:

```bash
uv run python scripts/generate_tool_table.py
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run the test suite
uv run pytest

# Lint
uv run ruff check .

# Format check
uv run ruff format --check .
```

CI runs lint and tests on every push to `main` and on all pull requests.

## Project Structure

```
.claude-plugin/
└── plugin.json      # Claude Code plugin manifest
.mcp.json            # MCP server config for plugin mode
scripts/
├── generate_tool_table.py   # Regenerates the README tool table
└── measure_token_cost.py    # Measures tool-schema token footprint
src/dalgo_mcp/
├── config.py        # Environment config and validation
├── auth.py          # JWT token verifier for HTTP mode
├── client.py        # Async Dalgo API client with auto-auth
├── server.py        # FastMCP app, dual transport, client resolution
├── login.py         # Username/password login flow
├── oauth.py         # OAuth flow
├── pii.py           # PII handling utilities
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
tests/               # Pytest suite
```

## Releases

This project follows [Semantic Versioning](https://semver.org). Every release is tagged as `v<version>` and documented in the [CHANGELOG](CHANGELOG.md); see the [releases page](https://github.com/DalgoT4D/dalgo-mcp/releases) for downloadable artifacts and notes.

Release process:

1. Bump `version` in `pyproject.toml` and add a section to `CHANGELOG.md`.
2. Commit, then tag: `git tag v<version> && git push origin v<version>`.
3. The [publish workflow](.github/workflows/publish.yml) builds the package and publishes it to PyPI automatically.
4. Create a GitHub release from the tag with the changelog notes.

## Contributing

Contributions are welcome! To get started:

1. Fork the repository and create a feature branch.
2. Make your changes, keeping `ruff` clean and tests passing (`uv run ruff check . && uv run pytest`).
3. If you added or changed tools, regenerate the tool table (`uv run python scripts/generate_tool_table.py`).
4. Open a pull request with a clear description of the change.

Found a bug or have a feature request? Please [open an issue](https://github.com/DalgoT4D/dalgo-mcp/issues).

## About Dalgo

[Dalgo](https://dalgo.in) is an open-source data platform built by [Project Tech4Dev](https://projecttech4dev.org) for the social sector, combining data ingestion (Airbyte), transformation (dbt), orchestration (Prefect), and visualization in one place.

## License

Released under the [MIT License](LICENSE).

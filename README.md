# Dalgo MCP Server

MCP server for the [Dalgo](https://dalgo.in) ELT orchestration platform. Gives AI assistants access to your data warehouse, pipelines, dashboards, charts, reports, and more — via natural language.

Supports two transports:
- **stdio** — for Claude Desktop and Claude Code (local setup)
- **streamable-http** — for the Anthropic Messages API MCP connector (remote, no local setup needed)

## Tools

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
| `dalgo_get_flow_run_logs` | Get logs for a specific flow run | Pipelines |
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

**62 tools total.**

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

### Docker

The image runs in `streamable-http` mode on port `8079` by default.

```bash
cp .env.example .env
# Edit .env — at minimum, set DALGO_API_URL

docker build -t dalgo-mcp .
docker run --rm -p 8079:8079 --env-file .env dalgo-mcp
```

Or with Compose:

```bash
docker compose up --build
```

The server will be reachable at `http://localhost:8079/`. Point the Anthropic MCP connector at that URL and pass each user's Dalgo JWT as the `authorization_token`.

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

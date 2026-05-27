# Dalgo MCP — Claude Context

## Project Overview

MCP server for the [Dalgo](https://dalgo.in) ELT orchestration platform. Exposes **51 tools** across 11 modules so AI assistants can interact with data warehouses, pipelines, dashboards, charts, reports, and more via natural language.

**Repo:** `DalgoT4D/dalgo-mcp`  
**Language:** Python 3.10+  
**Package manager:** `uv`  
**Build backend:** Hatchling  

## Repository Structure

```
.claude-plugin/
└── plugin.json          # Claude Code plugin manifest
.mcp.json                # MCP server config for plugin mode
.env.example             # Template for required env vars
pyproject.toml           # Project metadata and dependencies
src/dalgo_mcp/
├── __init__.py
├── config.py            # Env config and validation
├── auth.py              # JWT verifier for HTTP mode
├── client.py            # Async Dalgo API client with auto-auth
├── server.py            # FastMCP app, dual transport, client resolution
├── login.py             # Username/password login flow
├── oauth.py             # OAuth flow
├── pii.py               # PII handling utilities
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

## Key Dependencies

- `mcp>=1.27.0` — MCP SDK (FastMCP)
- `httpx>=0.27.0` — Async HTTP client
- `pydantic>=2.0` — Config validation
- `python-dotenv>=1.0.0` — Env var loading
- `pyjwt>=2.0.0` — JWT verification for HTTP mode

## Transports

| Mode | Auth | Use case |
|------|------|----------|
| `stdio` | Username/password from `.env` | Claude Desktop / Claude Code (local) |
| `streamable-http` | Bearer JWT per request | Anthropic Messages API MCP connector (remote) |

## Local Dev Setup

```bash
git clone https://github.com/DalgoT4D/dalgo-mcp.git
cd dalgo-mcp
cp .env.example .env
# Fill in DALGO_API_URL, DALGO_USERNAME, DALGO_PASSWORD, DALGO_ORG_SLUG
uv sync
uv run dalgo-mcp
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DALGO_API_URL` | Yes | `http://localhost:8002` | Dalgo API base URL |
| `DALGO_USERNAME` | stdio only | | Dalgo login email |
| `DALGO_PASSWORD` | stdio only | | Dalgo login password |
| `DALGO_ORG_SLUG` | stdio only | | Dalgo organization slug |
| `DALGO_TRANSPORT` | No | `stdio` | `stdio` or `streamable-http` |
| `DALGO_HOST` | No | `0.0.0.0` | HTTP bind address |
| `DALGO_PORT` | No | `8080` | HTTP port |

## Current State (as of 2026-05-27)

- **No GitHub Actions workflows exist yet** — `.github/workflows/` directory is absent from the repo.
- Active development branch: `claude/github-actions-review-C6UME`

## Pending Work

- [ ] Set up CI workflow (lint + tests on push/PR)
- [ ] Set up PyPI publish workflow (on version tag)
- [ ] Decide on linter (ruff is the standard for modern Python projects)
- [ ] Add a test suite if none exists

## Notes for New Sessions

- Always develop on the branch `claude/github-actions-review-C6UME` unless instructed otherwise.
- The repo uses `uv` — don't use `pip` or `poetry`.
- No test files have been found yet; check `src/` before assuming tests need to be created from scratch.
- When adding GitHub Actions, target Python 3.10 as minimum (matches `requires-python`).

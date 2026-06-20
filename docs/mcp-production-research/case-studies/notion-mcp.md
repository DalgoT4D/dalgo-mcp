# Case study: Notion MCP

**Repo:** makenotion/notion-mcp-server · **Lang:** TypeScript ·
**Hosting:** `mcp.notion.com` (OAuth) + local npx/Docker · **Stars:** ~4.4k · **License:** MIT

The reference example for **remote-OAuth-first** strategy and **per-request token
passthrough** for multi-tenant deployments.

## Hosting & transport
- **Remote (officially supported):** OAuth at `mcp.notion.com` — "easy installation via
  standard OAuth," no token management for users.
- **Local (being de-emphasized):** `npx @notionhq/notion-mcp-server` or Docker
  (`mcp/notion`). README notes they "may sunset this local MCP server repository."
- Transports: **stdio** (default) and **streamable-http** (`--transport http --port <port>`).

## Auth ← the standout
- Remote: OAuth.
- Local: a Notion integration token (`NOTION_TOKEN=ntn_****`), with scope controlled by
  the integration's *Capabilities* (e.g. "Read content" → effectively read-only).
- **HTTP mode auth:** bearer via `--auth-token` / `AUTH_TOKEN`, **plus
  `--enable-token-passthrough` for multi-tenant** — each request carries its own token.

## Tool surface
- v2.0.0: 22 tools; discovered automatically at startup; API version headers sourced
  per-operation from the OpenAPI spec (the server is OpenAPI-generated).

## What to copy for dalgo-mcp
- **Token passthrough per request** is exactly our multi-tenant HTTP model — validates it.
- "Integration capabilities = read-only" mirrors using backend permissions to scope the MCP.
- A clear stance on remote-first vs local (we currently lead with local/plugin — worth
  deciding which is primary as we host).

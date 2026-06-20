# Case study: Cloudflare MCP servers

**Repo:** cloudflare/mcp-server-cloudflare · **Lang:** TypeScript (monorepo) ·
**Hosting:** `*.mcp.cloudflare.com` (Workers) · **Stars:** ~3.8k · **License:** Apache-2.0

The reference example for **edge/serverless remote hosting** and a **multi-server**
fleet sharing infrastructure.

## Architecture
- Monorepo of ~18 product-specific MCP servers (`apps/*`): observability, workers
  bindings, AI gateway, audit logs, AutoRAG, browser rendering, DNS analytics, Radar,
  Logpush, etc. Each at its own URL `<product>.mcp.cloudflare.com/mcp`.
- A separate broader "Code Mode" server lives in `cloudflare/mcp` at `mcp.cloudflare.com`.
- A dedicated **`workers-observability`** MCP — observability treated as first-class.

## Transport
- **streamable-http** at `/mcp`; **SSE** at `/sse` (explicitly deprecated).

## Auth
- OAuth-based remote auth; the broader Cloudflare stack uses the
  **`workers-oauth-provider`** library (separate repo) to add OAuth to Workers MCP servers.
- Tokens scoped to the permissions each product server needs.

## Local bridging
- `mcp-remote` (npm) bridges local stdio clients to the remote HTTP servers.

## What to copy for dalgo-mcp
- If we go edge: streamable-http on `/mcp`, drop SSE.
- The OAuth-provider-as-a-library pattern for remote auth.
- A dedicated observability surface.
- `mcp-remote` as the documented local→remote bridge for clients that only speak stdio.

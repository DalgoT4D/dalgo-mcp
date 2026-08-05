# Case study: Sentry MCP

**Repo:** getsentry/sentry-mcp · **Lang:** TypeScript (monorepo) ·
**Hosting:** `https://mcp.sentry.dev` (Cloudflare) · **Stars:** ~724

The reference example for **testing/evals** and **self-observability** on a hosted,
remote MCP.

## Hosting & transport
- Remote HTTP service at `mcp.sentry.dev`, "middleware to the upstream Sentry API,"
  built on Cloudflare's remote-MCP architecture.
- stdio is secondary ("work in progress").
- Deploy automated via `.github/workflows/deploy.yml`.

## Auth
- OAuth for the remote service (`SENTRY_CLIENT_ID` / `SENTRY_CLIENT_SECRET`,
  callback `http://localhost:5173/oauth/callback` in dev).
- Scoped user auth tokens: `org:read, project:read, project:write, team:read,
  team:write, event:write`.
- stdio mode uses `SENTRY_ACCESS_TOKEN`.

## Tool surface & gating
- AI-powered tools (`search_events`, `search_issues`, agent-mode `use_sentry`)
  require an LLM provider (`EMBEDDED_AGENT_PROVIDER` = `openai`|`anthropic`).
- **Graceful degradation:** without a provider, "all other tools function normally."
- Skills/features disableable via `MCP_DISABLE_SKILLS` (e.g. `seer` for self-hosted).

## Testing & evals ← the standout
A dedicated package per testing concern (monorepo `packages/`):
- `mcp-server-evals` — LLM evals (`pnpm eval`, needs `OPENAI_API_KEY`).
- `mcp-server-mocks` — mock upstream API.
- `mcp-test-client` — a programmatic MCP client for tests.
- `smoke-tests` — end-to-end smoke.
- `agent-cli-test` — CLI to exercise the server like an agent.
- MCP Inspector via `pnpm inspector`.
- CI workflows: `test.yml`, `eval.yml`, `smoke-tests.yml`, **`token-cost.yml`**,
  `release.yml`, `mcp-server-package.yml`.

## Observability
- Sentry **dogfoods Sentry** — errors and tracing on its own MCP server.

## Notable extra
- The `mcp-cloudflare` package ships a full **web playground / landing page** with
  a chat UI and per-host install tabs.

## What to copy for dalgo-mcp
- A testing pyramid: evals + mocks + a test client + smoke tests as separate concerns.
- A **token-cost CI gate** (we already have `scripts/measure_token_cost.py`).
- Self-observability with error reporting + tracing.
- Graceful per-capability degradation (relevant given our chart-data 500s).

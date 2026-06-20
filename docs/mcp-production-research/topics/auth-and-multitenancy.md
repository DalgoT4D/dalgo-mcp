# Topic: Auth & multi-tenancy

How production MCP servers authenticate users and isolate tenants.

## The consensus model
**Remote = OAuth 2.1; per-request token → identity → tenant.** Each end-user's own
token scopes them to their own data; the server holds no shared super-credential.

| Server | Remote auth | Local auth | Scoping primitive |
|--------|-------------|-----------|-------------------|
| Stripe | OAuth (`mcp.stripe.com`) | `--api-key` | **Restricted API Key** grants = tool permissions |
| Notion | OAuth (`mcp.notion.com`) | integration token (`NOTION_TOKEN`) | integration *Capabilities* (e.g. read-only) |
| GitHub | OAuth / GitHub App | PAT (`GITHUB_PERSONAL_ACCESS_TOKEN`) | token scopes per toolset |
| Sentry | OAuth (client id/secret) | `SENTRY_ACCESS_TOKEN` | scoped token (`org:read`, `project:write`, …) |
| Grafana | — | service account token | service-account permissions; `GRAFANA_ORG_ID` |
| Cloudflare | OAuth (`workers-oauth-provider`) | `mcp-remote` bridge | per-product token scope |
| dalgo-mcp | OAuth + per-request JWT | username/password → JWT | backend RBAC + org via `x-dalgo-org` |

## Key patterns
- **Reuse the platform's permission primitive** instead of inventing MCP-specific RBAC.
  Stripe (RAK), Notion (integration capabilities), and dalgo-mcp (backend roles) all do
  this — lowest maintenance, and the LLM can never exceed the user's own rights.
- **Per-request token passthrough for multi-tenancy.** Notion's `--enable-token-passthrough`
  and Grafana's `GRAFANA_FORWARD_HEADERS` allowlist are explicit mechanisms; dalgo-mcp
  caches a client per JWT.
- **Scoped / short-TTL tokens for MCP use.** Stripe's RAK is the model: a restricted key
  minted specifically for the agent. Long-lived full-access tokens in an LLM client are a
  liability (dalgo-mcp issues 12h full-access JWTs — see production-readiness B4).

## Tenant isolation — verify it server-side
The backend, not the MCP, must enforce that a token can only reach its own tenant.
dalgo-mcp's backend does this correctly: it filters `OrgUser` by `user` **and** org slug,
so spoofing the org header fails (`DDP_backend/ddpui/auth.py:61-65,139-143`). Because the
backend validates the JWT signature, the MCP can skip local verification — but add JWKS
verification for defense-in-depth if the MCP ever makes trust decisions itself.

## Pitfalls
- **In-memory OAuth state** doesn't survive restarts or scale horizontally — use a shared
  store (Redis) before running multiple replicas.
- **Multi-org users**: don't silently pick `org[0]`; let the client choose the target org.

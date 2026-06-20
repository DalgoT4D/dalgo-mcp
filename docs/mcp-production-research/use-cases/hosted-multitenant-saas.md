# Use case: Hosted, multi-tenant SaaS MCP

One MCP service the vendor runs; every user connects with their own token and only sees
their own tenant's data. **This is the archetype dalgo-mcp's OAuth + streamable-http code
points at.**

**Examples:** Sentry (`mcp.sentry.dev`), GitHub (`api.githubcopilot.com/mcp/`),
Stripe (`mcp.stripe.com`), Notion (`mcp.notion.com`), Cloudflare (`*.mcp.cloudflare.com`).

## What this archetype requires
- **Transport:** streamable-http (not SSE).
- **Auth:** OAuth 2.1; per-request token → identity → tenant. Scoped/short-TTL tokens.
- **Tenant isolation:** enforced server-side (the backend, not the MCP).
- **Stateless per request:** no in-memory OAuth/session state → externalize to Redis so
  replicas are interchangeable.
- **Rate limiting + quotas:** per-token and per-org, at the edge, to protect the backend.
- **Observability:** metrics, tracing, error reporting, audit of who-did-what.
- **Scaling:** horizontal behind a load balancer; liveness/readiness health checks.
- **Secrets:** from a manager, not a baked `.env`.

## dalgo-mcp gap snapshot (see production-readiness.md)
Have: OAuth/PKCE/refresh, per-token client cache, backend-enforced tenant isolation.
Need: Redis-backed token store, rate limiting, scoped tokens, metrics/tracing,
secret-log redaction, GHCR image, fixed deploy config.

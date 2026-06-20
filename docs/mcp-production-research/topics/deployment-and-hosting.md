# Topic: Deployment & hosting

## Transport
- **stdio** for local clients; **streamable-http** for remote. **SSE is deprecated**
  (Cloudflare serves `/mcp` streamable-http + a deprecated `/sse`; Grafana offers all three).
- Local→remote bridges exist for stdio-only clients: `mcp-remote` (Cloudflare/Notion).

## Hosting topologies
| Pattern | Examples | Notes |
|---------|----------|-------|
| Edge / serverless | Sentry, Cloudflare (Workers) | stateless per request; token→tenant; scales naturally |
| Hosted HTTP service | GitHub (`api.githubcopilot.com/mcp/`) | behind the vendor's own infra |
| Self-host container | Grafana, GitHub local, dalgo-mcp | Docker image + (often) Helm |
| Local stdio / plugin | dbt-mcp, dalgo-mcp plugin | per-user, creds in env |

## Containers & distribution
- Publish an image to a registry: GitHub → `ghcr.io/github/github-mcp-server`;
  Grafana → `grafana/mcp-grafana` + **Helm chart**. (dalgo-mcp builds locally only — gap.)
- Harden: multi-stage build, non-root user, locked deps (dalgo-mcp already does this).
- Add a Docker **`HEALTHCHECK`** and split **liveness vs readiness** (readiness should
  verify the upstream API is reachable).

## Statefulness
- Prefer **stateless per request** so any replica can serve any token.
- If you keep sessions, bound them: Grafana's `--session-idle-timeout-minutes` (default 30).
- Anything in-memory (OAuth codes/tokens, caches) blocks horizontal scaling — externalize it.

## TLS & proxy
- Terminate TLS at a proxy or in-process (Grafana's `--server.tls-cert-file`).
- Keep upstream-client TLS options for connecting to the backend.
- Reconcile ports across app/proxy/compose/docs (dalgo-mcp currently mismatches
  `:8079`/`:8081`/`:8080` — see production-readiness A8).

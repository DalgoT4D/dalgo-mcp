# MCP in Production — research library

How teams build, host, and operate Model Context Protocol servers in production.
Every claim is grounded in direct inspection of real repos and official docs
(June 2026), with `repo`/`file`/`flag` citations so it stays verifiable.

This library exists to inform productionizing **dalgo-mcp**. For our specific
plan, see the sibling docs:
- [`../research/mcp-production-harness.md`](../research/mcp-production-harness.md) — the 12-dimension harness taxonomy.
- [`../research/production-readiness.md`](../research/production-readiness.md) — our two-track (MCP + backend) gap analysis and roadmap.

## Structure

| Folder | What's in it |
|--------|--------------|
| [`case-studies/`](./case-studies/) | Per-server deep dives — how each notable MCP server is actually built. |
| [`topics/`](./topics/) | Cross-cutting themes (auth, hosting, gating, observability, rate limiting, testing, release) with comparisons across servers. |
| [`use-cases/`](./use-cases/) | Deployment archetypes and which patterns each one needs. |
| [`examples/`](./examples/) | Concrete, copyable config/code snippets. |

## Servers studied

| Server | Lang | Hosted? | Notable for |
|--------|------|---------|-------------|
| [dbt-mcp](./case-studies/dbt-mcp.md) | Python | no | toolset gating, changie releases, mcpb, framework examples |
| [Sentry](./case-studies/sentry-mcp.md) | TS | `mcp.sentry.dev` | eval/test pyramid, token-cost CI, self-observability |
| [GitHub](./case-studies/github-mcp-server.md) | Go | `api.githubcopilot.com/mcp/` | toolsets, read-only, lockdown mode |
| [Cloudflare](./case-studies/cloudflare-mcp.md) | TS | `*.mcp.cloudflare.com` | edge/Workers, OAuth provider, multi-server monorepo |
| [Stripe](./case-studies/stripe-mcp.md) | TS | `mcp.stripe.com` | restricted API keys as the permission model |
| [Notion](./case-studies/notion-mcp.md) | TS | `mcp.notion.com` | OAuth-remote-first, token passthrough |
| [Grafana](./case-studies/grafana-mcp.md) | Go | self-host | tool categories, `--disable-write`, Prometheus metrics, TLS, Helm |

## The 10 things that separate production from prototype

1. OAuth 2.1 + scoped, least-privilege tokens; per-request identity → tenant.
2. Toolset gating + a read-only mode (universal across mature servers).
3. Token cost treated as a tracked metric (Sentry gates it in CI).
4. Evals, not just unit tests — verify an LLM can actually use the tools.
5. Remote hosting on managed/edge infra; stateless-per-request design.
6. Self-observability: structured logs, metrics, tracing, error reporting.
7. Prompt-injection / data-egress defenses (e.g. GitHub lockdown mode).
8. Automated semver releases + multiple channels (PyPI/npm, GHCR, mcpb, registry).
9. Distribution-grade DX: one-command installs, per-host config, framework examples.
10. Governance hygiene (CONTRIBUTING, templates, CODEOWNERS, dependabot).

# Use case: Self-hosted, single-tenant MCP

Each organization runs its own MCP next to its own instance of the platform. One org,
credentials in env, minimal ops.

**Examples:** Grafana MCP, GitHub MCP (local Docker/binary), dbt-mcp, dalgo-mcp plugin/stdio.

## What this archetype requires
- **Transport:** stdio (for a local client) or single-tenant streamable-http on the org's network.
- **Auth:** a single service token / credentials in env (no OAuth needed).
- **Packaging:** a hardened container image + clear quickstart; ideally a Helm chart
  (Grafana) for k8s shops.
- **Upgrades:** versioned images, a changelog, and a documented upgrade path.
- **Operability, scaled down:** health check, structured logs, optional `/metrics`.
- **Safety:** read-only mode and toolset gating still matter (limit blast radius even
  for a trusted single tenant).

## Notes
- Far simpler than multi-tenant: no shared token store, no per-tenant isolation logic,
  no edge auth. Most of the "hard" production work disappears.
- dalgo-mcp already supports this well via the Claude Code plugin + stdio + Docker; the
  main adds are a published image, read-only/gating, and a runbook.

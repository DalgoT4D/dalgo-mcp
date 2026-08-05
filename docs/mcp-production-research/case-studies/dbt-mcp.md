# Case study: dbt-mcp

**Repo:** dbt-labs/dbt-mcp · **Lang:** Python · **Hosting:** local (stdio) ·
**Stars:** ~578 · **License:** Apache-2.0

The closest analog to dalgo-mcp: a Python MCP server fronting a data platform with
many tools across distinct product areas.

## Hosting & transport
- Local-first (stdio); connects dbt Core, dbt Fusion, and dbt Platform.

## Auth
- Platform access via a service token (`DBT_TOKEN`) + host/env IDs
  (`DBT_HOST`, `DBT_PROD_ENV_ID`, `DBT_DEV_ENV_ID`, `DBT_USER_ID`).
- A `config/config_providers/` layer abstracts where settings resolve from
  (admin API, discovery, semantic layer).

## Tool surface & gating ← the standout
- **Toolset enable/disable by env var**, one per product surface:
  `DBT_MCP_ENABLE_SEMANTIC_LAYER`, `DBT_MCP_ENABLE_DISCOVERY`,
  `DBT_MCP_ENABLE_DBT_CLI`, `DBT_MCP_ENABLE_ADMIN_API`, `DBT_MCP_ENABLE_DBT_CODEGEN`,
  `DBT_MCP_ENABLE_LSP`, `DBT_MCP_ENABLE_SQL`.
- Plus `DISABLE_TOOLS` for individual tools.
- Per-section **safety warnings** in the README (the dbt CLI tools "could modify
  your data models… proceed only if you trust the client").

## Testing
- `evals/` directory with LLM-driven evals (e.g. semantic-layer eval tests).

## Release & distribution
- **changie** for changelog automation (`.changie.yaml` maps change kinds →
  semver bump: Breaking→major, Enhancement→minor, Bug Fix→patch).
- A `Create release PR` workflow computes the bump and regenerates the changelog;
  merging it triggers the release.
- A `.claude/skills/release-dbt-mcp` **skill** that drives the whole release flow.
- Ships an experimental **`dbt-mcp.mcpb`** bundle per release for MCPB-aware clients.
- Dependencies pinned; only security updates auto-PR'd.

## Docs / DX
- `examples/` with runnable agents for **many frameworks**: LangGraph, CrewAI,
  Google ADK, OpenAI SDK, Vercel AI SDK, AWS Strands.
- Governance: CONTRIBUTING, issue templates, PR template, CODEOWNERS, dependabot,
  OpenSSF Best Practices badge.

## What to copy for dalgo-mcp
- `DALGO_ENABLE_<module>` gating mirroring our 11 modules + a `DISABLE_TOOLS`.
- changie to kill the manual changelog step; a release skill.
- An `.mcpb` bundle and 1–2 framework examples.
- Per-section safety warnings on destructive tool groups.

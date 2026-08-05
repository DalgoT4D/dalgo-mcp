# Topic: Release & distribution

## Versioning & changelog
- Semantic versioning, tag `v<x.y.z>`.
- **Automate the changelog.** dbt-mcp uses **changie** (`.changie.yaml` maps change kinds
  to bump levels) + a `Create release PR` workflow; merging it triggers the release. dbt
  even has a `.claude/skills/release-*` skill that drives the flow.
- Keep version in sync across manifests (dalgo-mcp drifts between `pyproject.toml` and
  `plugin.json` — automate or single-source it).

## Distribution channels (ship several)
| Channel | Who uses it | dalgo-mcp status |
|---------|-------------|------------------|
| PyPI / npm | language-native installs | ✅ PyPI (OIDC trusted publish), pending publisher setup |
| Container registry | hosted/self-host | ❌ no GHCR push (gap) — GitHub & Grafana publish images |
| Helm chart | Kubernetes | ❌ — Grafana ships one |
| **mcpb bundle** | MCPB-aware hosts (Claude Desktop) | ❌ — dbt ships `dbt-mcp.mcpb` per release |
| MCP registry | discovery | ❌ — `modelcontextprotocol/registry` exists |
| Editor plugin | Claude Code | ✅ plugin + skills |

## Recommended additions for dalgo-mcp
1. A **GHCR build-and-push** workflow on tags (biggest distribution gap for a hosted server).
2. An **`.mcpb`** bundle per release so Claude Desktop installs without hand-edited JSON.
3. **changie** to remove the manual changelog step.
4. Single-source the version (derive `plugin.json` from `pyproject.toml`).
5. A **registry listing** once the server is stable.

## Open question
`mcpb` vs editor plugin vs registry are three overlapping distribution mechanisms with no
clear single winner yet; registry trust/signing is still early. Ship the channels your
actual users need rather than all of them.

## Governance hygiene (cheap maturity signals)
CONTRIBUTING, issue/PR templates, CODEOWNERS, dependabot, and an OpenSSF badge — dbt-mcp
has all of these; dalgo-mcp has none yet.

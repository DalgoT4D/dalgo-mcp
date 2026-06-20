# Topic: Tool surface & gating

Every mature multi-tool MCP server lets operators control which tools load and run a
read-only mode. This is both a **token-cost** lever (each tool's schema costs context on
every request) and a **safety** lever (hide destructive tools).

## Gating mechanisms compared
| Server | Group gating | Per-tool | Read-only | Injection defense |
|--------|-------------|----------|-----------|-------------------|
| GitHub | `--toolsets`/`GITHUB_TOOLSETS` (16 sets, `default`/`all`) | `--tools` | `--read-only`/`GITHUB_READ_ONLY` | `GITHUB_LOCKDOWN_MODE` |
| Grafana | `--enabled-tools` categories; `--disable-<category>` | — | `--disable-write` | — |
| dbt-mcp | `DBT_MCP_ENABLE_*` per surface | `DISABLE_TOOLS` | (per-tool safety notes) | — |
| Sentry | `MCP_DISABLE_SKILLS`; AI tools gated on LLM provider | — | — | — |
| dalgo-mcp | ❌ none (all 63 always on) | ❌ | ❌ | ❌ |

## Recommended design (for dalgo-mcp)
- `DALGO_ENABLE_<MODULE>` for our 11 modules (mirrors dbt/Grafana categories).
- A **read-only mode** that hides every mutating tool — we already set
  `destructiveHint`/`readOnlyHint` annotations per tool, so a filter is mechanical.
- `default` vs `all` presets so most users get a small, cheap surface.
- Consider a lockdown-style flag when feeding untrusted data into tools.

## Token-cost control
- Sentry runs a **`token-cost.yml`** CI job; dbt and dalgo measure schema token cost.
- Fewer enabled tools = smaller per-request prompt = lower cost and better tool selection.
- Pagination/row caps and truncation keep tool *outputs* bounded (dalgo defaults
  `get_table_data` to 10 rows and truncates logs).

## Other surface concerns
- **Fail fast** on invalid tool names at startup; keep **aliases** for renamed tools (GitHub).
- **Dynamic toolset discovery** (GitHub) loads tool groups on demand to keep the base set small.

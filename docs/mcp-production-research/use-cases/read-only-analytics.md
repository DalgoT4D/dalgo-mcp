# Use case: Read-only analytics / "ask your data" MCP

The MCP exposes only safe, read-only tools — browse data, run queries, view dashboards —
with all mutating tools disabled. Lowest risk; ideal first production rollout.

**Relevant patterns:** Grafana `--disable-write`; GitHub `--read-only`; Notion integration
"Read content" capability; Stripe RAK with read-only grants.

## Why start here for dalgo-mcp
- Most user value (explore warehouse, charts, dashboards, pipeline status) is read-only.
- Eliminates the scariest failure mode: an agent deleting a pipeline/chart or kicking off
  a dbt run. Our destructive tools already carry `destructiveHint` annotations.
- Smaller tool surface → lower token cost and better tool selection.

## What it requires
- A **read-only flag** that hides every mutating tool (`create_*`, `update_*`, `delete_*`,
  `run_dbt`, canvas lock/publish). The annotations make this a mechanical filter.
- Output safety: PII masking on **all** data-returning tools (dalgo-mcp masks only 2 today),
  plus row caps/truncation.
- Read-friendly rate limits/quotas on expensive query tools (chart-data, warehouse).

## Rollout ladder
1. Read-only, internal pilot.
2. Read-only, broad rollout.
3. Enable mutating tools per-toolset, behind explicit opt-in + confirmation UX.

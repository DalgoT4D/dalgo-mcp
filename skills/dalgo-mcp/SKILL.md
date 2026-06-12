---
name: dalgo-mcp
description: Route Dalgo MCP tool workflows. Use when a request involves Dalgo data, pipelines, syncs, transforms, dashboards, charts, or reports, to pick the right domain skill and stay on MCP tools.
---

# dalgo-mcp

Use for routing any Dalgo request to the narrowest domain skill.

## Always

- Use the `dalgo_*` MCP tools for all Dalgo work. Do not call the Dalgo REST API directly with curl, httpx, or Python requests.
- Call tools directly with the obvious parameters; fetch a tool's schema only after a validation error. These skills are workflow guidance, not schema definitions.
- Never report an async operation (pipeline run, sync, dbt run) as successful based only on the trigger response. Each domain skill defines its verification loop — follow it.
- If the MCP tools cannot satisfy the request, say which capability is missing and point the user to the Dalgo web UI. Do not switch to direct API calls.
- For questions about Dalgo itself (features, how-to, concepts), use `dalgo_search_docs`, `dalgo_list_docs`, and `dalgo_get_doc` before answering from memory.

## Decision Rules

- Exploring warehouse schemas, tables, columns, or row data: use `dalgo-warehouse`.
- Running, scheduling, creating, or checking orchestration pipelines: use `dalgo-pipelines`.
- Airbyte sources, connections, stream catalogs, or sync history: use `dalgo-ingestion`.
- dbt models, the transform canvas, operations, or `dbt run`: use `dalgo-transforms`.
- Charts, dashboards, or reports: use `dalgo-visualization`.
- Diagnosing any failure (pipeline, sync, dbt) or checking notifications: use `dalgo-troubleshooting`.
- A request spanning domains (e.g. "sync the data then run transforms") chains skills in data-flow order: ingestion → pipelines → transforms → warehouse → visualization.

## Workflow Order

1. Identify the Dalgo domain(s) in the request.
2. Load the narrowest domain skill and follow its workflow.
3. Resolve names to IDs with the domain's `list_*` tool before calling detail or mutation tools.
4. Verify async operations to a terminal state before reporting success.

## Retrieve

- Tool categories: [references/tool-categories.md](references/tool-categories.md)

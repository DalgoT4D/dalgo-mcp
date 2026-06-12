---
name: dalgo-ingestion
description: Work with Dalgo data ingestion — Airbyte sources, connections, stream catalogs, and sync history. Use when a user asks to sync a source, check whether a sync ran, or inspect what a connection syncs.
---

# dalgo-ingestion

Use for source and connection workflows through Dalgo MCP tools.

## Always

- Know the data model: a **source** is an Airbyte connector config (`source_id`); a **connection** syncs a source into the warehouse (`connection_id`); a **pipeline** wraps a connection sync plus optional dbt steps. Syncing happens at the connection level.
- Trigger syncs via the wrapping pipeline (`dalgo-pipelines` loop), not directly — raw connection triggering is not exposed as a tool.
- Never report sync success without checking: pipeline verification loop if you triggered, `dalgo_get_sync_history` if you didn't.
- Confirm with the user before `dalgo_delete_source`; it is irreversible and breaks dependent connections.

## Decision Rules

- "Sync source X": find the source, find its connection, find the wrapping pipeline, then run the `dalgo-pipelines` trigger-poll-verify loop.
- "Did last night's sync work?": `dalgo_list_connections` → `dalgo_get_sync_history(connection_id)` → report the latest run's status, time, and records synced.
- "What tables does this sync?": `dalgo_get_connection_catalog(connection_id)` for streams, sync modes, and enabled state.
- "What connectors are available?": `dalgo_list_source_definitions`.
- No pipeline wraps the connection: say so and point the user to the Dalgo web UI to trigger it.

## Workflow Order

1. `dalgo_list_sources` → match by name → `source_id`.
2. `dalgo_list_connections` → connection(s) referencing that source.
3. Triggering: find the wrapping pipeline and follow `dalgo-pipelines`. Checking: `dalgo_get_sync_history`.
4. On failure, match the error against the triage patterns in the reference and suggest a concrete fix.

## Retrieve

- Tool table and sync-failure triage: [references/ingestion-workflows.md](references/ingestion-workflows.md)

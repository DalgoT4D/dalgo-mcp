---
name: dalgo-troubleshooting
description: Diagnose Dalgo failures — failed pipeline runs, sync errors, dbt errors — and handle notifications. Use when a user asks why something failed, what went wrong, or what their notifications say.
---

# dalgo-troubleshooting

Use for failure diagnosis and notifications through Dalgo MCP tools.

## Always

- Diagnose from evidence: fetch history and logs before naming a cause. Quote the actual error line, then explain it in plain language.
- Work backwards through the data flow: visualization → warehouse → transforms (dbt) → pipeline run → sync → source.
- End every diagnosis with a concrete suggested action the user can take.
- For "how does Dalgo handle X" questions during diagnosis, check `dalgo_search_docs` before answering from memory.
- Do not re-trigger a failed run as a diagnostic step; understand the failure first, then offer the re-run.

## Decision Rules

- "Why did pipeline X fail?": `dalgo_get_pipeline_run_history` → failed run's `flow_run_id` → `dalgo_get_flow_run_logs` → quote and translate the error.
- "Why is my data stale/missing?": check the last sync (`dalgo_get_sync_history`), then the last pipeline run, then whether dbt models built (`dalgo-transforms`).
- dbt errors in pipeline logs: use the error translations in `dalgo-transforms`.
- Sync errors: use the triage patterns in `dalgo-ingestion`.
- "Any notifications?" / "what did I miss?": `dalgo_get_unread_count`, then `dalgo_list_notifications`; only `dalgo_mark_notifications_read` when the user asks.

## Workflow Order

1. Locate the failing object and its most recent failed run.
2. Fetch logs or sync history for that run.
3. Identify the error line; classify it (credentials, schema drift, network, dbt model, permissions).
4. Explain cause and remedy in plain language; offer the fix or re-run.

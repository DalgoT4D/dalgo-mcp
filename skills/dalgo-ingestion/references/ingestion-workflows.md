# Ingestion Workflows

| Goal | Tool | Key parameter |
|---|---|---|
| List sources | `dalgo_list_sources` | — |
| Get source details | `dalgo_get_source` | `source_id` |
| Delete a source | `dalgo_delete_source` | `source_id` (confirm first) |
| List connector types | `dalgo_list_source_definitions` | — |
| List connections | `dalgo_list_connections` | — |
| Get connection details | `dalgo_get_connection` | `connection_id` |
| View stream catalog | `dalgo_get_connection_catalog` | `connection_id` |
| Check sync history | `dalgo_get_sync_history` | `connection_id` |
| Trigger sync via pipeline | `dalgo_trigger_pipeline_run` | `deployment_id` (see dalgo-pipelines) |

## Sync-failure triage

- **Schema drift** — "column not found", "schema mismatch", "unexpected field": the source structure changed. Refresh the connection catalog under Data > Ingest, then re-sync.
- **Credential expiry** — 401/403, "authentication failed", "token expired": update source credentials under Data > Sources.
- **Rate limiting** — 429, "rate limit exceeded": often resolves on retry; suggest off-peak scheduling.
- **Network/timeout** — "connection timed out", "unreachable": check the source system is online and accessible.
- **Partial sync** — some streams failed: report which streams (if per-stream detail is available) and re-run after fixing the failing stream.

## Example

User: "Did the beneficiary sync complete last night?"

1. `dalgo_list_connections` → connection_id for the beneficiary source
2. `dalgo_get_sync_history(connection_id)` → latest run
3. Report status, start/end time, and records synced; if it failed, triage with the patterns above.

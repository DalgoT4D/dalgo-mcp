# Source Sync and Verify

Use this guide when a user asks you to sync a data source, refresh data from a source, or check whether a sync completed.

## Understanding the Data Model

In Dalgo:
- A **source** is an Airbyte source connector configuration (e.g., "Google Sheets — Beneficiary Data"). Identified by `source_id`.
- A **connection** is a configured sync from a source to the warehouse (e.g., which streams/tables to sync and how). Identified by `connection_id`.
- **Syncing** is always done at the connection level, not the source level.
- A **pipeline** typically wraps a connection sync plus optional dbt transforms. Most users trigger syncs via pipelines, not raw connections.

Before triggering anything, determine which level the user is operating at.

---

## Rule: Never Report Sync Success Without Verifying

If you trigger a sync via a pipeline, follow the full pipeline verification loop in `prompts/pipelines/run_and_verify.md`.

If you are checking sync history directly (not triggering), see Step 3 below.

---

## Step 1: Identify What to Sync

If the user gives a source name (e.g., "beneficiary data"):
1. Call `dalgo_list_sources` to list all sources.
2. Match by name. If multiple match, ask the user to clarify.
3. Note the `source_id`.

If the user wants to trigger a sync, you need the associated connection or pipeline:
- Call `dalgo_list_connections` to find connections that reference this source.
- Match the connection by source name or ID.
- If a pipeline exists for this connection, use `dalgo_list_pipelines` and prefer triggering via the pipeline (which includes orchestration, retries, and optional dbt steps).

If the user already has a `connection_id` or `deployment_id`, skip the lookup.

---

## Step 2: Trigger the Sync

**Via pipeline (preferred):**
Follow `prompts/pipelines/run_and_verify.md` in full. The pipeline trigger → poll → verify loop applies without exception.

**Via connection directly (advanced):**
Direct connection sync triggering is not currently exposed as a tool. If the user needs a raw connection sync, suggest they use the Dalgo web UI or trigger the associated pipeline instead.

---

## Step 3: Check Sync History (No Trigger)

If the user asks "did the last sync work?" or "when was this source last synced?":
1. Call `dalgo_list_connections` to find the relevant `connection_id`.
2. Call `dalgo_get_sync_history(connection_id)` to retrieve past sync runs.
3. Look at the most recent entry. Report:
   - Status (succeeded/failed/cancelled)
   - Start and end time
   - Records synced (if available in the response)
4. If the last sync failed, report that clearly and describe what information is available about the failure.

---

## Step 4: Interpret Sync Failures

Airbyte sync failures have common root causes. When reporting a failure, try to identify the cause from available error information:

**Schema drift:** The source schema changed (new columns, renamed tables, deleted fields).
- Symptom: errors mentioning "column not found", "schema mismatch", "unexpected field"
- Suggestion: "The source schema may have changed. You can refresh the connection catalog in the Dalgo UI under Data > Ingest, or ask me to show the current catalog."

**Credential expiry:** The source credentials (API key, OAuth token, service account) expired.
- Symptom: 401/403 errors, "authentication failed", "token expired"
- Suggestion: "The source credentials may have expired. Update them in the Dalgo UI under Data > Sources."

**Rate limiting:** The source API is throttling requests.
- Symptom: 429 errors, "rate limit exceeded", "too many requests"
- Suggestion: "The source is rate-limiting the sync. This often resolves on retry — try triggering the sync again, or schedule it for off-peak hours."

**Network/timeout:** The source is unreachable or slow.
- Symptom: "connection timed out", "unreachable", "ECONNREFUSED"
- Suggestion: "There may be a network issue reaching the source. Check if the source system is online and accessible."

**Partial sync:** Some streams succeeded, others failed.
- Report which streams failed if the history response includes per-stream detail.
- Suggest re-running after addressing the failing stream's issue.

---

## Step 5: Inspect Connection Configuration

If you need to understand what a connection syncs (which tables/streams and in what mode):
1. Call `dalgo_get_connection(connection_id)` for connection details.
2. Call `dalgo_get_connection_catalog(connection_id)` to see the full list of streams, their sync modes (full refresh vs. incremental), and which are enabled.

Use this when: diagnosing why certain data isn't appearing, or when the user asks "what tables does this sync?"

---

## Quick Reference

| Goal | Tool | Key Parameter |
|------|------|---------------|
| List all sources | `dalgo_list_sources` | — |
| Get source details | `dalgo_get_source` | `source_id` |
| List connections | `dalgo_list_connections` | — |
| Get connection details | `dalgo_get_connection` | `connection_id` |
| Check sync history | `dalgo_get_sync_history` | `connection_id` |
| View stream catalog | `dalgo_get_connection_catalog` | `connection_id` |
| Trigger sync via pipeline | `dalgo_trigger_pipeline_run` | `deployment_id` |
| Poll pipeline run status | `dalgo_get_flow_run` | `flow_run_id` |
| Fetch pipeline run logs | `dalgo_get_flow_run_logs` | `flow_run_id` |

---

## Example Conversation Patterns

**User: "Sync the beneficiary data and confirm it worked."**
1. `dalgo_list_sources` → find source_id for "beneficiary data"
2. `dalgo_list_pipelines` → find pipeline that syncs this source
3. Follow pipeline run_and_verify loop (trigger → poll → report)

**User: "Did the beneficiary sync complete last night?"**
1. `dalgo_list_connections` → find connection_id for beneficiary source
2. `dalgo_get_sync_history(connection_id)` → find the most recent run
3. Report status, time, and records synced

**User: "Why did the sync fail?"**
1. `dalgo_get_sync_history(connection_id)` → find the failed run
2. Report error details if available in the history response
3. Match against common failure patterns above and suggest remediation

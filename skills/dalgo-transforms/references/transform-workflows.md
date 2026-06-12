# Transform Workflows

| Goal | Tool | Key parameter |
|---|---|---|
| View the model DAG | `dalgo_get_transform_graph` | — |
| Get node details | `dalgo_get_node_details` | `node_uuid` |
| Get node columns | `dalgo_get_node_columns` | `node_uuid` |
| Lock the canvas | `dalgo_acquire_canvas_lock` | — (required before edits) |
| Release the lock | `dalgo_release_canvas_lock` | — (always, even on failure) |
| Add source/model to canvas | `dalgo_add_source_to_canvas` | source/model identifier |
| Create an operation | `dalgo_create_operation` | join, filter, rename, aggregate, cast, … |
| Edit an operation | `dalgo_edit_operation` | node id, config |
| Materialize a chain | `dalgo_terminate_chain` | output model name |
| Warehouse data types | `dalgo_get_data_types` | — (for cast ops) |
| Run dbt | `dalgo_run_dbt` | `run_params: {}` or `{"select": "model"}` |
| Sync dbt source defs | `dalgo_sync_sources` | — |
| dbt workspace config | `dalgo_get_dbt_workspace` | — |
| Git status of dbt project | `dalgo_get_git_status` | — |
| Commit & push changes | `dalgo_publish_changes` | commit message (confirm first) |

## Verifying a dbt run

1. Trigger, then wait 30–60s (2–3 min for large projects).
2. `dalgo_get_sources_models` — are the expected models present and current?
3. `dalgo_get_git_status` — any unexpected modified files?
4. Undeterminable → tell the user to check Transform > Run History in the Dalgo UI; offer to re-run specific models.

## dbt error translations

- **Compilation error** ("column Y does not exist"): the model references a column missing from the source data — the source structure likely changed.
- **Relation not found** ("relation schema.table does not exist"): the upstream table is missing — the source sync may not have run; check `dalgo-ingestion`.
- **Dependency failure** ("model X depends on Y which failed"): fix Y first, then re-run X.
- **Permission denied**: warehouse user lacks rights — a configuration issue for the Dalgo administrator.
- **Timeout**: the query was cancelled for running too long — large data; the model may need optimization.

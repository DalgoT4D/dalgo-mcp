---
name: dalgo-transforms
description: Build and run dbt transformations in Dalgo — the transform canvas, operations, model materialization, dbt runs, and publishing to git. Use when a user asks to run dbt, build or edit models, or modify the transform canvas.
---

# dalgo-transforms

Use for dbt and transform-canvas workflows through Dalgo MCP tools.

## Always

- Canvas edits require the lock protocol: `dalgo_acquire_canvas_lock` before any modification, `dalgo_release_canvas_lock` after — release even if a step fails, or other users stay locked out.
- `dalgo_run_dbt` is fire-and-forget (queued via Celery): a 200 response means queued, not succeeded. Wait 30–60 seconds (longer for big projects) before checking outcomes; never report success from the trigger response.
- `dalgo_sync_sources` updates the dbt project's source definitions from the warehouse — it does NOT sync raw data from external sources. For that, route to `dalgo-ingestion`.
- Confirm with the user before `dalgo_publish_changes` (commits and pushes to git) and check `dalgo_get_git_status` first so you can say what will be committed.
- Translate dbt errors into plain language for non-technical users and end every failure report with a concrete next step.

## Decision Rules

- "Run all transforms": `dalgo_run_dbt` with empty `run_params`. Specific model: `{"select": "model_name"}`; model plus downstream: `{"select": "model_name+"}`.
- Re-running after failures: select only the failed models, not the whole project.
- "What models do we have?": `dalgo_get_transform_graph` and describe output models in plain English, not node IDs.
- Models failing on missing source tables: `dalgo_sync_sources` first, then re-run; if raw data itself is missing, route to `dalgo-ingestion`.
- Building a new model: lock → `dalgo_add_source_to_canvas` → `dalgo_create_operation` chain → `dalgo_terminate_chain` to materialize → unlock. Use `dalgo_get_data_types` for cast operations.

## Workflow Order

1. Inspect first: `dalgo_get_transform_graph`, `dalgo_get_node_details` / `dalgo_get_node_columns` for specifics.
2. For canvas edits: acquire lock → modify → terminate chain → release lock.
3. For runs: `dalgo_run_dbt` → wait → verify via `dalgo_get_sources_models` and `dalgo_get_git_status`.
4. If outcome is undeterminable from tools, say so and point to Transform > Run History in the Dalgo UI.

## Retrieve

- Tool table, run verification, and dbt error translations: [references/transform-workflows.md](references/transform-workflows.md)

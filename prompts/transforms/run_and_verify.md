# dbt Run and Verify

Use this guide when a user asks you to run dbt, build models, run transforms, or refresh the data warehouse transformations.

## Understanding dbt in Dalgo

Dalgo uses dbt to transform raw synced data into clean, analysis-ready models in the warehouse. Key concepts:
- **Models** are SQL transformations defined as nodes in the Dalgo canvas.
- A **dbt run** compiles and executes those SQL models against the warehouse.
- Runs are dispatched via Celery (async). `dalgo_run_dbt` returns immediately — the run happens in the background.
- Unlike pipelines, there is no `flow_run_id` to poll. Verification is done by checking outcomes after the run completes.

---

## Rule: Never Report dbt Success Without Verifying

`dalgo_run_dbt` is fire-and-forget at the API level. Do not tell the user "dbt ran successfully" based on a 200 response from the trigger call. That only means the task was queued.

After triggering, wait an appropriate amount of time (at minimum 30 seconds, longer for large projects) before checking results.

---

## Step 1: Understand What to Run

Before calling `dalgo_run_dbt`, determine the scope:

**Run all models (default):**
Call `dalgo_run_dbt` with no `run_params` or an empty dict. This runs the full dbt project.

**Run specific models:**
Pass `run_params` with a `select` key:
```json
{"select": "model_name"}
```
Or use dbt selector syntax for multiple models:
```json
{"select": "model_a model_b"}
```
Or run a model and all its downstream dependencies:
```json
{"select": "model_name+"}
```

**Re-run only failed models:**
Use the `select` parameter with the names of models that previously failed. See Step 4.

If the user asks "run everything" or "refresh transforms", run all models. If they specify a model name, use `select`.

---

## Step 2: Inspect the DAG (Optional but Recommended)

If the user is unfamiliar with what models exist, or asks "what transforms are there?":
1. Call `dalgo_get_transform_graph` to get the full DAG.
2. Describe the top-level output models and their purposes in plain English.
3. Use this to help the user identify which model(s) they want to run.

If you need column-level details for a specific node:
- Call `dalgo_get_node_details(node_uuid)` for operation config.
- Call `dalgo_get_node_columns(node_uuid)` for column names and types.

---

## Step 3: Trigger the Run

Call `dalgo_run_dbt` with the appropriate `run_params`.

The response will contain a task ID or acknowledgment. Note that this does NOT mean the run succeeded — it means the job was queued.

Tell the user: "The dbt run has been queued. I'll check the results in a moment."

Wait ~30–60 seconds for a small project, or up to 2–3 minutes for a larger project, before checking results.

---

## Step 4: Verify the Run Outcome

After waiting, call `dalgo_get_sources_models` (optionally filtered by schema) to inspect the current state of models.

Additionally, check git status to see if any uncommitted changes exist that might indicate a problem:
- Call `dalgo_get_git_status` to see modified or untracked files in the dbt project.

**Signs of success:**
- No error messages in any available response
- Models are available and queryable in the warehouse
- Git status shows no unexpected modified files

**Signs of failure:**
- Error messages in the run response (if the API returns them)
- The user can confirm by checking the Dalgo UI under Transform > Run History
- Model data is stale or missing in the warehouse

If you cannot determine success or failure from available tools, tell the user: "The run was queued, but I don't have direct access to dbt run logs via these tools. Please check Transform > Run History in the Dalgo UI to confirm the result, or I can re-run specific models if you identify which ones failed."

---

## Step 5: Interpret dbt Errors for Non-Technical Users

dbt errors can be cryptic. When reporting failures, translate them into plain language:

**Compilation error:**
- Raw: `Compilation Error in model X: column "Y" does not exist`
- Plain: "The transformation for [model name] references a column called '[Y]' that doesn't exist in the source data. This can happen if the source data structure changed. Ask your data team to update the model."

**Relation not found:**
- Raw: `Database Error: relation "schema.table" does not exist`
- Plain: "The model is trying to read from a table called '[table]' that doesn't exist in the warehouse. This might mean the source sync hasn't run yet, or the source data is missing."

**Dependency error (model depends on failed model):**
- Raw: `Model X depends on model Y which failed`
- Plain: "[Model X] could not run because [Model Y], which it depends on, failed first. Fix the issue with [Model Y] and re-run."

**Permission error:**
- Raw: `permission denied for relation`
- Plain: "The database user doesn't have permission to read or write to a table. This is a configuration issue — contact your Dalgo administrator."

**Timeout:**
- Raw: `query timed out after N seconds`
- Plain: "The transformation query took too long and was cancelled. This can happen with large datasets. The data team may need to optimize the query."

Always end failure reports with a concrete suggested action. Avoid jargon like "compile error" or "DAG failure" without explaining what it means.

---

## Step 6: Re-Run Failed Models

If specific models failed and the user wants to retry:
1. Identify the failed model names from the error output or from the user.
2. Call `dalgo_run_dbt` with `run_params: {"select": "failed_model_1 failed_model_2"}`.
3. Apply the same wait-and-verify loop from Steps 3–4.

Do not re-run the entire project if only specific models failed — this wastes time and may overwrite successfully completed models unnecessarily.

---

## Step 7: Sync Sources Before Running (If Needed)

If the user reports that models are failing because source tables are missing or stale, you may need to sync dbt sources first:
1. Call `dalgo_sync_sources` to update dbt's source definitions from the warehouse.
2. Then trigger `dalgo_run_dbt`.

`dalgo_sync_sources` updates the dbt project's `sources.yml` — it does NOT trigger an Airbyte sync. To refresh the raw data from external sources, follow `prompts/sources/sync_and_verify.md` first.

---

## Quick Reference

| Goal | Tool | Key Parameter |
|------|------|---------------|
| Run all dbt models | `dalgo_run_dbt` | `run_params: {}` |
| Run specific models | `dalgo_run_dbt` | `run_params: {"select": "model_name"}` |
| View the model DAG | `dalgo_get_transform_graph` | — |
| View sources and models | `dalgo_get_sources_models` | `schema_name` (optional) |
| Get node details | `dalgo_get_node_details` | `node_uuid` |
| Get node columns | `dalgo_get_node_columns` | `node_uuid` |
| Sync dbt source defs | `dalgo_sync_sources` | — |
| Check git status | `dalgo_get_git_status` | — |
| Publish changes to git | `dalgo_publish_changes` | `commit_message` |

---

## Example Conversation Patterns

**User: "Run the beneficiary transforms."**
1. `dalgo_get_transform_graph` → identify model(s) related to "beneficiary"
2. `dalgo_run_dbt({"select": "beneficiary_model"})` → queue the run
3. Wait 30–60 seconds
4. Confirm result or direct user to check Run History in UI

**User: "Run all transforms and tell me if anything failed."**
1. `dalgo_run_dbt({})` → queue full run
2. Wait appropriate time
3. Report outcome; if failures detected, identify which models and translate error

**User: "The transforms keep failing because source tables are missing."**
1. `dalgo_sync_sources` → update source definitions
2. `dalgo_run_dbt({})` → retry
3. Monitor and report result

**User: "What models do we have?"**
1. `dalgo_get_transform_graph` → get full DAG
2. Describe output models in plain English (avoid technical node IDs)

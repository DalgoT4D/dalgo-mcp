---
name: dalgo-pipelines
description: Run, monitor, create, and manage Dalgo orchestration pipelines (Prefect deployments), including the trigger-poll-verify loop. Use whenever a user asks to run a pipeline or check whether one succeeded.
---

# dalgo-pipelines

Use for pipeline workflows through Dalgo MCP tools.

## Always

- Never stop at "triggered". `dalgo_trigger_pipeline_run` only schedules a run — poll `dalgo_get_flow_run` to a terminal status before reporting the outcome.
- Resolve pipeline names to `deployment_id` via `dalgo_list_pipelines` before any detail or mutation call.
- On `FAILED`, `CRASHED`, or `CANCELLED`, fetch `dalgo_get_flow_run_logs` and quote the actual error before suggesting fixes.
- Confirm with the user before `dalgo_delete_pipeline`; it is irreversible.
- If the user says "just trigger it, don't wait", trigger without polling but state explicitly that completion was not verified.

## Decision Rules

- "Run pipeline X and make sure it worked": full trigger → poll → verify loop.
- "Did the last run succeed?": `dalgo_get_pipeline_run_history` with `limit=1` — do not trigger a new run.
- "Why did it fail?": route to `dalgo-troubleshooting`.
- Terminal statuses: `COMPLETED`, `FAILED`, `CRASHED`, `CANCELLED`. Non-terminal: `SCHEDULED`, `PENDING`, `RUNNING`.
- Poll every ~15 seconds, at most 20 times (~5 minutes); past that, report the run is still going and give the `flow_run_id` for a later check.

## Workflow Order

1. `dalgo_list_pipelines` → match by name → `deployment_id`.
2. `dalgo_trigger_pipeline_run(deployment_id)` → save `flow_run_id`; if the trigger errors, report and stop.
3. Poll `dalgo_get_flow_run(flow_run_id)` until terminal or poll limit.
4. `COMPLETED`: report success with timing. Failure: fetch logs, show the last ~30 lines, explain the error and a next step.

## Retrieve

- Tool table, status reference, and failure triage: [references/pipeline-workflows.md](references/pipeline-workflows.md)

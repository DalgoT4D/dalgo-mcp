# Pipeline Workflows

| Goal | Tool | Key parameter |
|---|---|---|
| List all pipelines | `dalgo_list_pipelines` | — |
| Get pipeline details | `dalgo_get_pipeline` | `deployment_id` |
| Create a pipeline | `dalgo_create_pipeline` | name, connections, schedule |
| Update a pipeline | `dalgo_update_pipeline` | `deployment_id` |
| Delete a pipeline | `dalgo_delete_pipeline` | `deployment_id` |
| Trigger a run | `dalgo_trigger_pipeline_run` | `deployment_id` → returns `flow_run_id` |
| Check run status | `dalgo_get_flow_run` | `flow_run_id` |
| Fetch run logs | `dalgo_get_flow_run_logs` | `flow_run_id` |
| View run history | `dalgo_get_pipeline_run_history` | `deployment_id`, `limit` |

## Failure triage by error pattern

- Authentication errors in logs → source credentials likely expired; update them under Data > Sources in the Dalgo UI.
- Timeouts → data volume too large or source slow; suggest off-peak scheduling.
- Connection/network errors → source system unreachable; check it is online.
- Schema errors → source structure changed; refresh the connection catalog, then re-run.
- dbt step failures → route to `dalgo-transforms` for model-level diagnosis.

## Example

User: "Run the beneficiary sync pipeline and make sure it worked."

1. `dalgo_list_pipelines` → deployment_id for "beneficiary sync"
2. `dalgo_trigger_pipeline_run(deployment_id)` → flow_run_id
3. Poll `dalgo_get_flow_run(flow_run_id)` every ~15s to a terminal status
4. `COMPLETED` → "The beneficiary sync pipeline completed successfully." `FAILED` → fetch logs, quote the error, suggest a fix.

Wrong: calling the trigger tool and reporting "Successfully triggered!" without polling.

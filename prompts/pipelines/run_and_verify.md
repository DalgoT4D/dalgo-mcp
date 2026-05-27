# Pipeline Run and Verify

Use this guide whenever a user asks you to run, trigger, execute, or start a pipeline — and especially when they ask you to confirm it succeeded, completed, or finished.

## Rule: Never Stop at "Triggered"

Calling `dalgo_trigger_pipeline_run` only schedules the run. It does not mean the pipeline succeeded. You MUST follow the full verification loop below unless the user explicitly says "just trigger it, don't wait."

If the user says "just trigger" without asking for verification, still acknowledge: "I've triggered the pipeline but have not verified completion. Ask me to check if you'd like to confirm the result."

---

## Step 1: Resolve the Pipeline

If you have the pipeline name but not the deployment ID:
1. Call `dalgo_list_pipelines` to get all pipelines.
2. Match by name (case-insensitive). If multiple match, ask the user to clarify.
3. Extract the `deployment_id` from the matched pipeline.

If you already have the `deployment_id`, skip to Step 2.

---

## Step 2: Trigger the Run

Call `dalgo_trigger_pipeline_run` with the `deployment_id`.

The response will contain a `flow_run_id`. Save this — you will need it for polling.

If the trigger call fails (HTTP error, no `flow_run_id` in response), report the error immediately and stop. Do not attempt to verify a run that was never started.

---

## Step 3: Poll for Completion

Call `dalgo_get_flow_run` with the `flow_run_id` every ~15 seconds.

**Terminal statuses** (stop polling when you see these):
- `COMPLETED` — success
- `FAILED` — the run failed
- `CRASHED` — the run crashed (infrastructure error)
- `CANCELLED` — the run was cancelled

**Non-terminal statuses** (keep polling):
- `SCHEDULED` — waiting to start
- `RUNNING` — actively executing
- `PENDING` — about to start

**Poll limit:** Never poll more than 20 times (approximately 5 minutes). If you reach the limit without a terminal status, report: "The pipeline is still running after 5 minutes. You can check its status later by asking me to check flow run [flow_run_id]."

Between polls, inform the user that you are waiting: "Pipeline is [status], checking again in ~15 seconds..."

---

## Step 4: Handle Success

If status is `COMPLETED`:
- Report clearly: "The pipeline completed successfully."
- Include any summary fields from the response (e.g., start time, end time, duration if available).
- Do not fetch logs for successful runs unless the user asks.

---

## Step 5: Handle Failure

If status is `FAILED`, `CRASHED`, or `CANCELLED`:

1. Call `dalgo_get_flow_run_logs` with the `flow_run_id`.
2. From the logs response, extract and show the **last 30 lines** (or all logs if fewer than 30 lines).
3. Report failure clearly: "The pipeline failed with status [STATUS]."
4. Quote the relevant error from the logs. Look for lines containing `ERROR`, `Exception`, `Traceback`, `failed`, or similar markers.
5. Suggest a next step based on the error if you can identify it:
   - Authentication errors: suggest checking source credentials
   - Timeout errors: suggest the data volume may be too large or the source is slow
   - Connection errors: suggest checking network/firewall settings
   - Schema errors: suggest re-running after a schema sync

---

## Optional: Check Recent History First

If the user asks "did the last pipeline run succeed?" or "what happened with the last run?" without asking to trigger a new one:
1. Call `dalgo_get_pipeline_run_history` with the `deployment_id` and `limit=1`.
2. Report the status and time of the most recent run.
3. If the last run failed, offer to fetch logs for that run's `flow_run_id`.

---

## Quick Reference

| Goal | Tool | Key Parameter |
|------|------|---------------|
| List all pipelines | `dalgo_list_pipelines` | — |
| Get pipeline details | `dalgo_get_pipeline` | `deployment_id` |
| Trigger a run | `dalgo_trigger_pipeline_run` | `deployment_id` |
| Check run status | `dalgo_get_flow_run` | `flow_run_id` |
| Fetch run logs | `dalgo_get_flow_run_logs` | `flow_run_id` |
| View run history | `dalgo_get_pipeline_run_history` | `deployment_id`, `limit` |

---

## Example Conversation Pattern

User: "Run the beneficiary sync pipeline and make sure it worked."

Correct model behavior:
1. Call `dalgo_list_pipelines` → find deployment_id for "beneficiary sync"
2. Call `dalgo_trigger_pipeline_run(deployment_id)` → get flow_run_id
3. Say: "Triggered. Waiting for completion..."
4. Poll `dalgo_get_flow_run(flow_run_id)` until terminal status
5. If `COMPLETED`: "The beneficiary sync pipeline completed successfully."
6. If `FAILED`: Call `dalgo_get_flow_run_logs`, show last 30 lines, explain the error.

Wrong model behavior: Call `dalgo_trigger_pipeline_run` and say "Successfully triggered the pipeline!" without polling.

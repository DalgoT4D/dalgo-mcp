# Automode: Per-Agent Design and the Harness Each One Needs

Companion to `automode-plan.md`. Read that first for the big picture (the MCP is the "hands";
the harness is the "brain, calendar, memory, and safety rails").

This doc answers three questions:
1. Do we build **different agents**, or **one agent** that figures out its own tools?
2. For each of the four jobs, what **prompt, skills, tools, and loop** does it need?
3. How does each agent **test its own work**, and how do **we test the agent**?

Terms defined once:
- **Tool scope:** the limited set of MCP tools we allow one agent to use (out of all 63).
- **Skill / playbook:** a short written guide the agent reads to do a task well (e.g. "how to fix an
  expired-credentials error"). In the Claude Agent SDK these are loaded on demand.
- **Self-verify:** the agent checking its own work before saying "done".
- **Eval:** our test set that scores whether the agent is actually good, before we trust it.

---

## 1. One agent or many? The answer: one harness, many profiles

This is the key decision, so let's be precise.

**Not one do-everything agent.** Giving a single agent all 63 tools and saying "figure it out" fails
for three reasons:
- **Too many tools hurts accuracy.** With 63 choices, the agent picks the wrong tool more often. A
  focused set of ~8 tools picks right.
- **No safety boundary.** A generalist *can* delete anything. We can't certify "this agent is safe"
  if it can do everything.
- **Different rhythms.** Self-healing reacts to an event at 2am. The analyst runs on a Monday
  schedule. Analytics waits for a person to ask. One loop can't fit all three.

**Not many separate programs either.** Building the loop, the MCP connection, the safety rail, the
audit log, and the memory store four times over is wasteful and inconsistent.

**The answer: build the harness once. Define each agent as a thin "profile" on top.**

**The rule:** One shared harness engine. Each agent is just a configuration: a prompt + a tool scope
+ a few skills + a trigger + a guardrail policy + an eval set.
**Example:** The "self-healing" agent and the "analyst" agent run on the *same* engine. They differ
only in their prompt, the 8-ish tools each is allowed, the playbooks they read, and when they wake up.
**Why it matters:** We build the hard part (loop, safety, audit, memory) once. Adding a fifth agent
later is writing a prompt and a few playbooks — not a new system.

```
                 ┌──────────────────────────────────────────────┐
                 │            SHARED HARNESS ENGINE               │
                 │  loop · MCP connection · wait-for-run ·        │
                 │  safety rail (kavach) · audit log · memory     │
                 └───────────────────────┬──────────────────────┘
                                         │ each profile = prompt + tools + skills + trigger
      ┌──────────────┬──────────────────┼──────────────────┬──────────────────┐
      ▼              ▼                   ▼                  ▼
 ┌─────────┐   ┌──────────┐       ┌────────────┐    ┌──────────────┐
 │ Healing │   │ Analytics│       │  Analyst   │    │   Builder    │
 │ profile │   │ profile  │       │  profile   │    │   profile    │
 └─────────┘   └──────────┘       └────────────┘    └──────────────┘
   event          on ask              cron           guided + gates
```

**So: different agents, yes — but one harness with different profiles around it, not one agent
guessing its way through all 63 tools.** Each profile knows its own small tool set, so it doesn't
have to "figure out" the whole platform every time.

---

## 2. The shared agent loop (used by every profile)

Every profile runs this same loop. Only the prompt, tools, and skills change.

```
  trigger fires (event / schedule / user ask)
        │
        ▼
  load profile: system prompt + tool scope + skills + memory for this org
        │
        ▼
  ┌────────────────── agent loop ──────────────────┐
  │  Claude thinks → picks an MCP tool → harness    │
  │  checks SAFETY RAIL → tool runs → result back   │
  │  (repeat until the goal is met or it gives up)  │
  └─────────────────────────────────────────────────┘
        │
        ▼
  SELF-VERIFY: did the goal actually happen? (re-read state)
        │
        ▼
  write AUDIT log + update MEMORY + notify human if needed
```

The **safety rail** step is where a write/delete is previewed, sent for approval, or blocked. The
**self-verify** step is the agent proving its own work. Both are built once, in the harness.

---

## 3. The four agents, side by side

This table is the quick reference. Details for each follow.

| Agent | Wakes up when | Tool scope (sample) | Risk level | Most-needed harness piece |
|---|---|---|---|---|
| **Self-healing** | A pipeline fails (event) | logs, run history, trigger, sync, run_dbt | Medium (retries safe; edits gated) | Wait-for-run + Memory |
| **NL → analytics** | A person asks (interactive) | schema, columns, sample data, create_chart, create_dashboard | Low (read + charts) | Grounding (data dictionary) |
| **Autonomous analyst** | A schedule (cron, e.g. weekly) | table data, row counts, create_report, create_dashboard | Low (creates reports) | Memory (baselines) |
| **Pipeline builder** | A person starts onboarding (guided) | source defs, canvas, create_pipeline, create_dashboard | **High (write-heavy, credentials)** | Safety rail + approval gates |

---

## 4. Agent A — Self-healing pipelines

**The job:** A sync or pipeline fails overnight. The agent finds the cause, fixes it safely or
retries, confirms it's green, and if it can't fix it, writes a plain-language note for the team.

**Trigger:** Event-driven. Dalgo already sends a webhook/notification when a Prefect flow run fails.
We start the agent from that. (Plus a periodic sweep as a backstop.)

**The loop:**
```
failure event → get_flow_run_logs → classify the failure (use a skill)
   → choose safest fix → act → trigger_pipeline_run → wait → green?
        ├─ yes → log it, remember the fix, done
        └─ no, after N tries → write plain-language remediation, notify human
```

**Tool scope:** `get_pipeline`, `get_pipeline_run_history`, `get_flow_run`, `get_flow_run_logs`,
`trigger_pipeline_run`, `sync_sources`, `run_dbt`, `get_git_status`, `get_connection_catalog`,
`list_notifications`, `mark_notifications_read`. (Read + re-run. Config/dbt edits are gated.)

**The prompt (draft):**
> "You are a pipeline reliability agent for a small NGO with no data engineer. A pipeline has failed.
> Read the logs, identify the root cause, and apply the *safest* fix that addresses it. A plain retry
> is safe. Editing config or dbt code needs human approval. Never delete anything. After acting,
> re-trigger and confirm the run is green. If you cannot fix it safely in 3 attempts, stop and write a
> short remediation in plain English a non-technical person can follow."

**Skills (playbooks it reads):** one per failure type, e.g.
- `expired-credentials.md` — symptoms in logs + the safe remedy (refresh/flag, never guess secrets).
- `schema-drift.md` — a source added/renamed a column; how to detect and the safe response.
- `dbt-compile-error.md` — read the compile error, locate the model, propose the fix (gated).
- `source-timeout.md` — when a plain retry is the right call.

**What it needs from the harness (beyond MCP):**
- **Wait-for-run:** a re-trigger takes minutes; the harness waits for the terminal state instead of
  the agent burning turns polling.
- **Memory:** "Source X failed with an expired token last Tuesday; the fix was Y." Try that first.
- **Safety rail:** retry = auto; config/dbt edit = human approval; delete = never.
- **Audit log:** every action recorded and reversible.

**How it self-verifies:** re-trigger the pipeline and confirm the flow run ends in `success`, and the
target tables refreshed (row count moved / updated_at is recent).

**How WE test it (evals):** a library of real, anonymized failure logs with the known root cause and
correct action. Score three things: did it diagnose correctly, did it pick the right action, and did
it *avoid* an unsafe action. Example: 30 logged failures → target 90%+ correct diagnosis, 0 unsafe
deletes.

---

## 5. Agent B — NL → analytics

**The job:** A program manager asks "show me dropout trends by district." The agent explores the
data, writes the query, builds the chart and a dashboard — correctly.

**Trigger:** Interactive (a person asks, in chat or the app).

**The loop:**
```
question → look up meanings in the data dictionary (grounding)
   → find the right tables/columns → write SQL (or a dbt model)
   → validate on a small sample → create_chart → check the chart isn't empty/wrong
   → assemble dashboard → present, with a one-line "here's what I assumed"
```

**Tool scope:** `list_schemas`, `list_tables`, `get_table_columns`, `get_node_columns`,
`get_table_data` (small sample), `describe_table_semantics` (NEW — see §8), `create_chart`,
`get_chart_data`, `render_chart`, `create_dashboard`, `run_dbt`, `get_transform_graph`.

**The prompt (draft):**
> "You are a data analyst for an NGO. Turn the user's plain-language question into a correct chart or
> dashboard. Before writing any SQL, look up what the columns and metrics mean in the data dictionary —
> do not guess. Always run your query on a small sample first and sanity-check the numbers. If the
> question is ambiguous (e.g. 'recent' or 'dropout' is undefined), ask exactly one clarifying question
> before proceeding. When you present, state the assumptions you made in one line."

**Skills:**
- `chart-type-selection.md` — trend over time → line; share of total → bar; etc.
- `metric-definitions.md` — how to read and extend the data dictionary.
- `sql-safety.md` — always `LIMIT` during exploration; avoid full table scans.
- `ask-one-question.md` — when and how to ask a single clarifying question instead of guessing.

**What it needs from the harness:**
- **Grounding (most important):** the per-org data dictionary, or the agent guesses what `dist_cd`
  means and produces a confident-but-wrong chart.
- **Memory (light):** remember metric definitions the user confirmed last time.
- **Safety (light):** reading and making charts is low risk. Creating a *dbt model* uses the canvas
  lock and may need approval.

**How it self-verifies:** run the query, confirm rows > 0 and totals are plausible (e.g. the parts
sum to a known whole). A second quick "critic" pass: *"does this chart actually answer the question
asked?"*

**How WE test it (evals):** a fixture warehouse with a set of plain-language questions that have
known-correct answers. Score: is the number right, and is the chart type appropriate. An LLM judge
can grade chart appropriateness against a rubric.

---

## 6. Agent C — Autonomous analyst

**The job:** Nobody watches the data between report cycles. Each week the agent inspects key metrics,
finds what genuinely changed, and writes a short narrative report.

**Trigger:** Schedule (cron, e.g. every Monday 7am).

**The loop:**
```
schedule fires → read this week's key metrics → compare to last week's (memory)
   → flag only genuinely notable changes (use anomaly skill)
   → write a short narrative → create_report / create_dashboard → notify
```

**Tool scope:** `list_tables`, `get_table_data`, `get_table_row_count`, `get_chart_data`,
`create_report`, `create_dashboard`, `create_chart`, `list_notifications`, `search_docs`.

**The prompt (draft):**
> "You are a recurring data analyst for an NGO. Each week, inspect the organization's key metrics and
> compare them to previous weeks. Report only *genuinely notable* changes — do not cry wolf over
> normal noise. Write a short narrative a program manager can act on: what changed, why it might
> matter, and what to check. Always cite the actual numbers."

**Skills:**
- `anomaly-rules.md` — simple, explainable rules: % change over a threshold, a metric hitting zero,
  a sudden spike in null values.
- `narrative-report.md` — the report structure: headline → what changed → likely meaning → suggested
  check.
- `metric-watchlist.md` — which metrics matter for this org (configurable per org).

**What it needs from the harness:**
- **Memory (most important):** last week's numbers, and what it already reported, so it can compute
  "change vs. last week" and not repeat the same alert.
- **Grounding:** what each metric means, so the narrative is correct.
- **Schedule trigger.** Low safety risk (it creates reports; it doesn't delete).

**How it self-verifies:** recompute each flagged anomaly to confirm it's real; check it hasn't already
reported the same thing (dedupe against memory).

**How WE test it (evals):** time-series fixtures with anomalies we injected on purpose. Score how many
real anomalies it caught (recall), how many false alarms it raised (precision), and report quality via
an LLM judge against a rubric.

---

## 7. Agent D — Pipeline builder (onboarding)

**The job:** Onboarding a new source is the hardest manual climb. The agent sets up the whole path —
source → connection → dbt scaffolding → pipeline → starter dashboard — pausing for approval at the
risky steps.

**Trigger:** Guided. A person starts onboarding; the agent drives but **checks in at each gate.**

**The loop:**
```
"set up source X" → pick source definition → [GATE: enter credentials, human approves]
   → create connection → discover catalog → propose dbt staging models → [GATE: approve]
   → acquire canvas lock → build operations → create pipeline → [GATE: approve go-live]
   → trigger first sync → verify → build starter dashboard → release lock
```

**Tool scope (widest, most write-heavy):** `list_source_definitions`, `get_connection_catalog`,
`add_source_to_canvas`, `acquire_canvas_lock`, `create_operation`, `edit_operation`, `run_dbt`,
`publish_changes`, `release_canvas_lock`, `create_pipeline`, `trigger_pipeline_run`, `create_chart`,
`create_dashboard`.

**The prompt (draft):**
> "You are an onboarding agent. Given a new data source, set up the full path from ingestion to a
> starter dashboard. This is write-heavy and partly irreversible, so pause for human approval at every
> sensitive or irreversible step — especially entering credentials and going live. After each step,
> verify it worked before moving on. Never proceed past a gate without explicit approval."

**Skills:**
- `source-setup.md` — choosing the right connector and the safe credential flow.
- `dbt-scaffolding.md` — Dalgo's staging-model conventions.
- `pipeline-assembly.md` — combining sync + dbt into a schedule.
- `starter-dashboard.md` — a sensible first dashboard for a new source.

**What it needs from the harness:**
- **Safety rail (most important):** dry-run by default, an approval gate at each stage, canvas lock,
  full audit. This is the highest-risk agent.
- **Memory:** the org's naming and modeling conventions.

**How it self-verifies:** after each stage — source connects, catalog is non-empty, dbt compiles, the
first sync succeeds, the dashboard renders.

**How WE test it (evals):** scripted onboarding scenarios against a test backend. Score two things:
how far it gets on its own, and — just as important — did it **pause at the right gates** and never
skip an approval.

---

## 8. One concrete MCP gap this surfaced

The builder agent needs to **create** a source and a connection. The MCP today only has
`list_sources`, `get_source`, `delete_source`, and `list_source_definitions` — there is **no
`create_source` or `create_connection` tool.**

**The rule:** Agent D is blocked until the MCP exposes source/connection creation.
**Example:** The builder can list available connectors and read a catalog, but it cannot actually
create the Airbyte source with credentials — that step doesn't exist as a tool yet.
**Why it matters:** Agents A, B, and C can be built on today's MCP. Agent D needs two new MCP tools
first. That makes the build order natural: **A → B/C → (add MCP tools) → D.**

---

## 9. The bottom line for the team

- **We build one harness, not four programs and not one know-it-all agent.** Each agent is a thin
  profile (prompt + ~8 tools + a few playbooks + a trigger) on the shared engine.
- **An agent does not "figure out" all 63 tools.** We hand each profile a small, relevant tool set so
  it chooses correctly and stays inside a safe boundary.
- **Two kinds of testing, both needed:** the agent *self-verifies* every run (did the goal happen?),
  and *we* run *evals* (a scored test set) before trusting any agent unattended.
- **Build order:** self-healing first (works on today's MCP, obvious success test) → analytics and
  analyst (need grounding + memory) → add two MCP tools → builder last (highest risk, write-heavy).

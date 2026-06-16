# Dalgo "Automode": A Plain-Language Plan

**Goal:** build autonomous agents that do real data work in Dalgo on their own — fix broken
pipelines, answer data questions with charts, write reports — without a person clicking through
the app each time.

**Audience:** Dalgo teammates (engineers and non-engineers). No jargon assumed.

A few terms, defined once:
- **MCP (Model Context Protocol):** a standard way to give an AI assistant a set of "tools" it can
  call. Dalgo already has an MCP server with 63 tools.
- **Agent:** an AI (like Claude) that is given a goal and decides which tools to call, in what order,
  to reach that goal.
- **Agent harness:** the program we wrap around the AI so it can run by itself — on a schedule, with
  memory, with safety rails. The harness is the part we still need to build.

---

## 1. The big picture in one diagram

Think of it as a worker. The MCP gives the worker **hands and eyes**. The harness gives the worker
a **brain, a memory, a calendar, and safety rules**.

```
        WHAT WE BUILD (agent harness)              WHAT EXISTS TODAY (Dalgo MCP)
   ┌──────────────────────────────────┐        ┌──────────────────────────────┐
   │  Calendar  → run on schedule/event│        │   63 tools = the "hands":    │
   │  Brain     → Claude decides steps │  uses  │   read warehouse, run dbt,   │
   │  Memory    → remembers past runs  │ ─────▶ │   trigger pipelines, make    │
   │  Safety    → checks before writes │        │   charts, read logs, etc.    │
   │  Verify    → confirms it worked   │        └──────────────┬───────────────┘
   └──────────────────────────────────┘                       │ calls Dalgo's
                                                               ▼ normal REST API
                                                    ┌──────────────────────┐
                                                    │  Dalgo backend:      │
                                                    │  Airbyte, dbt,       │
                                                    │  Prefect, warehouse  │
                                                    └──────────────────────┘
```

**The one-line summary:** The MCP is the hands. We are building the brain, the calendar, the memory,
and the safety rails around it.

---

## 2. What is already possible from the MCP today

A lot. If you connect Claude (Desktop, Claude Code, or the API) to the Dalgo MCP **right now**, a
person can chat with it and get real work done. The MCP already does these things:

| The agent can already... | Example tools | What a person could ask today |
|---|---|---|
| Look at the data | `list_schemas`, `list_tables`, `get_table_data`, `get_table_row_count` | "How many rows are in the sessions table?" |
| Read pipeline health | `list_pipelines`, `get_pipeline_run_history`, `get_flow_run_logs` | "Did last night's pipeline run succeed?" |
| Run things | `trigger_pipeline_run`, `run_dbt`, `sync_sources` | "Re-run the dbt models." |
| Build visuals | `create_chart`, `create_dashboard`, `create_report` | "Make a bar chart of enrollments by month." |
| Read docs | `search_docs`, `get_doc` | "How do I add a new source?" |

It even has some safety built in already:
- **PII (Personally Identifiable Information) masking** on data reads — names, phone numbers, Aadhaar
  numbers get hidden automatically.
- **Canvas lock** — stops two editors changing the same dbt project at the same time.
- **Tool labels** — each tool is marked read-only, write, or destructive (delete).

**The rule:** The MCP can already *do* almost any single action in Dalgo.
**Example:** In a live chat, Claude + MCP can fetch a failed pipeline's logs and explain the error.
**Why it matters:** We do not need to build new tools to get started. The hands are ready.

---

## 3. What the MCP cannot do (this is why we need a harness)

The MCP is "request and reply." It waits for someone to ask, answers once, then forgets. An
autonomous agent needs five things the MCP does not provide.

**The rule:** The MCP does not run itself, remember, wait, judge, or stay safe over time.
**Example:** Ask the MCP "fix my pipeline" and it might pull logs and suggest a fix — but it won't
wake up at 2am when the pipeline actually breaks, it won't wait for the re-run to finish, and it
won't remember it fixed the same thing last week.
**Why it matters:** These five gaps are exactly the harness.

| Gap | What's missing | Plain example |
|---|---|---|
| **1. No calendar** | The MCP only acts when asked. | Nothing wakes the agent up when a sync fails at night. |
| **2. No "wait and watch"** | Tools reply instantly; a pipeline takes 10 minutes. | The agent has to keep re-asking "done yet?" — wasteful and clumsy. |
| **3. No memory** | Every chat starts blank. | The agent re-learns the same warehouse and re-discovers the same fix every time. |
| **4. No judgment about meaning** | Tables have codes, not meanings. | The agent sees `dist_cd` but doesn't know it means "district". So "dropout by district" is guesswork. |
| **5. No safety rules for changes** | Labels exist, but nothing *enforces* them. | A delete tool will just delete. Nobody asked "are you sure?" before the agent removes a dashboard. |

---

## 4. What we build: the agent harness, piece by piece

Each piece below is small and has one job. We do **not** build them all at once (see the phased plan
in §6). This is the menu; §6 is the order.

**A. The loop (the brain that runs by itself)**
- **The rule:** A small program gives Claude the goal, lets it call MCP tools, and keeps going until
  the goal is met.
- **Example:** Goal = "make last night's failed pipeline green again." The loop lets Claude read
  logs, decide on a fix, apply it, re-trigger, and check the result — on its own.
- **How:** We use the **Claude Agent SDK** (Anthropic's official toolkit for building agents). It
  already knows how to talk to MCP servers, so it plugs straight into the Dalgo MCP.

**B. The trigger (the calendar)**
- **The rule:** Something outside the MCP decides *when* the agent runs.
- **Example:** A nightly schedule for the report agent; a "pipeline failed" alert for the
  self-healing agent.
- **How:** Dalgo already runs scheduled background jobs (Celery + Prefect). We add a job that starts
  the agent loop. No new infrastructure.

**C. The verify step (confirm it worked)**
- **The rule:** After the agent acts, it must prove the goal is met before saying "done".
- **Example:** After a "fix", re-trigger the pipeline and confirm it finishes green. After a chart,
  read the chart data back and check it isn't empty.
- **How:** This is logic in our loop, using existing read tools like `get_pipeline_run_history`.

**D. The safety rail (guardrails on changes)**
- **The rule:** Before any write or delete, the harness checks a policy. Risky actions are previewed,
  need approval, or are blocked.
- **Example:** The agent wants to delete a dashboard. The rail pauses and sends a one-line approval
  request to a human on Slack first. Read-only actions never pause.
- **How:** This reuses your existing **mcp-kavach** work (the open-source guardrail layer for MCP).
  Kavach already masks PII on the way out; we extend the same idea to *write* actions on the way in,
  plus an audit log of everything the agent did.

**E. The grounding (teaching the agent what the data means)**
- **The rule:** Give the agent a per-organization "data dictionary" so it stops guessing.
- **Example:** A small note that says `dist_cd` = district code, and "active student" = a student
  with a session in the last 30 days. Now "dropout by district" is exact, not a guess.
- **How:** A new MCP tool (e.g. `describe_table_semantics`) plus a stored dictionary the agent can
  read and add to over time. Needed for the analytics and report agents, not for self-healing.

**F. The memory (learn across runs)**
- **The rule:** The agent saves what it learned so the next run starts smarter.
- **Example:** "Last Tuesday, source X failed with an expired token; the fix was to refresh
  credentials." Next time, the agent tries that first.
- **How:** A simple per-org store the loop writes to and reads from.

**G. The evals (proof it does the job well)**
- **The rule:** A test set of real-ish tasks with a scorecard, so we know an agent is good *before*
  we let it run unattended.
- **Example:** 20 known broken pipelines. Score: how many did the agent correctly diagnose and fix?
- **Why it matters:** Without this, "the agent works" is just a hope. With it, we can certify each
  agent and catch regressions.

---

## 5. Possible from MCP vs. needs the harness — the cheat sheet

This is the table to send teammates who just want the bottom line.

| Capability | From MCP today? | Needs harness? |
|---|---|---|
| Read data, logs, pipeline status | ✅ Yes | — |
| Trigger a run / dbt / sync | ✅ Yes | — |
| Create a chart / dashboard / report | ✅ Yes | — |
| Mask PII on reads | ✅ Yes (built in) | — |
| Run automatically on a schedule or on failure | ❌ No | ✅ Trigger (B) |
| Wait for a 10-minute run to finish, then react | ❌ No | ✅ Loop + verify (A, C) |
| Remember past runs and fixes | ❌ No | ✅ Memory (F) |
| Know what columns and metrics *mean* | ❌ No | ✅ Grounding (E) |
| Ask permission before deleting / risky writes | ⚠️ Labels only | ✅ Safety rail (D) |
| Prove the agent is good before trusting it | ❌ No | ✅ Evals (G) |

---

## 6. The plan, in phases

Build the smallest useful thing first, learn from it, then widen. Each phase ends with something we
can show.

**Phase 0 — Prove it by hand (days, no building)**
- Connect Claude Code to the Dalgo MCP and do one task manually in a chat: "diagnose this failed
  pipeline."
- Goal: see exactly where Claude struggles (what it can't see, where it guesses). This list becomes
  our real to-do, grounded in evidence, not theory.

**Phase 1 — One agent, end to end (the self-healing pipeline agent)**
- Build the **loop (A)**, **trigger (B)**, and **verify (C)** for one narrow job: watch pipelines,
  on failure diagnose and retry/fix, confirm green.
- Why this one first: it reuses Dalgo's existing log-summarization and Prefect scheduling, the
  success test is obvious (did it go green?), and it solves a real pain — NGOs with no data engineer
  waking up to broken data.

**Phase 2 — Make it safe to leave alone (the kavach tie-in)**
- Add the **safety rail (D)**: dry-run by default, human approval for destructive actions, and a full
  **audit log** of what the agent did.
- This is the gate that lets an organization actually trust the agent unattended. It also pushes your
  open-source kavach work forward.

**Phase 3 — Add understanding (grounding) and a second agent**
- Build the **grounding (E)** and **memory (F)** pieces.
- Add the **NL-to-analytics agent**: "show dropout trends by district" → it explores, writes SQL/dbt,
  builds the chart and dashboard. This is the most impressive demo and needs grounding to be reliable.

**Phase 4 — Certify and widen (evals)**
- Build the **eval harness (G)** with scored test tasks for each agent.
- Only after an agent passes do we turn it on for real organizations.
- Add further agents (scheduled analyst, onboarding/pipeline builder) on the same foundation.

---

## 7. The single most important idea

The exciting, "doesn't exist yet" value is **not more tools**. The MCP tools are already strong.

The value is the **harness — especially the safety rail (D) and the evals (G).** Those two turn a
cool one-time demo into an agent an NGO can trust to run on its own. And the safety rail is a direct
extension of the open-source kavach work, so it fits what we already believe in: NGOs keep control of
their data, with everything open source.

**Build order in one line:** prove by hand → one self-healing agent → make it safe → teach it meaning
→ prove it's good → widen.

# MCP Apps in Dalgo MCP

[MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview) (SEP-1865,
ratified 2026-01-26) is the first official MCP extension. It lets a server return
**interactive HTML views** that render inside the host (Claude, Claude Desktop,
VS Code Copilot, and others) instead of plain text. The view runs in a sandboxed
iframe and talks back to the host over a `postMessage` JSON-RPC dialect, so it can
call our tools for fresh data.

This is a strong fit for Dalgo MCP because most of our value is visual — charts,
dashboards, dbt lineage, pipeline status — and today every result is a markdown
table or JSON blob.

## What ships in this PR (proof of concept)

A **chart-rendering App**:

- `ui://dalgo/chart` — a self-contained, dependency-free HTML view
  (`src/dalgo_mcp/apps/chart_view.html`) that implements the `ui/initialize`
  handshake, listens for `ui/notifications/tool-result`, and renders bar / line /
  pie / big-number charts as inline SVG.
- `dalgo_render_chart(chart_id)` — a tool annotated with
  `_meta.ui.resourceUri = ui://dalgo/chart`. It fetches the chart's config and
  executed data, masks PII, and returns them as `structuredContent` for the view.

### Contract used (spec 2026-01-26)

| Piece | Value |
|-------|-------|
| UI resource MIME type | `text/html;profile=mcp-app` |
| Tool → UI link | `_meta.ui.resourceUri` |
| Resource metadata | `_meta.ui` (`csp`, `permissions`, `prefersBorder`) |
| Data to iframe | host pushes `ui/notifications/tool-result` (a `CallToolResult` with `structuredContent`) |
| Handshake | iframe sends `ui/initialize`, then `ui/notifications/initialized` |
| Callbacks | iframe may `tools/call` over `postMessage` |

FastMCP ≥ 1.27 exposes a `meta=` kwarg on both `@app.tool` and `@app.resource`
that maps directly to protocol `_meta`, so no protocol-internal code is needed.

### Design note: dedicated tool vs. progressive enhancement

We added a **new** `dalgo_render_chart` tool rather than annotating the existing
`dalgo_get_chart_data`. This keeps the text-only tool unchanged for clients that
don't support MCP Apps, and lets the App tool return render-shaped
`structuredContent` (chart type + axes + rows) that the text tool doesn't.

The alternative — annotate `dalgo_get_chart_data` directly and return both text
and `structuredContent` — is the spec's "progressive enhancement" pattern and
would avoid adding a tool. We can migrate to it once the view is validated, if we
prefer one tool over two.

## Verification status

- ✅ Unit tested: resource registers with the correct MIME type and `_meta`; tool
  links to the resource and returns masked structured content (`tests/test_chart_app.py`).
- ✅ Packaging: `chart_view.html` is included in the built wheel.
- ⚠️ **Not yet verified end-to-end in a host.** The exact `postMessage` envelope
  must be confirmed by loading the server in Claude Desktop and calling
  `dalgo_render_chart`. The view is written defensively (it accepts a couple of
  result-envelope shapes), but the handshake may need small adjustments against a
  live host. This is the first follow-up task below.

## Roadmap — what's next

Ordered by value-to-effort.

1. **Validate the chart App end-to-end** in Claude Desktop; adjust the
   `postMessage` handshake / result parsing to match the live host. Capture a
   screenshot for the README.
2. **Pipeline run board** (`dalgo_list_pipelines` + `dalgo_get_pipeline_run_history`)
   — a red/green status grid with a *Trigger run* button that calls
   `dalgo_trigger_pipeline_run` back over `tools/call`. First App to exercise
   bidirectional callbacks; pairs with the `dalgo-pipelines` skill.
3. **Transform DAG viewer** (`dalgo_get_transform_graph`) — an interactive dbt
   lineage graph. Highest "impossible in text" payoff.
4. **Data grid** (`dalgo_get_table_data`) — sortable, paginated table; also moves
   row volume out of the model's context window into the iframe.
5. **Dashboard view** (`dalgo_get_dashboard`) — lay out a dashboard's charts,
   reusing the chart view per panel.

### Cross-cutting work

- **Toolset / App gating.** Add a `DALGO_ENABLE_APPS` (and per-app) env flag so
  Apps can be disabled for hosts that don't support them or to save context.
  Ties into the broader toolset-gating idea from the dbt-mcp comparison.
- **Shared App scaffolding.** Once there are 2–3 Apps, extract the handshake +
  result-handling JS into a shared `app_base.js` the views import, instead of
  duplicating per view.
- **CSP review.** Views are self-contained today (default-deny). If a future App
  needs a CDN (e.g. a mapping library), declare it in `_meta.ui.csp` explicitly.
- **Eval coverage.** Add a smoke check that each registered tool's
  `_meta.ui.resourceUri` resolves to a registered resource, to catch drift.

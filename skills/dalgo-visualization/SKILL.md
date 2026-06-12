---
name: dalgo-visualization
description: Create and manage Dalgo charts, dashboards, and reports. Use when a user asks to visualize data, build or modify a dashboard, or snapshot data into a report.
---

# dalgo-visualization

Use for chart, dashboard, and report workflows through Dalgo MCP tools.

## Always

- Create charts before assembling them into dashboards; `dalgo_create_dashboard` and `dalgo_update_dashboard` reference existing chart IDs.
- Validate a new or edited chart with `dalgo_get_chart_data` before telling the user it works — a chart can save fine and still have a broken query.
- Resolve names to IDs via the `list_*` tool for the object type before any detail or mutation call.
- Confirm with the user before any `delete_*` call; never delete as a fallback after a failed update.
- Check column names and types with `dalgo-warehouse` tools before building a chart query against an unfamiliar table.

## Decision Rules

- "Show me X as a chart": find the table/columns (`dalgo-warehouse`), create the chart, then run `dalgo_get_chart_data` to confirm it returns rows.
- "Add this to a dashboard": existing dashboard → `dalgo_get_dashboard` to see its current charts, then `dalgo_update_dashboard`. Only create a new dashboard when the user asks for one.
- "What's on dashboard X?": `dalgo_get_dashboard` includes its charts — no need to fetch each chart.
- "Snapshot this data" / point-in-time record: `dalgo_create_report`; reports are snapshots, charts are live queries.
- Chart returns no data: check the underlying table has rows (`dalgo-warehouse`) and the last sync ran (`dalgo-troubleshooting`) before changing the chart.

## Workflow Order

1. Resolve the data: schema, table, columns.
2. Create or update the chart; verify with `dalgo_get_chart_data`.
3. Assemble dashboards from verified chart IDs.
4. Report back with what was created and where to find it in the Dalgo UI.

## Retrieve

- Tool table: [references/visualization-workflows.md](references/visualization-workflows.md)

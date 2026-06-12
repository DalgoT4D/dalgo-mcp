# Visualization Workflows

| Goal | Tool | Key parameter |
|---|---|---|
| List charts | `dalgo_list_charts` | — |
| Get chart details | `dalgo_get_chart` | `chart_id` |
| Run a chart's query | `dalgo_get_chart_data` | `chart_id` |
| Create a chart | `dalgo_create_chart` | title, type, schema/table, config |
| Update a chart | `dalgo_update_chart` | `chart_id` |
| Delete a chart | `dalgo_delete_chart` | `chart_id` (confirm first) |
| List dashboards | `dalgo_list_dashboards` | — |
| Get dashboard + charts | `dalgo_get_dashboard` | `dashboard_id` |
| Create a dashboard | `dalgo_create_dashboard` | title, chart IDs |
| Update a dashboard | `dalgo_update_dashboard` | `dashboard_id` |
| Delete a dashboard | `dalgo_delete_dashboard` | `dashboard_id` (confirm first) |
| List reports | `dalgo_list_reports` | — |
| View a report | `dalgo_get_report` | `report_id` |
| Create a report (snapshot) | `dalgo_create_report` | title, data config |
| Delete a report | `dalgo_delete_report` | `report_id` (confirm first) |

## Example

User: "Make a chart of beneficiaries per district and put it on the field-ops dashboard."

1. `dalgo_get_table_columns` on the beneficiaries table → confirm a district column exists
2. `dalgo_create_chart` (bar chart, count by district)
3. `dalgo_get_chart_data(chart_id)` → confirm rows come back
4. `dalgo_list_dashboards` → find "field-ops" → `dalgo_get_dashboard` → `dalgo_update_dashboard` adding the chart ID

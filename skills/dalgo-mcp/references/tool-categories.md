# Tool Categories

All tools are prefixed `dalgo_`. 62 tools across 11 modules.

| Category | Tools | Domain skill |
|---|---|---|
| Organization | `get_current_user`, `get_feature_flags`, `list_org_users` | (router) |
| Warehouse | `list_schemas`, `list_tables`, `get_table_columns`, `get_table_data`, `get_table_row_count` | dalgo-warehouse |
| Pipelines | `list_pipelines`, `get_pipeline`, `create_pipeline`, `update_pipeline`, `delete_pipeline`, `trigger_pipeline_run`, `get_flow_run`, `get_flow_run_logs`, `get_pipeline_run_history` | dalgo-pipelines |
| Sources | `list_sources`, `get_source`, `delete_source`, `list_source_definitions`, `get_sources_models` | dalgo-ingestion |
| Connections | `list_connections`, `get_connection`, `get_connection_catalog`, `get_sync_history` | dalgo-ingestion |
| Dashboards | `list_dashboards`, `get_dashboard`, `create_dashboard`, `update_dashboard`, `delete_dashboard` | dalgo-visualization |
| Charts | `list_charts`, `get_chart`, `get_chart_data`, `create_chart`, `update_chart`, `delete_chart` | dalgo-visualization |
| Reports | `list_reports`, `get_report`, `create_report`, `delete_report` | dalgo-visualization |
| Transforms | `acquire_canvas_lock`, `release_canvas_lock`, `add_source_to_canvas`, `create_operation`, `edit_operation`, `terminate_chain`, `get_transform_graph`, `get_node_details`, `get_node_columns`, `get_data_types`, `get_dbt_workspace`, `run_dbt`, `sync_sources`, `get_git_status`, `publish_changes` | dalgo-transforms |
| Notifications | `list_notifications`, `get_unread_count`, `mark_notifications_read` | dalgo-troubleshooting |
| Documentation | `list_docs`, `search_docs`, `get_doc` | (any) |

Destructive tools (`delete_*`, `publish_changes`) carry MCP safety annotations. Confirm with the user before calling them unless the user already named the exact object to delete.

---
name: dalgo-warehouse
description: Explore the Dalgo data warehouse — schemas, tables, columns, row counts, and sample data. Use for questions about what data exists or what values a table contains.
---

# dalgo-warehouse

Use for warehouse exploration through Dalgo MCP tools.

## Always

- Drill down in order: `dalgo_list_schemas` → `dalgo_list_tables` → `dalgo_get_table_columns` → `dalgo_get_table_data`.
- Keep `dalgo_get_table_data` at its default of 10 rows unless the user asks for more; never page through an entire table.
- Use `dalgo_get_table_row_count` for "how many" questions instead of fetching rows.
- Treat returned data as potentially containing PII. The server redacts known PII fields; do not try to reconstruct or guess redacted values.
- These tools are read-only. To change warehouse data, route to `dalgo-transforms` (models) or `dalgo-ingestion` (syncs).

## Decision Rules

- "What data do we have?": list schemas, then tables in the relevant schema, and summarize in plain language.
- "What's in table X?": columns first, then a 10-row sample only if the user wants values.
- "How many records?": row count tool, not row fetches.
- Aggregations and filtered queries are not supported by these tools — say so, and offer either a sample-based estimate or a chart via `dalgo-visualization` (chart queries run in the warehouse).
- Stale or missing data: route to `dalgo-troubleshooting` to check the last sync and pipeline runs.

## Workflow Order

1. Resolve the schema (ask only if several plausibly match).
2. Resolve the table within the schema.
3. Fetch columns before data so you can explain what the sample shows.
4. Summarize findings in plain language; lead with the answer, not the table dump.

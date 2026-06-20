# Topic: Observability, rate limiting & abuse

## Observability
The bar, set mainly by Grafana and Sentry:
- **Metrics:** Grafana exposes **Prometheus `/metrics`** (`--metrics`, optional separate
  `--metrics-address`). Track per-tool call count, latency, error rate, and token cost.
- **Slow-request logging:** Grafana's `--slow-request-threshold` (e.g. `500ms`).
- **Structured, level-controlled logs:** `--log-level debug|info|warn|error`. Use JSON
  in production, not free-form text.
- **Error reporting + tracing:** Sentry **dogfoods Sentry** on its own MCP. Trace the
  MCP→upstream-API hop; report exceptions to an aggregator (Sentry/OTel).

### Pitfall: secret leakage in logs
Debug request-logging that dumps headers will log bearer tokens. Redact `Authorization`
and request bodies before logging (dalgo-mcp's `DebugRequestMiddleware` currently leaks
these — production-readiness A9).

## Rate limiting & abuse
This is the **least mature** area across the ecosystem — most servers defer to the
upstream API's limits and document nothing. For a hosted MCP that can *amplify* load,
that's insufficient.
- Enforce **per-token and per-org** limits at the MCP edge (nginx `limit_req_zone`, or an
  app-layer limiter) to protect the backend.
- Add **quotas on expensive tools** (warehouse queries, chart-data, dbt runs).
- Tag **MCP-origin requests** so the backend can attribute and throttle them, and keep an
  audit trail of who called what.
- Bound outputs (row caps, truncation) so a single call can't blow up cost or context.

## Health
- Liveness: process is up. Readiness: upstream API reachable + dependencies OK.
- Surface useful counters on a health endpoint (dalgo-mcp's `/health` already returns
  uptime, active token-clients, tool count).

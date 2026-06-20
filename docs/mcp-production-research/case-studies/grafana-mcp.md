# Case study: Grafana MCP

**Repo:** grafana/mcp-grafana · **Lang:** Go · **Hosting:** self-host ·
**Stars:** ~3.2k · **License:** Apache-2.0

The most complete **operability** example: tool categories, read-only, metrics, TLS,
session management, and Helm — all via flags.

## Transport
- `-t stdio` (default) | `-t sse` | `-t streamable-http`.
- `--address` (default `localhost:8000`), `--base-path`, `--endpoint-path` (default `/`).

## Tool surface & gating ← the standout
- Tools organized into **categories**; `--enabled-tools` (comma-separated categories).
- Per-category disable: `--disable-<category>` (e.g. `--disable-dashboard`, `--disable-prometheus`).
- **Read-only:** `--disable-write` blocks all writes (dashboard updates, incident
  creation, annotations, snapshots…).
- Several categories disabled by default (admin, cloudwatch, elasticsearch, snowflake, …)
  to keep the surface small.

## Auth
- Service account token: `GRAFANA_SERVICE_ACCOUNT_TOKEN` (or `_FILE` re-read per request).
- `GRAFANA_URL` required; `GRAFANA_ORG_ID` for multi-org.
- `GRAFANA_FORWARD_HEADERS` — allowlist of headers to forward (SSE/HTTP only) — a clean
  **multi-tenant** mechanism.

## Observability ← the standout
- `--metrics` exposes **Prometheus metrics at `/metrics`** (optionally on a separate
  `--metrics-address`).
- `--slow-request-threshold` (e.g. `500ms`) for slow-request logging.
- `--log-level debug|info|warn|error`; `-debug` for HTTP request/response logging.
- `--session-idle-timeout-minutes` (default 30) for session lifecycle.

## Security / TLS
- Client TLS to Grafana (`--tls-cert-file`/`--tls-key-file`/`--tls-ca-file`).
- **Server TLS** for streamable-http (`--server.tls-cert-file`/`--server.tls-key-file`).

## Distribution
- `uvx mcp-grafana`, binary releases, `docker pull grafana/mcp-grafana`,
  `go install`, and a **Helm chart** for Kubernetes.

## What to copy for dalgo-mcp
- Tool **categories + `--disable-write`** — a clean, proven gating model.
- **Prometheus `/metrics` + slow-request threshold + session idle timeout** — the
  operability features we're missing.
- Header-forwarding allowlist as an explicit multi-tenant control.
- A Helm chart if we target k8s.

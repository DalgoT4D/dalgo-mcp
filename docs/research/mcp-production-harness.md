# How teams build the production "harness" around MCP servers

Research synthesis for productionizing `dalgo-mcp`. Grounded in direct inspection
of real repositories and official docs (June 2026). Citations point to specific
repos/files/flags so claims are verifiable.

**Servers studied:** dbt-labs/dbt-mcp (Python, ~578★), getsentry/sentry-mcp
(TypeScript, ~724★, hosted at `mcp.sentry.dev`), github/github-mcp-server (Go,
~30.7k★, hosted at `api.githubcopilot.com/mcp/`), cloudflare/mcp-server-cloudflare
(TypeScript, ~3.8k★, ~18 servers under `*.mcp.cloudflare.com`),
modelcontextprotocol/servers (reference) and modelcontextprotocol/registry.

---

## 1. Executive summary — what separates a production MCP server from a prototype

1. **A real auth story for remote mode.** OAuth 2.1 with scoped, least-privilege
   tokens and per-request identity — not a single shared service token. (Sentry,
   GitHub, Cloudflare all do this; we already have OAuth + per-token JWT clients.)
2. **Toolset gating.** Every mature multi-tool server lets operators enable/disable
   *groups* of tools and run **read-only** — both for token cost and for safety.
   (GitHub `--toolsets`/`--read-only`; dbt `DBT_MCP_ENABLE_*`; Sentry `MCP_DISABLE_SKILLS`.)
   We register all 63 tools unconditionally — the single biggest gap.
3. **Token-cost as a tracked metric.** Sentry runs a `token-cost.yml` CI job; we
   have `scripts/measure_token_cost.py` but don't gate on it.
4. **Evals, not just unit tests.** The best servers test that an LLM can actually
   *use* the tools (Sentry's `mcp-server-evals`, `pnpm eval`). Unit tests alone
   miss tool-description regressions.
5. **Remote hosting on managed/edge infra** with health checks, autoscaling, and a
   stateless-per-request design so tokens map to tenants (Sentry/Cloudflare on
   Workers; GitHub on its own infra).
6. **Self-observability.** Structured logs + metrics + tracing + error reporting on
   the server itself. Sentry dogfoods Sentry; this is table stakes for a hosted
   service. We have request/tool-call logging middleware but no metrics/tracing.
7. **Prompt-injection / data-egress defenses.** GitHub ships `GITHUB_LOCKDOWN_MODE`
   to restrict untrusted public-repo content; read-only modes everywhere. We have
   PII masking + truncation, which is a good start.
8. **Automated, semver'd releases + multiple distribution channels** — PyPI/npm,
   Docker image (GHCR), an **mcpb bundle**, and a listing in the **MCP registry**.
9. **Distribution-grade docs/DX** — one-command installs, per-host config snippets,
   and runnable **examples for several agent frameworks** (dbt-mcp's `examples/`).
10. **Governance hygiene** — CONTRIBUTING, issue/PR templates, CODEOWNERS,
    dependabot, changelog automation. Cheap signals of maturity.

---

## 2. Harness taxonomy (12 dimensions)

### 1. Transport & hosting
- **Pattern:** ship **stdio** for local + **streamable-http** for remote. SSE is
  deprecated (Cloudflare serves `/mcp` streamable-http and a deprecated `/sse`).
- GitHub: remote HTTP at `https://api.githubcopilot.com/mcp/` **and** local Docker/binary (`github-mcp-server stdio`).
- Sentry: remote HTTP primary (`mcp.sentry.dev`), stdio secondary ("work in progress").
- **For us:** we already have both transports. Mark stdio as the local path, streamable-http as the hosted path. Avoid SSE.

### 2. Auth & multi-tenancy
- **Remote = OAuth 2.1 + scoped tokens.** Sentry: `SENTRY_CLIENT_ID/SECRET`, scopes
  `org:read, project:read, project:write, team:read, team:write, event:write`.
  GitHub: PAT / OAuth / GitHub App, least-privilege scopes (`repo`, `read:org`, …).
- **Per-request identity → tenant.** Each user's token scopes them to their data.
  We already cache a client per JWT and detect org via `/api/currentuserv2`.
- **Local = a token/credentials in env**, never a shared service secret in remote mode.
- **For us:** the multi-tenant model is built. Harden: token TTL/refresh, audit
  logging of who called what, and confirm one tenant's token can never read another's data.

### 3. Config & secrets
- **Env-var driven** everywhere; dbt-mcp's `.env.example` enumerates every flag.
  GitHub documents `chmod 600` on config files and keeping tokens out of VCS.
- dbt-mcp has a `config/config_providers/` layer abstracting where settings come from.
- **For us:** our `config.py` is fine; add a documented `.env.example` superset and,
  for hosted mode, pull secrets from a secret manager rather than a baked `.env`.

### 4. Tool surface management ← biggest gap for us
- **Toolset gating is universal:**
  - GitHub: `--toolsets repos,issues,…` / `GITHUB_TOOLSETS`, `default`/`all`,
    per-tool `--tools`, **`--read-only`/`GITHUB_READ_ONLY`**, dynamic toolset
    discovery, 16 toolsets.
  - dbt-mcp: `DBT_MCP_ENABLE_SEMANTIC_LAYER`, `DBT_MCP_ENABLE_DISCOVERY`,
    `DBT_MCP_ENABLE_DBT_CLI`, … plus `DISABLE_TOOLS`.
  - Sentry: `MCP_DISABLE_SKILLS` (e.g. disable `seer`); AI tools gated on an LLM provider.
- **Token-cost control:** Sentry CI `token-cost.yml`; dbt/we measure schema token cost.
- **Pagination/truncation:** we already default `get_table_data` to 10 rows and
  truncate logs — same instinct.
- **For us:** add `DALGO_ENABLE_<MODULE>` (our 11 modules map cleanly) and a global
  read-only flag that hides every `delete_*`/mutating tool.

### 5. Deployment & infra
- **Edge/serverless:** Sentry & Cloudflare on Workers (stateless, per-request token).
- **Containers:** GitHub publishes `ghcr.io/github/github-mcp-server`; we have a
  Dockerfile + compose + nginx.
- **Health checks:** we expose `/health`. Add readiness vs liveness distinction and
  surface tool count / active token-clients (we already do the latter).
- **For us:** decide hosted topology (container on Dalgo infra behind the existing
  nginx vs edge). Add autoscaling + a documented reverse-proxy/TLS setup.

### 6. Observability
- **Sentry dogfoods Sentry** — errors + tracing on their own MCP. This is the
  reference example of server self-observability.
- Cloudflare ships a dedicated `workers-observability` MCP and treats observability
  as first-class.
- **For us:** we have `ToolCallLoggingMiddleware` (per-call timing + success). Add:
  structured JSON logs, a metrics endpoint (per-tool latency/error counters), and
  error reporting (Sentry/OTel). Tracing across the MCP→Dalgo-API hop is high value.

### 7. Rate limiting, quotas & abuse
- Under-documented across the board (even GitHub defers to the underlying API's limits).
- **For us:** the Dalgo backend is the scaling bottleneck — per-token and per-org
  rate limits belong at the MCP edge (nginx or app middleware) to protect the
  backend, plus quotas on expensive tools (`get_chart_data`, `run_dbt`, `get_table_data`).

### 8. Reliability & error handling
- Consistent structured error envelopes (we have `format_response` + `errors.py`).
- Timeouts + retries on upstream calls; graceful degradation when a sub-capability
  is unavailable (Sentry: AI tools degrade, "all other tools function normally").
- GitHub fails fast on invalid tool names at startup; preserves renamed tools via aliases.
- **For us:** add explicit httpx timeouts/retries to the Dalgo client; make sure one
  failing endpoint (e.g. the chart-data 500s we saw) degrades cleanly per-tool.

### 9. Security
- **Read-only modes** everywhere as the primary blast-radius control.
- **GitHub `GITHUB_LOCKDOWN_MODE`** restricts untrusted public content — an explicit
  prompt-injection / tool-poisoning defense.
- Least-privilege scopes, token rotation, dependency pinning (dbt-mcp pins deps and
  only auto-updates for security).
- **For us:** PII masking + truncation exist. Add: a read-only mode, dependency
  pinning policy, input validation on free-form tool args (`chart_data: dict`,
  `run_params`), and a security review of the OAuth/login routes.

### 10. Testing & evals
- **Sentry is the gold standard:** dedicated packages `mcp-server-evals` (`pnpm eval`,
  needs `OPENAI_API_KEY`), `mcp-server-mocks`, `mcp-test-client`, `smoke-tests`,
  `agent-cli-test`, plus MCP Inspector (`pnpm inspector`). CI: `test.yml`, `eval.yml`,
  `smoke-tests.yml`, `token-cost.yml`.
- GitHub has an `e2e/` suite against live GitHub.
- **For us:** we have pytest unit tests. Add (a) an integration smoke test against a
  live/staging Dalgo, (b) an LLM eval that checks the model picks the right tool from
  the description, (c) a drift check that every `_meta.ui.resourceUri` resolves.

### 11. Release, versioning & distribution
- **Changelog automation:** dbt-mcp uses **changie** (`.changie.yaml`, kind→bump
  mapping) + a `Create release PR` workflow + a Claude release skill.
- **Channels:** PyPI/npm + Docker (GHCR) + **mcpb bundle** (dbt ships `dbt-mcp.mcpb`
  per release) + the **MCP registry** (modelcontextprotocol/registry) for discovery.
- **For us:** we have semver tags + PyPI publish (pending trusted-publisher setup) +
  a Claude Code plugin. Add: GHCR image publish, an mcpb bundle, a registry listing,
  and consider changie to kill the manual changelog step.

### 12. Docs & developer experience
- dbt-mcp ships `examples/` for **many agent frameworks** (LangGraph, CrewAI, Google
  ADK, OpenAI SDK, Vercel AI SDK, AWS Strands) — strong adoption signal.
- Sentry ships a hosted **web playground/landing** (`mcp-cloudflare` client) with a
  chat UI and install tabs per host.
- Governance: CONTRIBUTING, issue/PR templates, CODEOWNERS, dependabot, OpenSSF badge.
- **For us:** we have a strong README, demo GIF, and skills. Add 1–2 framework
  examples, governance files, and per-host config snippets (we have Desktop/Code).

---

## 3. Per-exemplar highlights (what to copy)

- **dbt-mcp** — copy: `DBT_MCP_ENABLE_*` toolset gating; **changie** release
  automation; the `.mcpb` bundle per release; `examples/` per framework; the
  `.claude/skills/release-*` skill that drives the release.
- **Sentry MCP** — copy: the **testing pyramid** (evals + mocks + test-client +
  smoke-tests as separate packages); the **`token-cost.yml`** CI gate; **dogfooded
  self-observability**; graceful degradation when the LLM-provider-dependent tools
  can't run; a hosted web playground with per-host install tabs.
- **GitHub MCP server** — copy: `--toolsets`/`--read-only`/`--tools` granularity;
  **`GITHUB_LOCKDOWN_MODE`** as an explicit injection defense; dynamic toolset
  discovery; fail-fast on bad tool names with backward-compatible aliases; clear
  least-privilege scope docs.
- **Cloudflare** — copy (if we go edge): streamable-http on `/mcp`, deprecate SSE;
  `workers-oauth-provider` pattern; `mcp-remote` as the local→remote bridge; a
  dedicated observability surface.
- **MCP registry** — list `dalgo-mcp` for discoverability once stable.

---

## 4. Production-readiness checklist for a FastMCP Python server (ours)

**Must-have before a hosted launch**
- [ ] Toolset gating: `DALGO_ENABLE_<MODULE>` (11 modules) + a global **read-only** flag.
- [ ] Verify tenant isolation: a token can never reach another org's data (test it).
- [ ] httpx timeouts + retries on every Dalgo API call; per-tool graceful degradation.
- [ ] Structured JSON logging + error reporting (Sentry/OTel) on the server.
- [ ] Rate limiting + quotas per token/org at the MCP edge (protect the backend).
- [ ] Secrets from a manager (not a baked `.env`) in hosted mode; token TTL/refresh.
- [ ] Health: liveness + readiness; container published to GHCR; documented TLS/proxy.
- [ ] Security pass on OAuth/login routes; input validation on free-form `dict` args.
- [ ] Integration smoke test against staging in CI.

**High-value, soon after**
- [ ] LLM eval suite (right-tool-selection) + `token-cost` CI gate.
- [ ] Metrics endpoint (per-tool latency/error/usage counters) + tracing across the API hop.
- [ ] mcpb bundle per release; MCP registry listing.
- [ ] changie (or similar) changelog automation; GHCR + PyPI in one release flow.

**Nice-to-have**
- [ ] Framework examples (`examples/langgraph`, `examples/anthropic-sdk`).
- [ ] Hosted web playground / landing with per-host install tabs.
- [ ] Governance files (CONTRIBUTING, issue/PR templates, CODEOWNERS, dependabot).
- [ ] i18n/description overrides (GitHub-style) if non-English NGO users need it.

---

## 5. Open questions / unsettled in the ecosystem

- **Eval standards are immature.** Everyone rolls their own (Sentry's `pnpm eval`);
  no shared benchmark for "can an agent use these tools."
- **Remote-auth conventions still settling.** OAuth 2.1 + protected-resource metadata
  is the direction, but implementations differ; the SDK's auth helpers are young.
- **Registry maturity.** modelcontextprotocol/registry exists but discovery/trust
  (signing, verification) is early.
- **Rate limiting / abuse** is barely documented publicly — each team improvises.
- **mcpb vs plugin vs registry** — three overlapping distribution mechanisms; no clear
  single winner yet.

## 6. Sources
- dbt-labs/dbt-mcp (README, `.env.example`, `.changie.yaml`, `.claude/skills/release-dbt-mcp`)
- getsentry/sentry-mcp (README; `packages/` — mcp-server-evals, mcp-server-mocks, mcp-test-client, smoke-tests; `.github/workflows/` — deploy, eval, smoke-tests, test, token-cost, release)
- github/github-mcp-server (README — toolsets/flags/env, `e2e/`)
- cloudflare/mcp-server-cloudflare (README — multi-server monorepo, `/mcp` + `/sse`, mcp-remote)
- modelcontextprotocol/servers, modelcontextprotocol/registry
- modelcontextprotocol.io (transport & auth conventions)

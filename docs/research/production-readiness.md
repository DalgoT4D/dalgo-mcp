# Pushing dalgo-mcp to production — two-track readiness plan

Combines (1) external harness research ([mcp-production-harness.md](./mcp-production-harness.md)),
(2) a gap analysis of the **MCP codebase**, and (3) a readiness analysis of the
**Dalgo backend** (`DDP_backend`). All claims cite `file:line`.

Assumed target: a **Dalgo-hosted, multi-tenant** MCP service (each user connects
with their own JWT) — the model the existing OAuth + streamable-http code points at.

---

## TL;DR

- **Foundations are good.** Dual transport, OAuth/PKCE/refresh, per-token client
  caching, PII masking, hardened Docker, OIDC PyPI publish.
- **One reassuring backend finding:** tenant isolation is *enforced server-side* —
  a user can only ever resolve an org they belong to (`DDP_backend/ddpui/auth.py:61-65,139-143`).
  So the MCP's "pin to org[0]" issue is a *wrong-org-among-your-own-orgs* correctness
  bug, **not** a cross-tenant data leak.
- **Hard blockers for hosting:** no rate limiting anywhere (MCP or backend), no
  toolset/read-only gating, in-memory OAuth state (can't scale horizontally), broken
  deploy port config, and bearer tokens logged in debug mode.

---

## Track A — MCP server (dalgo-mcp)

Gap analysis against the production checklist. Status / evidence / effort.

| # | Area | Status | Evidence | Gap | Effort |
|---|------|--------|----------|-----|--------|
| A1 | Horizontal scaling | ❌ | `oauth.py:59-64`, `client.py:14` — OAuth clients/codes/tokens + token-client cache are **in-memory module state** | Replicas won't share sessions; restart drops all auth. Needs Redis/DB-backed store | L |
| A2 | Multi-org selection | 🟡 | `client.py:50,54` pins to `data[0]`/`orgs[0]` | Multi-org users may get the wrong (own) org; no way to choose target org | M |
| A3 | Toolset gating / read-only | ❌ | `server.py:187-202` registers all 63 tools; annotations exist (`charts.py:14,32,43,54`) but nothing consumes them | No `DALGO_ENABLE_<module>`, no read-only mode hiding `delete_*`/`run_dbt` | M |
| A4 | Input validation | 🟡 | untyped `dict` args → `client.post(json=...)`: `charts.py:33`, `pipelines.py:30`, `transforms.py:25,137`, `dashboards.py:30`, `reports.py:29` | Model controls entire request bodies; add Pydantic models | M |
| A5 | Reliability | 🟡 | `client.py:25` 60s timeout, **no retries**; `errors.py` hierarchy is dead code (`check_response` never called by tools) | Add backoff on 5xx; standardize one error path | M |
| A6 | JWT verification | 🟡 | `auth.py:21`, `oauth.py:294`, `client.py:154` decode with `verify_signature: False` | Acceptable *because* backend verifies (see B1), but no defense-in-depth | M |
| A7 | Rate limiting | ❌ | no `limit_req` in `nginx.conf`; no app limiter | Abusive token can hammer backend through MCP | S–M |
| A8 | Deploy config | 🟡 | `nginx.conf:17` proxies `:8081`, app listens `:8079` (`config.py:24`), `.env.example` says `8080`; no Docker `HEALTHCHECK` | Fresh deploy breaks; reconcile ports + add healthcheck | S |
| A9 | Observability | 🟡 | `ToolCallLoggingMiddleware` (`server.py:40-69`) HTTP-only; `DebugRequestMiddleware:24-29` **logs Authorization + body**; no metrics/tracing/error-reporting | Redact secrets; structured logs; metrics + OTel; error reporting | S–M |
| A10 | Distribution | 🟡 | `publish.yml` PyPI OK; **no GHCR image push**; `pyproject.toml`↔`plugin.json` version drift; manual changelog | Add Docker publish workflow; version sync; consider changie | S |
| A11 | Testing | 🟡 | 5 unit test files; `oauth.py`/`auth.py`/`login.py`/`context.py` untested; `measure_token_cost.py` not in CI | Add auth/tenant tests, a staging smoke test, token-cost gate | M |

**Preserve:** per-tool annotations, dual-transport design (`context.py:17-37`),
hardened non-root Docker, PII masking + truncation, working OAuth/PKCE/refresh.

---

## Track B — Dalgo backend (DDP_backend)

What the backend needs to safely serve a hosted multi-tenant MCP.

| # | Area | Status | Evidence | Note |
|---|------|--------|----------|------|
| B1 | JWT auth | ✅ | `ddpui/auth.py:117-128` validates via SimpleJWT `AccessToken(token)` (signature **is** verified); lib `djangorestframework-simplejwt==5.5.1` | The MCP can safely skip local verification |
| B2 | **Tenant isolation** | ✅ | `auth.py:61-65` & `139-143` filter `OrgUser` by `user=request.user` **and** `org__slug=x-dalgo-org` | Spoofing the org header can't reach another org's data — **not** a leak |
| B3 | RBAC | ✅ (where applied) | `has_permission()` decorator + `RolePermission` table cached in Redis (`auth.py:30,70-74`) | MCP acts as the user → inherits the user's role; can't exceed it. Must confirm the decorator is on every mutating endpoint the MCP hits |
| B4 | Token TTL / scope | 🟡 | `settings.py:324-325`: access **12h**, refresh **30d**; no scoped/service-token type | A 12h full-access token held by an LLM client is broad. Add a shorter-lived or **scoped MCP token** type |
| B5 | **Rate limiting** | ❌ | `ratelimit==2.2.1` in `requirements.txt` but **`@ratelimit` used nowhere** (grep empty) | No throttling at all. **Blocker** for a hosted MCP that can amplify load |
| B6 | Heavy endpoints | 🟡 | `/api/charts/{id}/data/` runs synchronous warehouse queries (the staging 500s); `run_dbt_via_celery` is async (good) | Add query timeouts + row caps; the chart-data path is the risk |
| B7 | PII | 🟡 | backend returns raw rows; masking lives only in the MCP (`pii.py`, 2 tools) | Either mask server-side or ensure every MCP data path masks |
| B8 | Audit / abuse | 🟡 | request logging exists; no MCP-origin tagging | Tag MCP-origin requests; per-org usage/audit trail |

**Required backend changes**
- **Must:** wire up **rate limiting** (the lib is already a dep, or do it at nginx/gateway) per user+org [B5]; introduce a **scoped/short-TTL MCP token** type [B4]; audit that `has_permission` covers every mutating endpoint the MCP calls [B3].
- **Nice:** query timeouts + row caps on warehouse/chart-data [B6]; MCP-origin audit tagging [B8]; a server-side PII policy [B7].

---

## Sequenced roadmap

**Phase 0 — make it deployable (days).** Fix port config + add `HEALTHCHECK` [A8];
redact Authorization in debug logging [A9]; add nginx `limit_req` rate limiting [A7]
and wire backend `ratelimit` [B5]. These are small and remove the embarrassing/unsafe failures.

**Phase 1 — safe to host for a pilot (1–2 wks).** Read-only mode + toolset gating
[A3]; input validation on dict payloads [A4]; retries + one error path [A5];
multi-org selection [A2]; structured logging + error reporting [A9]; scoped/short-TTL
MCP token [B4]; confirm RBAC coverage [B3]; auth/tenant tests + staging smoke test [A11].

**Phase 2 — scale & broad rollout (2–4 wks).** Persistent shared OAuth/token store
(Redis) [A1]; metrics + tracing across the MCP→API hop [A9]; per-org quotas on
expensive tools + backend query caps [A7/B6]; GHCR image publish + version sync +
changelog automation [A10]; LLM eval suite + token-cost CI gate [A11].

**Phase 3 — polish/adoption.** mcpb bundle + MCP registry listing; framework
examples; governance files; backend MCP-origin audit trail [B8].

---

## Security blockers (do not host without these)
1. **Rate limiting** [A7 + B5] — currently none anywhere.
2. **Secret leakage in logs** [A9] — `DebugRequestMiddleware` logs bearer tokens.
3. **Scoped/short-TTL MCP tokens** [B4] — a 12h full-access token in an LLM client.

## Not a blocker (verified safe)
- Cross-tenant data access — **enforced server-side** [B2]; the MCP `verify_signature: False`
  is acceptable because the backend validates every token [B1].

# Topic: Testing & evals

Unit tests alone miss the failure mode that matters most for an MCP server: **the model
can no longer pick or call the right tool** (usually a tool-description or schema
regression). The mature answer is a layered suite.

## The testing pyramid (Sentry is the reference)
Sentry keeps each concern in its own package:
- **Unit** — pure logic, mocked upstream (`mcp-server-mocks`).
- **Test client** — a programmatic MCP client (`mcp-test-client`) that calls tools like a host.
- **Evals** — LLM-driven: does an agent choose the right tool and use it correctly?
  (`mcp-server-evals`, `pnpm eval`, needs `OPENAI_API_KEY`). dbt-mcp has `evals/` too.
- **Smoke** — end-to-end against a real/staging backend (`smoke-tests`); GitHub has `e2e/`.
- **Inspector** — manual interactive testing (`pnpm inspector`, the MCP Inspector).

## CI gates worth adding
- Run unit + smoke on every PR (dalgo-mcp's CI runs lint + unit + a registration smoke check).
- **Token-cost gate** — Sentry's `token-cost.yml` fails the build if the tool schemas grow
  past budget. dalgo-mcp has `scripts/measure_token_cost.py` but doesn't gate on it.
- A **drift check** that every tool's `_meta.ui.resourceUri` (MCP Apps) resolves to a
  registered resource.

## What dalgo-mcp specifically lacks
- Tests for the security-critical paths: OAuth, JWT/auth, login, tenant resolution.
- An integration/smoke test against a live or faked Dalgo API.
- An eval that asserts correct tool selection from descriptions.

## Open question
Eval standards are immature — everyone rolls their own; there's no shared benchmark for
"can an agent use these tools." Treat your eval suite as bespoke and version it with the tools.

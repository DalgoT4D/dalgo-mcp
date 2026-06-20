# Case study: GitHub MCP Server

**Repo:** github/github-mcp-server · **Lang:** Go ·
**Hosting:** `https://api.githubcopilot.com/mcp/` + local Docker/binary ·
**Stars:** ~30.7k · **License:** MIT

The reference example for **fine-grained tool control** and **injection defense** at
the largest scale.

## Hosting & transport
- Remote hosted HTTP server (`api.githubcopilot.com/mcp/`) for compatible hosts.
- Local: Docker image `ghcr.io/github/github-mcp-server`, or binary (`github-mcp-server stdio`).
- Enterprise: `GITHUB_HOST` for GHES/ghe.com (remote not supported for GHES → local).

## Auth
- PAT (`GITHUB_PERSONAL_ACCESS_TOKEN`), OAuth (remote), or GitHub App.
- Documented least-privilege scopes per toolset (`repo`, `read:org`, `security_events`, …).
- Security guidance: env vars not hardcoding, `chmod 600` configs, rotate tokens,
  keep out of VCS.

## Tool surface & gating ← the standout
- **16 toolsets**: actions, code_security, context, discussions, gists, git, issues,
  labels, notifications, orgs, projects, pull_requests, repos, secret_protection,
  security_advisories, stargazers, users.
- Enable groups: `--toolsets repos,issues,…` or `GITHUB_TOOLSETS` (env wins);
  `default` and `all` presets.
- Per-tool selection: `--tools get_file_contents,issue_read,…`.
- **Read-only mode:** `--read-only` / `GITHUB_READ_ONLY=1`.
- **Dynamic toolset discovery** (toolsets surfaced/loaded on demand).
- **`GITHUB_LOCKDOWN_MODE=1`** — restrict access to untrusted public-repo content;
  an explicit **prompt-injection / tool-poisoning** defense.
- i18n/description overrides: `github-mcp-server-config.json` or `GITHUB_MCP_*` env,
  `--export-translations`.

## Reliability
- Fails fast on invalid tool names at startup; preserves renamed tools via aliases.

## Testing
- `e2e/` suite against live GitHub.

## What to copy for dalgo-mcp
- The `--toolsets` / `--read-only` / `--tools` granularity model.
- A lockdown-style flag for untrusted data contexts.
- Fail-fast tool-name validation with backward-compatible aliases.
- Clear per-toolset least-privilege scope docs.

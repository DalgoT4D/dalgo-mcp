# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Seven Claude Code plugin skills (`skills/`): a `dalgo-mcp` router plus domain
  skills for warehouse, pipelines, ingestion, transforms, visualization, and
  troubleshooting, encoding workflows like trigger-poll-verify and the canvas
  lock protocol.
- Demo GIF in the README showing a real failure-diagnosis conversation.

## [0.1.0] - 2026-06-12

Initial release.

### Added

- 62 MCP tools across 11 modules: organization, warehouse, pipelines, sources,
  connections, dashboards, charts, reports, transforms, notifications, and
  documentation.
- Dual transport support: `stdio` for Claude Desktop / Claude Code and
  `streamable-http` for the Anthropic Messages API MCP connector.
- Multi-user HTTP mode with per-request Bearer JWT authentication and
  automatic organization detection.
- Claude Code plugin for one-command installation.
- Docker image and Compose setup (serves `streamable-http` on port 8079).
- PII redaction utilities and token-aware truncation of large responses.
- Safety annotations on destructive tools.
- Test suite (`pytest`) and CI (lint + test) on every push and pull request.
- Automated PyPI publishing on `v*` tags.

[Unreleased]: https://github.com/DalgoT4D/dalgo-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DalgoT4D/dalgo-mcp/releases/tag/v0.1.0

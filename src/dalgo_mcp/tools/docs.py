"""Dalgo documentation search and browsing tools.

Provides three tools for searching and reading Dalgo product documentation
sourced from https://github.com/DalgoT4D/dalgo_docs.

Uses a hardcoded doc index for instant search (no API calls) and fetches
full page content from GitHub raw only when reading a specific page.
"""

import json
import time

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# ---------------------------------------------------------------------------
# Hardcoded doc index — built from the dalgo_docs repo
# ---------------------------------------------------------------------------

DOCS_INDEX: list[dict] = [
    # --- Getting Started ---
    {"path": "docs/welcome.md", "title": "Welcome to Dalgo", "section": "Getting Started", "keywords": ["introduction", "overview", "platform"]},

    # --- Quickstart ---
    {"path": "docs/quickstart/index.md", "title": "Quickstart Guide", "section": "Quickstart", "keywords": ["getting started", "setup", "tutorial"]},
    {"path": "docs/quickstart/account-setup.md", "title": "Account Setup", "section": "Quickstart", "keywords": ["account", "signup", "registration"]},
    {"path": "docs/quickstart/impact.md", "title": "Impact Setup", "section": "Quickstart", "keywords": ["impact", "metrics", "KPIs"]},
    {"path": "docs/quickstart/first-dashboard.md", "title": "First Dashboard", "section": "Quickstart", "keywords": ["dashboard", "visualization", "tutorial"]},
    {"path": "docs/quickstart/first-report.md", "title": "First Report", "section": "Quickstart", "keywords": ["report", "snapshot", "tutorial"]},
    {"path": "docs/quickstart/next-steps.md", "title": "Next Steps", "section": "Quickstart", "keywords": ["next steps", "advanced", "resources"]},

    # --- Concepts ---
    {"path": "docs/concepts/glossary.md", "title": "Glossary", "section": "Concepts", "keywords": ["glossary", "terms", "definitions", "vocabulary"]},

    # --- Impact ---
    {"path": "docs/impact/index.md", "title": "Impact Overview", "section": "Impact", "keywords": ["impact", "home", "metrics", "KPIs", "indicators"]},

    # --- Charts ---
    {"path": "docs/charts/index.md", "title": "Charts Overview", "section": "Charts", "keywords": ["charts", "visualization", "analytics"]},
    {"path": "docs/charts/creating-a-chart.md", "title": "Creating a Chart", "section": "Charts", "keywords": ["chart", "create", "SQL", "query"]},
    {"path": "docs/charts/chart-types.md", "title": "Chart Types", "section": "Charts", "keywords": ["chart types", "bar", "line", "pie", "number"]},

    # --- Dashboards ---
    {"path": "docs/dashboards/index.md", "title": "Dashboards Overview", "section": "Dashboards", "keywords": ["dashboards", "visualization", "overview"]},
    {"path": "docs/dashboards/viewing.md", "title": "Viewing Dashboards", "section": "Dashboards", "keywords": ["view", "dashboard", "display"]},
    {"path": "docs/dashboards/creating.md", "title": "Creating Dashboards", "section": "Dashboards", "keywords": ["create", "dashboard", "new"]},
    {"path": "docs/dashboards/superset-usage.md", "title": "Superset Usage", "section": "Dashboards", "keywords": ["superset", "apache", "analytics", "BI"]},
    {"path": "docs/dashboards/superset.md", "title": "Superset Integration", "section": "Dashboards", "keywords": ["superset", "integration", "BI", "connect"]},

    # --- Reports ---
    {"path": "docs/reports/index.md", "title": "Reports Overview", "section": "Reports", "keywords": ["reports", "snapshots", "data"]},
    {"path": "docs/reports/creating.md", "title": "Creating Reports", "section": "Reports", "keywords": ["create", "report", "new", "snapshot"]},
    {"path": "docs/reports/comments.md", "title": "Report Comments", "section": "Reports", "keywords": ["comments", "collaboration", "feedback"]},
    {"path": "docs/reports/sharing.md", "title": "Sharing Reports", "section": "Reports", "keywords": ["share", "report", "collaboration", "access"]},
    {"path": "docs/reports/exporting.md", "title": "Exporting Reports", "section": "Reports", "keywords": ["export", "download", "PDF", "CSV"]},

    # --- Data ---
    {"path": "docs/data/index.md", "title": "Data Management", "section": "Data", "keywords": ["data", "management", "overview"]},
    {"path": "docs/data/overview.md", "title": "Data Overview", "section": "Data", "keywords": ["data", "summary", "pipeline", "architecture"]},

    # --- Data > Ingest ---
    {"path": "docs/data/ingest/index.md", "title": "Data Ingestion", "section": "Data > Ingest", "keywords": ["ingest", "ETL", "ELT", "sync"]},
    {"path": "docs/data/ingest/connections.md", "title": "Connections", "section": "Data > Ingest", "keywords": ["connections", "airbyte", "sync", "source"]},
    {"path": "docs/data/ingest/sources.md", "title": "Data Sources", "section": "Data > Ingest", "keywords": ["sources", "connectors", "airbyte"]},
    {"path": "docs/data/ingest/warehouse.md", "title": "Warehouse Setup", "section": "Data > Ingest", "keywords": ["warehouse", "destination", "database", "BigQuery"]},

    # --- Data > Transform ---
    {"path": "docs/data/transform/index.md", "title": "Data Transformation", "section": "Data > Transform", "keywords": ["transform", "dbt", "models"]},
    {"path": "docs/data/transform/ui-transform.md", "title": "UI Transformations", "section": "Data > Transform", "keywords": ["transform", "UI", "no-code", "visual"]},
    {"path": "docs/data/transform/dbt-transform.md", "title": "dbt Transformations", "section": "Data > Transform", "keywords": ["dbt", "transform", "SQL", "models"]},
    {"path": "docs/data/transform/switching-repositories.md", "title": "Switching Repositories", "section": "Data > Transform", "keywords": ["git", "repository", "switch", "dbt"]},

    # --- Data (continued) ---
    {"path": "docs/data/orchestrate.md", "title": "Orchestration", "section": "Data", "keywords": ["orchestrate", "pipeline", "prefect", "schedule", "cron"]},
    {"path": "docs/data/explore.md", "title": "Data Exploration", "section": "Data", "keywords": ["explore", "query", "data", "browse"]},
    {"path": "docs/data/quality.md", "title": "Data Quality", "section": "Data", "keywords": ["quality", "testing", "validation", "checks"]},

    # --- Settings ---
    {"path": "docs/settings/index.md", "title": "Settings Overview", "section": "Settings", "keywords": ["settings", "configuration", "preferences"]},
    {"path": "docs/settings/user-management.md", "title": "User Management", "section": "Settings", "keywords": ["users", "roles", "permissions", "invite"]},
    {"path": "docs/settings/billing.md", "title": "Billing", "section": "Settings", "keywords": ["billing", "subscription", "payment", "plan"]},
    {"path": "docs/settings/about.md", "title": "About", "section": "Settings", "keywords": ["about", "version", "info"]},

    # --- Support ---
    {"path": "docs/support/index.md", "title": "Support Overview", "section": "Support", "keywords": ["support", "help", "contact"]},
    {"path": "docs/support/getting-help.md", "title": "Getting Help", "section": "Support", "keywords": ["help", "support", "contact", "community"]},
    {"path": "docs/support/troubleshooting.md", "title": "Troubleshooting", "section": "Support", "keywords": ["troubleshoot", "debug", "errors", "FAQ"]},

    # --- Self-Serve ---
    {"path": "self-serve-docs/intro.md", "title": "Self-Serve Introduction", "section": "Self-Serve", "keywords": ["self-serve", "introduction", "overview"]},

    # --- Self-Serve > Data Sources ---
    {"path": "self-serve-docs/data-sources/adding-a-data-source.md", "title": "Adding a Data Source", "section": "Self-Serve > Data Sources", "keywords": ["data source", "add", "connector", "setup"]},

    # --- Self-Serve > Warehouse ---
    {"path": "self-serve-docs/warehouse/aws-rds-setup.md", "title": "AWS RDS Setup", "section": "Self-Serve > Warehouse", "keywords": ["AWS", "RDS", "database", "setup", "PostgreSQL"]},

    # --- Self-Serve > Superset ---
    {"path": "self-serve-docs/superset/row-level-security.md", "title": "Row-Level Security", "section": "Self-Serve > Superset", "keywords": ["superset", "RLS", "security", "permissions", "row-level"]},
    {"path": "self-serve-docs/superset/user-and-role-management.md", "title": "User and Role Management", "section": "Self-Serve > Superset", "keywords": ["superset", "users", "roles", "permissions", "admin"]},
    {"path": "self-serve-docs/superset/embedding-dashboards.md", "title": "Embedding Dashboards", "section": "Self-Serve > Superset", "keywords": ["superset", "embed", "iframe", "dashboard", "integration"]},

    # --- Self-Serve > Local Dev Setup ---
    {"path": "self-serve-docs/local-dev-setup/index.md", "title": "Local Development Setup", "section": "Self-Serve > Local Dev Setup", "keywords": ["local", "development", "setup", "environment"]},
    {"path": "self-serve-docs/local-dev-setup/dalgo-login.md", "title": "Dalgo Login", "section": "Self-Serve > Local Dev Setup", "keywords": ["login", "authentication", "credentials"]},
    {"path": "self-serve-docs/local-dev-setup/warehouse-access.md", "title": "Warehouse Access", "section": "Self-Serve > Local Dev Setup", "keywords": ["warehouse", "access", "database", "connection"]},
    {"path": "self-serve-docs/local-dev-setup/github-setup.md", "title": "GitHub Setup", "section": "Self-Serve > Local Dev Setup", "keywords": ["github", "git", "repository", "clone"]},
    {"path": "self-serve-docs/local-dev-setup/python-and-ide.md", "title": "Python and IDE Setup", "section": "Self-Serve > Local Dev Setup", "keywords": ["python", "IDE", "vscode", "editor"]},
    {"path": "self-serve-docs/local-dev-setup/ssh-access.md", "title": "SSH Access", "section": "Self-Serve > Local Dev Setup", "keywords": ["SSH", "remote", "access", "server"]},
    {"path": "self-serve-docs/local-dev-setup/dbt-setup.md", "title": "dbt Setup", "section": "Self-Serve > Local Dev Setup", "keywords": ["dbt", "setup", "install", "local"]},
    {"path": "self-serve-docs/local-dev-setup/dbt-profiles.md", "title": "dbt Profiles", "section": "Self-Serve > Local Dev Setup", "keywords": ["dbt", "profiles", "configuration", "profiles.yml"]},
    {"path": "self-serve-docs/local-dev-setup/vaultwarden.md", "title": "Vaultwarden", "section": "Self-Serve > Local Dev Setup", "keywords": ["vaultwarden", "passwords", "secrets", "vault"]},
    {"path": "self-serve-docs/local-dev-setup/ai-coding-assistants.md", "title": "AI Coding Assistants", "section": "Self-Serve > Local Dev Setup", "keywords": ["AI", "coding", "copilot", "assistant", "LLM"]},

    # --- Self-Serve > Learning Hub ---
    {"path": "self-serve-docs/learning-hub/index.md", "title": "Learning Hub", "section": "Self-Serve > Learning Hub", "keywords": ["learning", "tutorials", "guides", "education"]},
    {"path": "self-serve-docs/learning-hub/dbt-cheat-sheet.md", "title": "dbt Cheat Sheet", "section": "Self-Serve > Learning Hub", "keywords": ["dbt", "cheat sheet", "reference", "SQL", "commands"]},
    {"path": "self-serve-docs/learning-hub/data-quality.md", "title": "Data Quality Guide", "section": "Self-Serve > Learning Hub", "keywords": ["data quality", "testing", "validation", "best practices"]},
]

# ---------------------------------------------------------------------------
# GitHub raw content base URL
# ---------------------------------------------------------------------------

_GITHUB_RAW_BASE = "https://raw.githubusercontent.com/DalgoT4D/dalgo_docs/main"
_VALID_PATH_PREFIXES = ("docs/", "self-serve-docs/")

# ---------------------------------------------------------------------------
# In-memory cache for fetched doc content
# ---------------------------------------------------------------------------

_doc_cache: dict[str, tuple[str, float]] = {}  # path -> (content, timestamp)
_CACHE_MAX_SIZE = 50
_CACHE_TTL_SECONDS = 3600  # 1 hour

# Lazy-initialized httpx client for GitHub raw fetches
_http_client: httpx.AsyncClient | None = None


async def _get_http_client() -> httpx.AsyncClient:
    """Get or create the httpx client for GitHub raw fetches."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"Accept": "text/plain"},
        )
    return _http_client


def _get_cached(path: str) -> str | None:
    """Return cached content if present and not expired."""
    if path in _doc_cache:
        content, ts = _doc_cache[path]
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return content
        del _doc_cache[path]
    return None


def _put_cache(path: str, content: str) -> None:
    """Store content in cache, evicting oldest entries if over capacity."""
    if len(_doc_cache) >= _CACHE_MAX_SIZE:
        oldest_key = min(_doc_cache, key=lambda k: _doc_cache[k][1])
        del _doc_cache[oldest_key]
    _doc_cache[path] = (content, time.time())


def _find_doc_entry(path: str) -> dict | None:
    """Find a doc entry by path."""
    for entry in DOCS_INDEX:
        if entry["path"] == path:
            return entry
    return None


# ---------------------------------------------------------------------------
# Search scoring
# ---------------------------------------------------------------------------

def _score_entry(entry: dict, terms: list[str]) -> int:
    """Score a doc entry against search terms.

    Scoring: title match = 10, keyword match = 7, section match = 5, path match = 3.
    """
    score = 0
    title_lower = entry["title"].lower()
    section_lower = entry["section"].lower()
    path_lower = entry["path"].lower()
    keywords_lower = [kw.lower() for kw in entry["keywords"]]

    for term in terms:
        if term in title_lower:
            score += 10
        if any(term in kw for kw in keywords_lower):
            score += 7
        if term in section_lower:
            score += 5
        if term in path_lower:
            score += 3

    return score


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register(app: FastMCP, get_client):

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_list_docs() -> str:
        """List all Dalgo documentation pages grouped by section.

        Returns the complete documentation index organized by section.
        Use this to discover what documentation is available before
        searching or reading specific pages.

        No network calls — returns instantly from a built-in index.
        """
        sections: dict[str, list[dict]] = {}
        for entry in DOCS_INDEX:
            section = entry["section"]
            if section not in sections:
                sections[section] = []
            sections[section].append({
                "path": entry["path"],
                "title": entry["title"],
            })

        return json.dumps({
            "total_docs": len(DOCS_INDEX),
            "sections": sections,
        }, indent=2)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_search_docs(query: str) -> str:
        """Search Dalgo documentation by keyword.

        Searches across titles, sections, paths, and keywords from the
        built-in documentation index. Returns up to 10 most relevant results.

        No network calls — returns instantly from a built-in index.
        Use dalgo_get_doc(path) to read the full content of a result.

        Args:
            query: Search query (e.g. "dbt transform", "dashboard", "setup").
        """
        if not query or not query.strip():
            return json.dumps({"error": "Query cannot be empty. Provide a search term like 'dbt', 'dashboard', or 'setup'."})

        terms = [t.lower() for t in query.strip().split() if t]

        scored = []
        for entry in DOCS_INDEX:
            score = _score_entry(entry, terms)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:10]

        results = []
        for score, entry in top:
            results.append({
                "path": entry["path"],
                "title": entry["title"],
                "section": entry["section"],
                "relevance_score": score,
            })

        return json.dumps({
            "query": query,
            "total_results": len(scored),
            "showing": len(results),
            "results": results,
            "hint": "Use dalgo_get_doc(path='...') to read the full content of any result.",
        }, indent=2)

    @app.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def dalgo_get_doc(path: str) -> str:
        """Fetch and return the full content of a Dalgo documentation page.

        Fetches markdown content from the Dalgo docs GitHub repository.
        Results are cached in memory (1-hour TTL, 50-page cap).

        Args:
            path: Document path from the index (e.g. "docs/quickstart/index.md",
                  "self-serve-docs/learning-hub/dbt-cheat-sheet.md").
        """
        if not path or not path.strip():
            return json.dumps({"error": "Path cannot be empty. Use dalgo_search_docs or dalgo_list_docs to find valid paths."})

        path = path.strip()

        # Validate path prefix
        if not path.startswith(_VALID_PATH_PREFIXES):
            return json.dumps({
                "error": f"Invalid path: '{path}'. Path must start with 'docs/' or 'self-serve-docs/'.",
                "hint": "Use dalgo_search_docs or dalgo_list_docs to find valid paths.",
            })

        # Check cache first
        cached = _get_cached(path)
        if cached is not None:
            entry = _find_doc_entry(path)
            return json.dumps({
                "path": path,
                "title": entry["title"] if entry else path,
                "content": cached,
                "source": "cache",
            })

        # Fetch from GitHub
        url = f"{_GITHUB_RAW_BASE}/{path}"
        try:
            client = await _get_http_client()
            resp = await client.get(url)

            if resp.status_code == 404:
                return json.dumps({
                    "error": f"Document not found: '{path}'.",
                    "hint": "Use dalgo_search_docs or dalgo_list_docs to find valid paths.",
                })

            resp.raise_for_status()
            content = resp.text

            # Cache the result
            _put_cache(path, content)

            entry = _find_doc_entry(path)
            return json.dumps({
                "path": path,
                "title": entry["title"] if entry else path,
                "content": content,
                "source": "github",
            })

        except httpx.HTTPStatusError as e:
            # Return cached content if available despite error
            stale = _doc_cache.get(path)
            if stale:
                entry = _find_doc_entry(path)
                return json.dumps({
                    "path": path,
                    "title": entry["title"] if entry else path,
                    "content": stale[0],
                    "source": "stale_cache",
                    "warning": f"GitHub returned HTTP {e.response.status_code}. Showing cached content.",
                })
            return json.dumps({
                "error": f"Failed to fetch document: HTTP {e.response.status_code}",
                "path": path,
            })

        except httpx.HTTPError as e:
            stale = _doc_cache.get(path)
            if stale:
                entry = _find_doc_entry(path)
                return json.dumps({
                    "path": path,
                    "title": entry["title"] if entry else path,
                    "content": stale[0],
                    "source": "stale_cache",
                    "warning": f"GitHub fetch failed: {e}. Showing cached content.",
                })
            return json.dumps({
                "error": f"Failed to fetch document: {e}",
                "path": path,
            })

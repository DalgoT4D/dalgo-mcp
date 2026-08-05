# Example: toolset gating + read-only mode (FastMCP / Python)

Sketch for adding dbt/Grafana/GitHub-style gating to a FastMCP server like dalgo-mcp.
Illustrative — adapt to the real `config.py` / `server.py`.

## Config (env-driven)
```python
# config.py
self.enabled_modules = set(
    os.environ.get("DALGO_ENABLE_MODULES", "all").replace(" ", "").split(",")
)  # e.g. "warehouse,pipelines,charts" or "all"
self.read_only = os.environ.get("DALGO_READ_ONLY", "").lower() in ("1", "true", "yes")
```

## Gate at registration time
```python
# server.py
MODULES = {
    "organization": organization, "warehouse": warehouse, "pipelines": pipelines,
    "sources": sources, "connections": connections, "dashboards": dashboards,
    "charts": charts, "reports": reports, "transforms": transforms,
    "notifications": notifications, "docs": docs,
}
for name, module in MODULES.items():
    if config.enabled_modules == {"all"} or name in config.enabled_modules:
        module.register(app)
```

## Read-only filter using the annotations we already set
Every tool already declares intent via `ToolAnnotations`. Wrap `app.tool` so that, in
read-only mode, tools that aren't `readOnlyHint=True` are skipped:
```python
def make_tool(app, read_only: bool):
    real = app.tool
    def tool(*args, annotations=None, **kwargs):
        if read_only and annotations and annotations.readOnlyHint is not True:
            return lambda fn: fn          # skip registration; tool not exposed
        return real(*args, annotations=annotations, **kwargs)
    return tool
# app.tool = make_tool(app, config.read_only)  # install before module.register(app)
```

## Result
- `DALGO_ENABLE_MODULES=warehouse,charts,dashboards DALGO_READ_ONLY=1` → a small,
  safe, cheap analytics surface (see use-cases/read-only-analytics.md).
- Pairs with a `token-cost` CI gate so the enabled surface stays within budget.

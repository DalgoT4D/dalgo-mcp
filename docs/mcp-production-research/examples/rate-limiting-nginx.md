# Example: per-token rate limiting at the edge (nginx)

A hosted MCP amplifies load onto the backend, so cap request rate per caller. This is the
quickest win since dalgo-mcp already fronts the server with nginx.

## Limit by Authorization token
```nginx
# http {} block — a 10MB zone keyed by the bearer token, 5 req/s sustained.
map $http_authorization $mcp_client { default $http_authorization; }
limit_req_zone $mcp_client zone=mcp_per_token:10m rate=5r/s;
limit_req_status 429;

server {
    location / {
        limit_req zone=mcp_per_token burst=20 nodelay;  # allow short bursts
        proxy_pass http://127.0.0.1:8079;               # fix: match the app port!
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Notes
- Keying on the raw token is coarse; for per-**org** limits, throttle in the app where the
  org is resolved (`x-dalgo-org`) instead.
- Return `429` so clients back off; pair with quotas on expensive tools
  (chart-data, warehouse queries, dbt runs) in the app layer.
- Also wire backend throttling — `DDP_backend` already depends on the `ratelimit` lib but
  doesn't use it (production-readiness B5).
- **Fix the upstream port** while here: nginx currently proxies `:8081` but the app listens
  on `:8079` (production-readiness A8).

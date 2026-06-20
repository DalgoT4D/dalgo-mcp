# Case study: Stripe MCP

**Repo:** stripe/agent-toolkit · **Lang:** TypeScript ·
**Hosting:** `https://mcp.stripe.com` (OAuth) + local npx · **Stars:** ~1.6k · **License:** MIT

The reference example for **using the platform's own permission primitive as the MCP
permission model** — least privilege without bespoke MCP RBAC.

## Hosting & transport
- Local: `npx -y @stripe/mcp --api-key=YOUR_STRIPE_SECRET_KEY`.
- Remote: `https://mcp.stripe.com` with OAuth ("secure MCP client access via OAuth").

## Auth & least privilege ← the standout
- Permissions are controlled entirely by **Restricted API Keys (RAK, `rk_*`)** created
  in the Stripe dashboard. "Tool permissions are controlled by your Restricted API Key."
- Tool availability is implicitly scoped to whatever the key grants — no separate MCP
  permission layer to maintain.

## Tool surface
- Tools exposed in MCP format; scoping is via the RAK rather than CLI flags.

## What to copy for dalgo-mcp
- **Reuse Dalgo's existing role/permission model as the MCP permission model** — exactly
  what we do: the MCP acts as the user and inherits their backend RBAC. Stripe validates
  this is a legitimate, low-maintenance pattern (vs reinventing scopes in the MCP).
- For a hosted offering, consider a Dalgo equivalent of the RAK: a **scoped/restricted
  token** users mint for MCP use (ties to our production-readiness item B4).

# Rate Limit Recovery & Diagnostics

## Understanding 429 Responses

When Figma returns HTTP 429, the response includes diagnostic headers:

| Header | Purpose |
|--------|---------|
| `Retry-After` | Seconds to wait before retrying |
| `X-Figma-Plan-Tier` | The plan tier that triggered the limit |
| `X-Figma-Rate-Limit-Type` | Which rate limit was hit (per-user, per-file, etc.) |
| `X-Figma-Upgrade-Link` | URL to upgrade the plan |

## Common Causes

### 1. File owned by a Starter/free-plan user
Rate limits are tied to the **file owner's plan**, not the API token holder's plan. If the user accesses a file owned by someone on a Starter plan, that plan's very low limits apply.

**Fix:** Duplicate the Figma file into the user's own workspace so their plan's limits apply.

### 2. Burst pattern from large fetches
Fetching an entire file without `depth` or `nodeId` returns megabytes of data, then triggering dozens of image requests for frames with 50-200 children. This burst quickly exhausts rate limits.

**Fix:** Follow the metadata-first pipeline: `depth=2`, specific `nodeId`, images last.

### 3. View/Collab seat (not Dev/Full seat)
View and Collab seats get only **6 Tier-1 calls per month** — not per minute, per *month*. Any MCP usage will exhaust this almost immediately.

**Fix:** The user needs a Dev or Full seat on the Figma plan.

### 4. Plan upgrade propagation delay
After upgrading a Figma plan, new rate limits may take time to propagate. API calls during this window still hit old limits.

**Fix:** Wait 15-30 minutes after plan upgrade before resuming API usage.

## Recovery Strategy

1. **Immediate stop** — Do not make any more Figma API calls. Each failed retry can extend the lockout window.

2. **Diagnose** — Ask the user:
   - "What Figma plan are you on?" (Starter/Pro/Organization/Enterprise)
   - "Do you own this file or is it shared from someone else's workspace?"
   - "Have you recently changed your Figma plan?"

3. **Wait** — Respect the `Retry-After` duration. Typical lockouts:
   - Minor burst: 1-5 minutes
   - Sustained burst: 30-60 minutes
   - Severe abuse: up to 4-5 days (reported by community)

4. **Resume with minimal calls** — When retrying:
   - Use `depth=1` first to verify access is restored
   - Follow the metadata-first pipeline strictly
   - Space calls at least 5 seconds apart for safety

## Alternative Approaches When Rate-Limited

- **Work from screenshots**: Ask the user to screenshot the Figma design; use vision to generate code
- **Work from exported assets**: Ask the user to export SVGs/PNGs manually from Figma
- **Use Figma's Dev Mode**: Suggest the user copy CSS/layout values from Dev Mode manually
- **Cache previous responses**: If you've already fetched data earlier in the conversation, reuse it — don't re-fetch

## Community Solutions

- **[Figma-Context-MCP-Cached](https://github.com/pactortester/figma-context-mcp-cached)**: Community fork that adds local persistent caching with configurable TTL, significantly reducing redundant API calls
- **Figma's official MCP server**: Figma released their own Dev Mode MCP server with potentially different rate handling — see Figma's help center for setup instructions

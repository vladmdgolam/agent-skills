---
name: figma-context-mcp
description: "Expert guide for using the Figma Context MCP (Framelink) efficiently while avoiding 429 rate-limit errors. Activate when: (1) using Framelink Figma MCP tools (get_figma_data, download_figma_images), (2) fetching Figma designs for code generation, (3) user hits 429 rate limits from Figma API, (4) extracting design tokens or component data from Figma, (5) downloading Figma assets/images, (6) any design-to-code workflow involving Figma URLs. Covers metadata-first fetching, depth-limited node trees, batch image downloads, rate-limit diagnostics, and plan-tier awareness."
---

# Figma Context MCP

Expert guide for the [Figma Context MCP](https://github.com/GLips/Figma-Context-MCP) (also known as Framelink). Teaches efficient API usage patterns that prevent 429 rate-limit lockouts.

## Tools

| Tool | Purpose | API Tier |
|------|---------|----------|
| `get_figma_data` | Fetch file/node structure, layout, components | Tier 1 (most restricted) |
| `download_figma_images` | Export PNG/SVG renders of specific nodes | Tier 2-3 |

## Critical: Rate Limits

Figma enforces per-plan rate limits. Limits apply based on the **file owner's plan**, not yours:

| Tier | Starter | Pro | Org |
|------|---------|-----|-----|
| Tier 1 (files) | 10/min | 15/min | 20/min |
| Tier 2 (images) | 25/min | 50/min | 100/min |
| Tier 3 | 50/min | 100/min | 150/min |

View/Collab seats get only **6 Tier-1 calls/month**. If accessing files owned by someone on a Starter/free plan, their limits apply to you.

429 lockouts can last **4-5 days**. Prevention is essential.

## Workflow: Metadata-First Pipeline

**Never fetch everything upfront.** Adopt this pipeline to keep most jobs under 2-3 API calls and <500 KB:

### 1. Start with a targeted node, not the whole file

When a user provides a Figma URL like `figma.com/design/FILEKEY/Name?node-id=123-456`, always extract and pass the `nodeId`. Never fetch the entire file when a specific node is available.

```
get_figma_data(fileKey="ABC123", nodeId="123-456", depth=2)
```

### 2. Use minimal depth

Always set `depth` to limit tree traversal:
- **depth=1**: Top-level frame only (layout structure, component names)
- **depth=2**: Frame + direct children (usually sufficient for code generation)
- **depth=3**: Maximum recommended — only when nested auto-layouts require it

**Default if omitted: the API returns the ENTIRE subtree** — often megabytes for complex frames with 50-200+ children. This is the #1 cause of 429 errors.

### 3. Analyze locally before fetching more

After receiving the initial response:
- Identify which child nodes actually need detail (skip hidden, decorative, or library-referenced nodes)
- Extract design tokens (colors, spacing, typography) directly from the response — no extra calls needed
- Build your component structure from what you already have

### 4. Fetch deeper nodes only if necessary

If a specific child node needs more detail, fetch just that node:

```
get_figma_data(fileKey="ABC123", nodeId="child-node-id", depth=1)
```

### 5. Download images last, in small batches

Only request images for the **final deduplicated set** of visual assets you actually need:
- Deduplicate by `imageRef` — multiple nodes can reference the same fill image
- Batch into groups of **5-10 nodes** per call
- Use `pngScale=1` unless the user specifically needs @2x/@3x assets

```
download_figma_images(
  fileKey="ABC123",
  nodes=[{nodeId: "1:2", fileName: "hero", ...}],  # max 5-10 per call
  localPath="./assets",
  pngScale=1
)
```

## When You Hit a 429

See [references/rate-limit-recovery.md](references/rate-limit-recovery.md) for diagnostics and recovery steps.

Quick checklist:
1. **Stop all Figma API calls immediately** — additional calls extend the lockout
2. Check if the file is owned by a Starter/free-plan user (limits are per-owner)
3. If the user has a Pro/Org plan, suggest duplicating the file into their own workspace
4. Wait for `Retry-After` header duration before retrying
5. When retrying, use the minimal-depth pipeline above

## Common Patterns

### Design-to-code (single component)
1. `get_figma_data` with specific `nodeId` + `depth=2` (1 call)
2. Generate code from response — no image calls unless the component contains raster assets
3. If images needed: `download_figma_images` for just the raster fills (1 call)
4. **Total: 1-2 API calls**

### Design-to-code (full page)
1. `get_figma_data` with page `nodeId` + `depth=1` to get frame list (1 call)
2. Identify the 2-3 key frames that matter
3. `get_figma_data` for each key frame with `depth=2` (2-3 calls)
4. Extract tokens locally, download only unique raster assets (1 call)
5. **Total: 4-5 API calls**

### Extract design tokens only
1. `get_figma_data` with `nodeId` + `depth=2` (1 call)
2. Parse colors, typography, spacing from the response — no image calls needed
3. **Total: 1 API call**

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Omitting `depth` | Returns entire subtree (MB of data) | Always set `depth=2` or less |
| Omitting `nodeId` | Fetches entire file | Always extract `nodeId` from URL |
| Downloading all images upfront | Bursts of image requests hit Tier 2 limits | Download only final deduplicated set |
| Retrying on 429 | Extends lockout duration | Stop, wait for `Retry-After`, then resume with minimal calls |
| Fetching library components | Remote library nodes trigger extra API calls | Use local component data from initial response |

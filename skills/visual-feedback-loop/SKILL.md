---
name: visual-feedback-loop
description: "AI agent visual feedback loop for any web app. Use when iterating on visual code (UI, canvas, 3D, SVG, charts, animations) and you need to SEE the rendered result to evaluate quality. Covers: dev-screenshot API pattern (GET trigger → SSE → client capture → POST back → file saved), parameterized rendering, WebMCP tool registration, and console fallbacks. Activate on: 'take a screenshot', 'show me the render', 'visual QA', 'compare before/after', or any iterative visual work where the agent needs to inspect rendered output."
---

# Visual Feedback Loop

Capture and inspect visual output from a running web app during iterative development.

## How It Works

```
Agent (CLI)                     Server                            Browser
     |--- GET /api/dev-screenshot -->|--- SSE "capture" ----------->|
     |    ?param=value               |                              |-- capture canvas
     |                               |<-- POST { dataUrl } ---------|
     |                               | writes .screenshots/latest.png
     |<-- { ok, path } --------------|
```

Agent can't access the browser directly. Server relays: GET triggers → SSE notifies browser → browser captures and POSTs back → GET resolves. File saved to `.screenshots/latest.png`.

## Usage

Capture current view:
```bash
curl http://localhost:3000/api/dev-screenshot
```

Capture with params (app-specific — browser client interprets them):
```bash
curl 'http://localhost:3000/api/dev-screenshot?component=header&theme=dark'
curl 'http://localhost:3000/api/dev-screenshot?letter=б&depth=0.8'
```

Then always read the result:
```
Read .screenshots/latest.png
```

A/B comparison — capture variant A, read, capture variant B, read, compare.

Console fallback: `await window.__takeDevScreenshot()`

## Rules

1. **Always `Read .screenshots/latest.png` after capture.** Never assume the render is correct.
2. **Browser tab must be open** at the app URL. Timeout = no SSE connection = ask user to refresh.
3. **One request at a time.** Second GET returns 409. Wait for first to resolve (success/error/10s timeout).
4. **Errors return instantly**, not as timeouts. Client POSTs errors back: `{ ok: false, error: "..." }`.
5. **HMR breaks SSE.** After code changes, user must refresh the browser tab.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Timeout: browser did not respond | Open/refresh app in browser |
| 409: already in progress | Wait for timeout (10s) |
| Black/empty image | Refresh browser tab |
| Works once, then times out | HMR broke SSE — refresh tab |

See [references/errors.md](references/errors.md) for full error reference.

## Setup

To add this pattern to a new project, see [references/setup-nextjs.md](references/setup-nextjs.md) for complete Next.js implementation (API route, SSE listener, WebMCP registration).

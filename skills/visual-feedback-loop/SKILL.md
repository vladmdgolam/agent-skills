---
name: visual-feedback-loop
description: "AI agent visual feedback loop for any web app. Use when iterating on visual code (UI, canvas, 3D, SVG, charts, animations) and you need to SEE the rendered result to evaluate quality. Covers: dev-screenshot API pattern (GET trigger → SSE → client capture → POST back → file saved), parameterized offscreen rendering, WebMCP tool registration for Chrome Canary agents, and console fallbacks. Activate on: 'take a screenshot', 'show me the render', 'visual QA', 'compare before/after', or any iterative visual work where the agent needs to inspect rendered output."
---

# Visual Feedback Loop

Enable AI agents to capture and inspect visual output from a running web app during iterative development. Works with any renderer: canvas, SVG, DOM, 3D scenes, charts — anything the browser can display.

## Architecture

```
Agent (CLI/MCP)                 Web Server                        Browser Client
     |                               |                                 |
     |--- GET /api/dev-screenshot -->|                                 |
     |    ?myParam=value             | sets pending { resolve, params }|
     |                               |--- SSE data: {myParam} -------->|
     |                               |                                 |-- capture visual
     |                               |                                 |-- toDataURL / html2canvas / etc.
     |                               |<-- POST { dataUrl } ------------|
     |                               | writes .screenshots/latest.png  |
     |<-- { ok, path } --------------|                                 |
     |                               |                                 |
     | Read .screenshots/latest.png  |                                 |
```

The key insight: the agent can't access the browser directly, but can make HTTP requests. The server acts as a relay — agent triggers via GET, server notifies the browser via SSE, browser captures and POSTs back, GET resolves.

## Setup Guide (for any web app)

### 1. API Route (Next.js example)

Create `app/api/dev-screenshot/route.ts`:

```typescript
import { NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { join } from 'path'

interface PendingRequest {
  resolve: (value: { ok: boolean; path?: string; error?: string }) => void
  params?: Record<string, string>
}

let pending: PendingRequest | null = null
let sseNotify: ((params?: Record<string, string>) => void) | null = null
const TIMEOUT_MS = 10_000

export async function GET(req: Request) {
  if (process.env.NODE_ENV === 'production')
    return NextResponse.json({ error: 'Dev only' }, { status: 404 })

  const { searchParams } = new URL(req.url)

  // SSE stream for browser client
  if (searchParams.has('stream')) {
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(': connected\n\n'))
        sseNotify = (params) => {
          const payload = params ? JSON.stringify(params) : 'capture'
          controller.enqueue(encoder.encode(`data: ${payload}\n\n`))
        }
        if (pending) {
          const payload = pending.params ? JSON.stringify(pending.params) : 'capture'
          controller.enqueue(encoder.encode(`data: ${payload}\n\n`))
        }
      },
      cancel() { sseNotify = null },
    })
    return new Response(stream, {
      headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' },
    })
  }

  if (pending)
    return NextResponse.json({ error: 'Screenshot already in progress' }, { status: 409 })

  // Collect query params to pass to the client
  const params: Record<string, string> = {}
  searchParams.forEach((v, k) => { params[k] = v })
  const hasParams = Object.keys(params).length > 0

  const result = await new Promise<{ ok: boolean; path?: string; error?: string }>((resolve) => {
    pending = { resolve, params: hasParams ? params : undefined }
    sseNotify?.(hasParams ? params : undefined)
    setTimeout(() => {
      if (pending?.resolve === resolve) {
        pending = null
        resolve({ ok: false, error: 'Timeout: browser did not respond' })
      }
    }, TIMEOUT_MS)
  })

  return NextResponse.json(result)
}

export async function POST(req: Request) {
  if (process.env.NODE_ENV === 'production')
    return NextResponse.json({ error: 'Dev only' }, { status: 404 })

  const body = await req.json()

  // Client reports an error
  if (body.error) {
    const result = { ok: false, error: body.error }
    if (pending) { pending.resolve(result); pending = null }
    return NextResponse.json(result)
  }

  const { dataUrl } = body
  if (!dataUrl) return NextResponse.json({ error: 'Missing dataUrl' }, { status: 400 })

  const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, '')
  const dir = join(process.cwd(), '.screenshots')
  await mkdir(dir, { recursive: true })
  await writeFile(join(dir, 'latest.png'), Buffer.from(base64, 'base64'))

  const result = { ok: true, path: '.screenshots/latest.png' }
  if (pending) { pending.resolve(result); pending = null }
  return NextResponse.json(result)
}
```

### 2. Client SSE Listener

In your main client component:

```typescript
useEffect(() => {
  if (process.env.NODE_ENV === 'production') return
  const es = new EventSource('/api/dev-screenshot?stream')

  es.onmessage = async (event) => {
    let dataUrl: string | null = null

    if (event.data === 'capture') {
      // Default: capture whatever is on screen
      dataUrl = myCanvas.toDataURL('image/png')  // or html2canvas, etc.
    } else {
      try {
        const params = JSON.parse(event.data)
        // Use params to do custom/parameterized renders
        dataUrl = await myCustomRenderer(params)
      } catch (err) {
        // Report error back so agent GET resolves with message
        fetch('/api/dev-screenshot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: String(err.message || err) }),
        }).catch(() => {})
        return
      }
    }

    if (dataUrl) {
      fetch('/api/dev-screenshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataUrl }),
      }).catch(() => {})
    }
  }

  return () => es.close()
}, [])
```

### 3. Gitignore

Add `.screenshots/` to `.gitignore`.

### 4. WebMCP (optional, Chrome Canary 146+)

Register tools via `webmcp-kit` so agents with `navigator.modelContext` can call them directly.

**Requirement for Claude Code:** WebMCP tools run in the browser, so Claude Code needs the **Claude in Chrome** browser extension to invoke them (via `mcp__claude-in-chrome__javascript_tool`). Without the extension, WebMCP tools are registered but unreachable from the CLI — use the curl-based API instead, which works without any browser extension.

```typescript
import { defineTool } from 'webmcp-kit'
import { z } from 'zod'

const screenshotTool = defineTool({
  name: 'takeScreenshot',
  description: 'Capture the current visual state',
  inputSchema: z.object({}),
  execute: async () => {
    const dataUrl = myCanvas.toDataURL('image/png')
    // Also save server-side
    fetch('/api/dev-screenshot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataUrl }),
    }).catch(() => {})
    const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, '')
    return { content: [{ type: 'image', data: base64, mimeType: 'image/png' }] }
  },
})
screenshotTool.register()
```

## Critical Rules

### 1. Always Read the file after capture
The API saves to `.screenshots/latest.png`. Use the `Read` tool — it supports images natively. Never assume the render looks correct without checking.

### 2. Browser tab must be open
The capture requires a browser client connected via SSE. If the GET times out, the user needs to open/refresh the app.

### 3. One request at a time
A second GET while one is pending returns 409. Wait for the first to resolve.

### 4. Errors come back through the API
If the client-side render throws, POST the error back. The GET resolves immediately with `{ ok: false, error: "..." }` instead of timing out for 10s.

### 5. HMR breaks SSE
Hot module replacement disconnects the EventSource. After code changes, the user must refresh the browser tab.

## Usage

### Basic capture

```bash
curl http://localhost:3000/api/dev-screenshot
```
Then: `Read .screenshots/latest.png`

### Parameterized capture

Pass any query params — they arrive as JSON in the SSE message for the client to interpret:

```bash
# Your app decides what these params mean
curl 'http://localhost:3000/api/dev-screenshot?component=header&theme=dark'
curl 'http://localhost:3000/api/dev-screenshot?letter=б&depth=0.8'
curl 'http://localhost:3000/api/dev-screenshot?chartType=bar&data=sample'
```

### A/B comparison workflow

```bash
# Capture variant A
curl 'http://localhost:3000/api/dev-screenshot?variant=a'
# Read .screenshots/latest.png — note observations

# Capture variant B
curl 'http://localhost:3000/api/dev-screenshot?variant=b'
# Read .screenshots/latest.png — compare
```

### Console fallback

Expose a window function for manual use or Chrome MCP:

```javascript
await window.__takeDevScreenshot()
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Timeout: browser did not respond | No browser tab or SSE disconnected | Open/refresh the app |
| 409: already in progress | Previous request pending | Wait for timeout (10s) |
| Black/empty image | Canvas context lost | Refresh browser tab |
| Works once, then times out | HMR broke SSE | Refresh browser tab |
| `{ ok: false, error: "..." }` | Client-side render error | Read the error message |

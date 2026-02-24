# Setup: Next.js Implementation

Copy-paste reference for implementing the visual feedback loop in a Next.js app router project.

## 1. API Route (`app/api/dev-screenshot/route.ts`)

```typescript
import { NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { join } from 'path'

// Store on globalThis so state survives HMR module reloads (Prisma pattern)
interface PendingRequest {
  resolve: (value: { ok: boolean; path?: string; error?: string }) => void
  params?: Record<string, string>
}
interface DevScreenshotState {
  pending: PendingRequest | null
  sseNotify: ((params?: Record<string, string>) => void) | null
}
const g = globalThis as unknown as { __devScreenshot?: DevScreenshotState }
if (!g.__devScreenshot) g.__devScreenshot = { pending: null, sseNotify: null }
const state = g.__devScreenshot

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
        state.sseNotify = (params) => {
          const payload = params ? JSON.stringify(params) : 'capture'
          controller.enqueue(encoder.encode(`data: ${payload}\n\n`))
        }
        if (state.pending) {
          const payload = state.pending.params ? JSON.stringify(state.pending.params) : 'capture'
          controller.enqueue(encoder.encode(`data: ${payload}\n\n`))
        }
      },
      cancel() { state.sseNotify = null },
    })
    return new Response(stream, {
      headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' },
    })
  }

  if (state.pending)
    return NextResponse.json({ error: 'Screenshot already in progress' }, { status: 409 })

  const params: Record<string, string> = {}
  searchParams.forEach((v, k) => { params[k] = v })
  const hasParams = Object.keys(params).length > 0

  const result = await new Promise<{ ok: boolean; path?: string; error?: string }>((resolve) => {
    state.pending = { resolve, params: hasParams ? params : undefined }
    state.sseNotify?.(hasParams ? params : undefined)
    setTimeout(() => {
      if (state.pending?.resolve === resolve) {
        state.pending = null
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

  if (body.error) {
    const result = { ok: false, error: body.error }
    if (state.pending) { state.pending.resolve(result); state.pending = null }
    return NextResponse.json(result)
  }

  const { dataUrl } = body
  if (!dataUrl) return NextResponse.json({ error: 'Missing dataUrl' }, { status: 400 })

  const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, '')
  const dir = join(process.cwd(), '.screenshots')
  await mkdir(dir, { recursive: true })
  await writeFile(join(dir, 'latest.png'), Buffer.from(base64, 'base64'))

  const result = { ok: true, path: '.screenshots/latest.png' }
  if (state.pending) { state.pending.resolve(result); state.pending = null }
  return NextResponse.json(result)
}
```

## 2. Client SSE Listener (in main component)

```typescript
useEffect(() => {
  if (process.env.NODE_ENV === 'production') return
  const es = new EventSource('/api/dev-screenshot?stream')

  es.onmessage = async (event) => {
    let dataUrl: string | null = null

    if (event.data === 'capture') {
      dataUrl = myCanvas.toDataURL('image/png')
    } else {
      try {
        const params = JSON.parse(event.data)
        dataUrl = await myCustomRenderer(params)
      } catch (err) {
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

  // Expose console fallback
  ;(window as any).__takeDevScreenshot = async () => {
    const dataUrl = myCanvas.toDataURL('image/png')
    const res = await fetch('/api/dev-screenshot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataUrl }),
    })
    return res.json()
  }

  return () => {
    es.close()
    delete (window as any).__takeDevScreenshot
  }
}, [])
```

## 3. Gitignore

Add `.screenshots/` to `.gitignore`.

## 4. WebMCP (optional, Chrome Canary 146+)

Register tools via `webmcp-kit` for agents with `navigator.modelContext`:

```bash
npm install -D webmcp-kit zod
```

```typescript
import { defineTool } from 'webmcp-kit'
import { z } from 'zod'

const screenshotTool = defineTool({
  name: 'takeScreenshot',
  description: 'Capture the current visual state',
  inputSchema: z.object({}),
  execute: async () => {
    const dataUrl = myCanvas.toDataURL('image/png')
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

**Note:** Claude Code needs the **Claude in Chrome** browser extension to invoke WebMCP tools. Without it, use the curl-based API instead.

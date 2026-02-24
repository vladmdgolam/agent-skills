# Error Reference

## API Errors

| HTTP Status | Response | Cause | Fix |
|-------------|----------|-------|-----|
| 200 | `{ ok: false, error: "Timeout: browser did not respond" }` | No browser connected via SSE within 10s | Open/refresh the app in browser |
| 200 | `{ ok: false, error: "..." }` | Client-side render error (custom message) | Read the error — app-specific issue |
| 404 | `{ error: "Dev only" }` | Running in production mode | Use dev server |
| 409 | `{ error: "Screenshot already in progress" }` | Previous GET still pending | Wait for timeout or success |
| 400 | `{ error: "Missing dataUrl" }` | POST body missing dataUrl | Internal error — client code bug |

## SSE Connection Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| EventSource connection failed | Dev server not running | Start dev server |
| SSE works then stops | HMR/code change disconnected it | Refresh browser tab |
| Multiple SSE connections | Multiple tabs open | Close extra tabs (only one client needed) |

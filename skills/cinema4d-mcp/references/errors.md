# C4D MCP Error Reference

## Python API Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `'c4d.Vector' object is not iterable` | Can't do `list(vector)` | Use `def vec(v): return [v.x, v.y, v.z]` |
| `module 'c4d' has no attribute 'SCENEFILTER_ANIMATION'` | Constant not in this C4D build | Use `hasattr()` check, fallback to `SCENEFILTER_OBJECTS` etc. |
| `module 'c4d' has no attribute 'MG_POLY_MODE_CLONE_COUNT'` | Wrong attribute name | Use `c4d.MG_RADIAL_COUNT` for radial cloners |
| `module 'c4d' has no attribute 'MG_RADIAL_START'` | Attribute doesn't exist | Skip or `try/except` |
| `module 'c4d' has no attribute 'MG_OBJECT_ITERATION'` | Wrong attribute name | Skip or `try/except` |
| `Execution on main thread timed out after 15s` | Script too slow or MoGraph heavy | Simplify, reduce loops, split into chunks |
| `Parameter value accessible (object unknown in Python)` | RS node container IDs aren't plain Python types | Skip with `try/except` when iterating data containers |
| `'c4d.Material' object has no attribute 'GetGUID'` | Materials don't have `GetGUID` | Use `mat.FindUniqueID(c4d.MAXON_CREATOR_ID)` or `mat.GetUniqueID()` |

## MCP Tool Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `list_objects` validation error (expected string, got dict) | MCP schema mismatch (fixed in some forks) | Update server, or use `execute_python_script` to traverse hierarchy |
| `load_scene` error (`takes 1 positional argument but N were given`) | Plugin bug: path unpacked as args | Load scene manually or via `execute_python_script` + `LoadDocument` |
| `render_preview` validation error (expected string, got dict) | Same schema mismatch (fixed in some forks) | Update server, or skip preview |
| Frame sampling returns static values | Missing pass evaluation | Call `ExecutePasses` after `SetTime` |
| Jumping to frame X gives wrong positions | Stateful MoGraph evaluation | Step sequentially from start frame |

## Security Restrictions

Banned keywords in `execute_python_script`: `import os`, `os.system`, `subprocess`, `exec(`, `eval(`.

Keep scripts within the allowed C4D API surface (`c4d`, `c4d.modules.mograph`, `json`, `math`).

## Key Parameter IDs

| ID | Location | Meaning |
|----|----------|---------|
| `1041671` | Materials, Effectors | Emission color |
| `1100` | Random Effectors | Seed value |
| `1010` | Effectors | Position/rotation range |
| `1012` | Random.rot | Rotation range (radians) |

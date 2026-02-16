---
name: cinema4d-mcp
description: "Cinema 4D MCP expert for extracting scene data, writing C4D Python scripts, and controlling Cinema 4D through MCP tools. Activate when: (1) using cinema4d MCP tools (get_scene_info, list_objects, execute_python_script, add_primitive, etc.), (2) writing Python scripts for Cinema 4D extraction or manipulation, (3) working with MoGraph cloners/effectors/fields, (4) baking animation data from C4D scenes, (5) debugging C4D Python API errors, (6) extracting Redshift material or camera data. Covers critical gotchas, correct extraction patterns, MoGraph baking, timeline evaluation, API compatibility, and known failure modes."
---

# Cinema 4D MCP

## Tool Selection

Use **structured MCP tools** (`get_scene_info`, `list_objects`, `add_primitive`, etc.) for simple operations.

Use **`execute_python_script`** as the primary path for non-trivial extraction. It avoids wrapper/schema mismatches, gives full `c4d` API access, and allows proper frame stepping control.

## Health Check (Always First)

1. `get_scene_info` - verify connection
2. `execute_python_script` with `print("ok")` - verify Python works
3. If both work, extraction is possible even when other tools are broken

## Critical Rules

### 1. World vs Local Coordinates
`GeGetMoData()` returns cloner-local positions. Always apply global matrix:
```python
mg = cloner.GetMg()
world_pos = mg * m.off  # LOCAL -> WORLD
```
Missing this shifts everything by the cloner's global offset.

### 2. Visibility Constants Are Swapped
- `MODE_OFF = 1` (not 0!)
- `MODE_ON = 0` (not 1!)
- `MODE_UNDEF = 2` (default/inherit)

Always use `c4d.MODE_OFF` / `c4d.MODE_ON`, never raw integers.

### 3. Sequential Frame Stepping
MoGraph effectors accumulate state. Iterate 0->N sequentially:
```python
for frame in range(start, end + 1):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
    # NOW read data
```
Never jump to arbitrary frames. Never skip `ExecutePasses`.

### 4. Split Heavy Bakes
MCP scripts timeout on large frame ranges (~20-30s default, some forks 60s). Bake in chunks (e.g., frames 0-200, then 200-400), combine afterward. Log progress with `print()`.

### 5. Iterative Traversal Only
Use stack-based traversal. Recursive traversal hits Python recursion limits:
```python
def find_obj(name):
    stack = [doc.GetFirstObject()]
    while stack:
        obj = stack.pop()
        while obj:
            if obj.GetName() == name:
                return obj
            if obj.GetDown():
                stack.append(obj.GetDown())
            obj = obj.GetNext()
    return None
```

### 6. API Version Compatibility
Constants differ between C4D versions. Use defensive checks:
```python
if hasattr(c4d, "SCENEFILTER_ANIMATION"):
    ...
```

### 7. Check Render Visibility
Objects can be disabled via traffic lights (`GetRenderMode()`), RS Object tags, parent hierarchy inheritance, or Takes system.

## MoGraph Extraction Pattern

```python
import c4d
from c4d.modules import mograph as mo

def vec(v):
    return [float(v.x), float(v.y), float(v.z)]

cloner = find_obj("ClonerName")
mg = cloner.GetMg()

for frame in range(start, end + 1, step):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
    md = mo.GeGetMoData(cloner)
    matrices = md.GetArray(c4d.MODATA_MATRIX)
    for i, m in enumerate(matrices):
        world_pos = mg * m.off
        scale = (m.v1.GetLength() + m.v2.GetLength() + m.v3.GetLength()) / 3.0
```

## Animation Track Discovery

```python
for t in obj.GetCTracks():
    did = t.GetDescriptionID()
    ids = [int(did[i].id) for i in range(did.GetDepth())]
    curve = t.GetCurve()
    keys = []
    if curve:
        for k in range(curve.GetKeyCount()):
            key = curve.GetKey(k)
            keys.append({"frame": key.GetTime().GetFrame(fps), "value": float(key.GetValue())})
```

## Cloner Mode Constants

```
c4d.ID_MG_MOTIONGENERATOR_MODE: 0=Grid, 1=Linear, 2=Radial, 3=Object, 4=Honeycomb
c4d.MG_GRID_MODE: 0=Endpoint (total span), 1=Per Step (spacing)
```

## Redshift Availability

**Accessible without RS:** hierarchy, transforms, keyframes, MoGraph clone data, C4D native shaders.

**NOT accessible without RS:** node graph internals, RS lights/environment, RS API IDs.

## Known Errors & Workarounds

See [references/errors.md](references/errors.md) for complete Python API and MCP tool error tables.

## Raw Socket Fallback

If MCP tools fail but C4D socket server is alive (`127.0.0.1:5555`):
```python
import json, socket
s = socket.create_connection(("127.0.0.1", 5555), timeout=5)
s.sendall((json.dumps({"command": "get_scene_info"}) + "\n").encode())
```

## Data Output

- Save to JSON with metadata (scene name, fps, frame range, sampling step)
- `json.dumps()` + `print()` for small results, `/tmp/*.json` for large data
- Keep both raw extraction and derived model

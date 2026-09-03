---
name: cinema4d-mcp
description: "Cinema 4D MCP expert for extracting scene data, writing C4D Python scripts, and controlling Cinema 4D through MCP tools. Activate when: (1) using cinema4d MCP tools (get_scene_info, list_objects, execute_python_script, add_primitive, etc.), (2) writing Python scripts for Cinema 4D extraction or manipulation, (3) working with MoGraph cloners/effectors/fields, (4) baking animation data from C4D scenes, (5) debugging C4D Python API errors, (6) extracting Redshift material or camera data. Covers critical gotchas, correct extraction patterns, MoGraph baking, timeline evaluation, API compatibility, and known failure modes."
---

# Cinema 4D MCP

## Source of Truth

This skill targets Vlad's fork of Cinema 4D MCP: [vladmdgolam/cinema4d-mcp](https://github.com/vladmdgolam/cinema4d-mcp).

Relevant fork additions:
- `inspect_redshift_materials` - read-only Redshift inspector for assignments, preview-derived colors, readable description/container fields, and best-effort graph probing. **Note:** this tool may skip RS materials as `not_redshift_like` (type 5703) — use `execute_python_script` with the `maxon` API for full RS node graph extraction instead (see Redshift Material Extraction section).
- Duplicate-safe material targeting - the inspector accepts `material_index` and returns stable scene indices plus duplicate-name hints when names collide.
- Redshift GraphView fallback - when node-space access fails but `import redshift` works, the inspector falls back to `redshift.GetRSMaterialNodeMaster(...)` and reports GraphView nodes plus resolved connections.
- The loaded C4D plugin may lag behind the repo copy. After plugin edits, restart Cinema 4D before trusting new tool behavior.

## Tool Selection

Use **structured MCP tools** (`get_scene_info`, `list_objects`, `add_primitive`, etc.) for simple operations.

Use **`execute_python_script`** as the primary path for non-trivial extraction. It avoids wrapper/schema mismatches, gives full `c4d` + `maxon` API access, and allows proper frame stepping control. This is especially important for **Redshift material extraction** — the `maxon` node-space API gives full access to RS node graphs, which other tools may miss.

Use **`inspect_redshift_materials`** as a quick overview of material assignments and preview colors, but be aware it may skip RS materials as `not_redshift_like` if they use type 5703 wrappers. For full RS node graph data, use `execute_python_script` with the `maxon` API pattern documented in the Redshift section.

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

## Complete Animation Bake Workflow

This is the authoritative end-to-end procedure. Follow it in order — each step gates the next.

### Step 1: Health Check
```python
# Tool call: get_scene_info
# Then:
import c4d
print(doc.GetDocumentName(), doc.GetFps(), doc.GetMaxTime().GetFrame(doc.GetFps()))
```
Confirm: scene name resolves, fps is correct (typically 24/25/30), max frame is the expected end frame.

### Step 2: Discover Animation Tracks
Before baking, confirm the cloner actually has animated effectors:
```python
import c4d

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

fps = doc.GetFps()
cloner = find_obj("MyClonerName")  # replace with actual name

# Check direct tracks on cloner
for t in cloner.GetCTracks():
    did = t.GetDescriptionID()
    ids = [int(did[i].id) for i in range(did.GetDepth())]
    curve = t.GetCurve()
    key_count = curve.GetKeyCount() if curve else 0
    print(f"Track IDs: {ids}, keys: {key_count}")

# Check effector children for their own tracks
child = cloner.GetDown()
while child:
    for t in child.GetCTracks():
        did = t.GetDescriptionID()
        ids = [int(did[i].id) for i in range(did.GetDepth())]
        print(f"  Effector '{child.GetName()}' track IDs: {ids}")
    child = child.GetNext()
```
If no tracks appear, the animation may be driven by fields or expressions — proceed to bake anyway; `ExecutePasses` will resolve those.

### Step 3: Bake MoGraph (Sequential Frame Stepping)
```python
import c4d
from c4d.modules import mograph as mo
import json

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

def vec(v):
    return [float(v.x), float(v.y), float(v.z)]

fps = doc.GetFps()
start = 0
end = int(doc.GetMaxTime().GetFrame(fps))
cloner = find_obj("MyClonerName")
mg = cloner.GetMg()  # global matrix for LOCAL->WORLD

frames_data = {}

for frame in range(start, end + 1):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)

    md = mo.GeGetMoData(cloner)
    if md is None:
        print(f"Frame {frame}: no MoData")
        continue

    matrices = md.GetArray(c4d.MODATA_MATRIX)
    clone_indices = md.GetArray(c4d.MODATA_CLONE)

    frame_clones = []
    for i, m in enumerate(matrices):
        world_pos = mg * m.off
        scale = (m.v1.GetLength() + m.v2.GetLength() + m.v3.GetLength()) / 3.0
        frame_clones.append({
            "index": i,
            "position": vec(world_pos),
            "scale": float(scale),
            "clone_index": float(clone_indices[i]) if clone_indices else None
        })

    frames_data[frame] = frame_clones
    if frame % 50 == 0:
        print(f"Baked frame {frame}/{end}")

print(f"Done. Total frames baked: {len(frames_data)}")
```

### Step 4: Extract Keyframes (Optional — for sparse data)
If you need keyframe-only data rather than every-frame bake:
```python
import c4d

fps = doc.GetFps()
obj = find_obj("MyObject")

keyframe_data = {}
for t in obj.GetCTracks():
    did = t.GetDescriptionID()
    ids = [int(did[i].id) for i in range(did.GetDepth())]
    curve = t.GetCurve()
    if not curve:
        continue
    keys = []
    for k in range(curve.GetKeyCount()):
        key = curve.GetKey(k)
        keys.append({
            "frame": key.GetTime().GetFrame(fps),
            "value": float(key.GetValue())
        })
    keyframe_data[str(ids)] = keys

print(json.dumps(keyframe_data))
```

### Step 5: Export JSON
```python
import json

output = {
    "scene": doc.GetDocumentName(),
    "fps": fps,
    "start_frame": start,
    "end_frame": end,
    "clone_count": len(frames_data.get(start, [])),
    "frames": frames_data
}

import tempfile, os
export_path = os.path.join(tempfile.gettempdir(), "mograph_export.json")
with open(export_path, "w") as f:
    json.dump(output, f)

print(f"Exported {len(frames_data)} frames to {export_path}")
```

### Step 6: Validate
Run this after export to catch silent errors before handing data downstream:
```python
import json, math

with open(export_path) as f:
    data = json.load(f)

fps = data["fps"]
start = data["start_frame"]
end = data["end_frame"]
expected_frames = end - start + 1
actual_frames = len(data["frames"])

errors = []

if actual_frames != expected_frames:
    errors.append(f"Frame count mismatch: expected {expected_frames}, got {actual_frames}")

nan_count = 0
for frame_key, clones in data["frames"].items():
    for clone in clones:
        for coord in clone["position"]:
            if math.isnan(coord) or math.isinf(coord):
                nan_count += 1
        if clone.get("clone_index") is not None:
            if not (0.0 <= clone["clone_index"] <= 1.0):
                errors.append(f"Frame {frame_key} clone {clone['index']}: clone_index out of range: {clone['clone_index']}")

if nan_count > 0:
    errors.append(f"NaN/Inf found in {nan_count} position coordinates")

if errors:
    for e in errors:
        print("ERROR:", e)
else:
    print("Validation passed.")
    print(f"  Frames: {actual_frames}, Clones per frame: {data['clone_count']}")
```

## Validation Checklist

### Before Baking
- [ ] Frame range set in scene (`doc.GetMaxTime()` returns expected end frame)
- [ ] All effectors active (check visibility traffic lights and Tags)
- [ ] No interfering Takes (`doc.GetTakeData().GetCurrentTake()` is the correct take)
- [ ] Test on small range (frames 0-10) first — confirm clone count and positions look right before running full bake

### After Baking
- [ ] Total frame count equals `end - start + 1` (no off-by-one, no gaps)
- [ ] No NaN or Inf values in position coordinates
- [ ] Clone indices are in range 0.0–1.0 (if using `MODATA_CLONE`)
- [ ] World positions make sense — spot-check frame 0 and last frame against viewport

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

## Redshift Material Extraction

**RS node graphs ARE accessible** via the `maxon` Python API when Redshift is installed. The `inspect_redshift_materials` MCP tool may report materials as `not_redshift_like` (type 5703), but the node graph is still readable through the maxon node-space API.

### Primary Path: maxon Node-Space API (Proven Working)

RS materials use node space `com.redshift3d.redshift4c4d.class.nodespace`. Access via:

```python
import c4d
import maxon

RS_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

mat = doc.GetMaterials()[0]
nm = mat.GetNodeMaterialReference()
graph = nm.GetGraph(RS_NODESPACE)  # returns NodesGraphModelRef

# Traverse ALL nodes and ports:
root = graph.GetRoot()
inner = root.GetInnerNodes(maxon.NODE_KIND.ALL_MASK, False)

for n in inner:
    kind = n.GetKind()
    nid = str(n.GetId())

    if kind == 1:  # NODE — e.g. standardmaterial, incandescent, texturesampler
        print(f"Node: {nid}")
    elif kind == 8:  # INPORT — readable port with value
        short_name = nid.split('.')[-1]
        try:
            val = n.GetDefaultValue()
            if val is not None:
                print(f"  {short_name} = {val}")
        except:
            pass
```

**What this gives you:**
- All shader nodes (RS Standard Material, Incandescent, MaxonNoise, TextureSampler, RSRamp, RSColorCorrection, etc.)
- All input port values (colors, intensities, roughness, refraction weight, texture paths, noise params, ramp stops, etc.)
- `GetDefaultValue()` and `GetEffectivePortValue()` both work

**⚠ API drift (observed C4D 2024.2, 2026-08):** on some builds
`GetDefaultValue()` returns `None` for every port (customized or not) and
`GetEffectivePortValue()` does not exist on the GraphNode wrapper; the
graph STRUCTURE still enumerates fine via `GetInnerNodes(ALL_MASK)`.
Also `dir(port)` can raise "expected generic datatype capsule". When
values are unreadable, fall back to empirical extraction: render one
small frame (batch queue, e.g. 295x640 single frame ≈ 7 min RS) and
measure colors from pixels, or use the emission-probe pattern for field
values. That answered "which node carries the preset color" faster than
fighting the API.

**Instead: try binary extraction first.** The values ARE in the .c4d
binary and ARE readable via direct parsing — see
`~/cinema4d-mcp/scripts/extract_rs_binary.py` (standalone Python, no
C4D/RS license needed). Handles float64 and int32 scalar port values
in both C4D serialization formats (`10_1c` and `10_1f`). This is
faster, cheaper, and more reliable than the API.

```bash
python3 ~/cinema4d-mcp/scripts/extract_rs_binary.py scene.c4d
```

### Binary format decoded

Two serialization formats exist in .c4d files:

| Format | Header marker | Value marker | Found in |
|--------|--------------|--------------|----------|
| Newer | `10 1c 10 1c` (16 bytes) | `10 21` + type | Probe/bake files |
| Older | `10 1f 10 1f` (16 bytes) | `10 24` + type | Scene `_002.c4d` files |

Type bytes: `0x11` = float64 (IEEE 754 LE, 8 bytes), `0x12` = int32
(LE, 4 bytes). After the value: 2-byte big-endian uint16 = next port
path length (used as alignment validation). For `vec3`/color values:
type byte `0x22` → 3 × float64 RGB.

A third format (`10 20 10 20`, 16-byte header + `10 28` value marker)
encodes **node graph connections** (wiring between ports), not port
values — still being RE'd.

### What can be extracted

| Category | Status | Notes |
|----------|--------|-------|
| Scalar float64/int32 | ✅ Fully working | brightness, contrast, animation_speed, coord_scale, seed, refr_weight, refl_roughness, rotate, etc. |
| Ramp color stops | ✅ Decoded | type `0x22` vec3 color + position + interpolation + bias per stop |
| `coord_offset` | ⚠️ Always default | (0, 0, ~0.054) in all tested scenes — not explicitly stored |
| Material colors | ❌ Not direct values | `base_color` is a node connection, not a stored RGB; use `GetPreview(0)` or emission probes |
| Connection wiring | ❌ 10_20 format | Serializes which node output wires to which node input |

### Extracted values across all 4 scene files

See `docs/c4d-binary-reverse-engineering.md` in music-shader for the
full table. Key shared values:
- `brightness`: 0.054 (all scenes)
- `contrast`: 0.428 or 0.238 (per noise node)
- `animation_speed`: 2.85 or 1.1 (two noise nodes in Skriptonit)
- `coord_scale_global`: ~26-27 (all scenes)
- `refr_weight`: 0.581, `refl_roughness`: 0.336
- `level` (color correction): 1.0-1.5

For color/vec3/ramp types the binary reader doesn't handle yet, use the
emission-probe method or `GetPreview(0)` (cached thumbnail) for coarse
color data.

**To find specific node types**, use:
```python
result = maxon.GraphModelHelper.FindNodesByAssetId(
    graph, "com.redshift3d.redshift4c4d.nodes.core.standardmaterial", True
)
```

### Secondary Path: Legacy GraphView (Older RS Materials)

For older RS shader-network materials where `GetGraph()` returns None:
```python
import redshift
gv = redshift.GetRSMaterialNodeMaster(mat)
if gv:
    root = gv.GetRoot()
    child = root.GetDown()
    while child:
        print(f"Node: {child.GetName()} op={child.GetOperatorID()}")
        child = child.GetNext()
```

### Fallback: Preview Bitmap Sampling

When neither path works (RS not installed), sample preview bitmaps for approximate colors:
```python
bmp = mat.GetPreview(0)
if bmp:
    r, g, b = bmp.GetPixel(bmp.GetBw() // 2, bmp.GetBh() // 2)
```

**⚠ Also works when the Redshift LICENSE HAS LAPSED, not just when RS is
absent.** `GetPreview()` returns a bitmap C4D already cached from the last
render/interactive preview — it does not trigger a new render, so it is
unaffected by a license check that blocks `RenderDocument()` / batch / PV
rendering outright. Confirmed live (2026-08): with the license lapsed,
`CallCommand(12099)` (PV render) hung indefinitely with
`CHECKISRUNNING_EXTERNALRENDERING` stuck at `1`, while `mat.GetPreview(0)`
on the same document returned instantly with real (non-placeholder) pixel
data. The near-instant response itself is the tell that you're reading a
cache, not paying for a render — if a "preview" call takes seconds, that's
a different code path. When a license lapses mid-project, this is the
fastest way to keep pulling *some* per-material data (coarse average
color via a 3x3 or denser pixel-grid sample) without needing the license
back — see the OOM/hang troubleshooting row below for the render-side
symptoms this pairs with.

### Node Kind Constants

| Kind | Value | Meaning |
|------|-------|---------|
| NODE | 1 | Shader node (standardmaterial, incandescent, etc.) |
| INPUTS | 2 | Input ports container |
| OUTPUTS | 4 | Output ports container |
| INPORT | 8 | Individual input port (has value) |
| OUTPORT | 16 | Individual output port |

### Duplicate Names

If the scene contains multiple materials with the same visible name, use `material_index` instead of `material_name` with the MCP inspector.

## Clone-to-Material Mapping

Use `MODATA_CLONE` array from `GeGetMoData()` to get normalized clone indices (0.0–1.0 mapped to child objects):
```python
md = mo.GeGetMoData(cloner)
clone_indices = md.GetArray(c4d.MODATA_CLONE)  # float array, 0.0–1.0
```
These values map to the cloner's child object cycle. **Verify visually** — don't assume the cycle matches hierarchy order.

## Examples

### Example 1: Extract MoGraph Cloner Animation to JSON for Three.js

**Scenario:** A cloner with 50 spheres driven by a Random effector needs to be exported as per-frame position data for playback in Three.js.

**Step-by-step:**

1. Health check — confirm `get_scene_info` returns scene name and `doc.GetFps()` returns 30.

2. Identify the cloner name from `list_objects` or `get_scene_info`. Assume it is `"SphereCloner"`.

3. Run a small test bake (frames 0-10) to confirm data shape:
```python
import c4d
from c4d.modules import mograph as mo

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

fps = doc.GetFps()
cloner = find_obj("SphereCloner")
mg = cloner.GetMg()

for frame in range(0, 11):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
    md = mo.GeGetMoData(cloner)
    matrices = md.GetArray(c4d.MODATA_MATRIX)
    world_positions = [list(mg * m.off) for m in matrices]
    print(f"Frame {frame}: {len(world_positions)} clones, first pos: {world_positions[0]}")
```

4. Confirm output: 50 clones per frame, positions changing frame to frame, no NaN values.

5. Run full bake using the Complete Animation Bake Workflow (Steps 3-5 above). The export JSON is saved to the system temp directory.

6. Convert to Three.js-compatible format — the JSON structure `frames[frame][clone_index].position` maps directly to `BufferAttribute` update per frame in an `AnimationMixer`-driven loop.

**Three.js consumption pattern:**
```javascript
// Load the exported JSON
const data = await fetch('/data/spherecloner_export.json').then(r => r.json());
const fps = data.fps;

// On each animation frame:
function updateClones(currentTime) {
    const frame = Math.floor(currentTime * fps);
    const frameData = data.frames[frame];
    if (!frameData) return;
    frameData.forEach((clone, i) => {
        meshes[i].position.set(...clone.position);
    });
}
```

---

### Example 2: Debug Missing Redshift Colors Using Preview Bitmap Workaround

**Scenario:** A scene uses Redshift materials. You need to identify which material is which color for a clone-to-material mapping, but `mat[c4d.MATERIAL_COLOR_COLOR]` returns black or zero for all RS materials.

**Why it fails:**
Redshift materials store color in the RS node graph, not in the standard C4D material container. `mat[c4d.MATERIAL_COLOR_COLOR]` reads the legacy C4D channel, which is empty for RS materials.

**Workaround — preview bitmap sampling:**
```python
import c4d

doc_mats = doc.GetMaterials()
material_colors = []

for mat in doc_mats:
    name = mat.GetName()
    bmp = mat.GetPreview(0)  # 0 = default preview size
    if bmp is None:
        material_colors.append({"name": name, "color": None, "error": "no preview"})
        continue

    w = bmp.GetBw()
    h = bmp.GetBh()

    # Sample a 3x3 grid of pixels from the center region to get a representative color
    samples = []
    for sx in [w // 3, w // 2, 2 * w // 3]:
        for sy in [h // 3, h // 2, 2 * h // 3]:
            r, g, b = bmp.GetPixel(sx, sy)
            samples.append((r, g, b))

    avg_r = sum(s[0] for s in samples) // len(samples)
    avg_g = sum(s[1] for s in samples) // len(samples)
    avg_b = sum(s[2] for s in samples) // len(samples)

    material_colors.append({
        "name": name,
        "color_rgb_0_255": [avg_r, avg_g, avg_b],
        "color_hex": f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"
    })

import json
print(json.dumps(material_colors, indent=2))
```

**Caveats:**
- Preview bitmaps are generated from the last render or interactive preview. If C4D hasn't rendered a preview for a material, `GetPreview()` may return None or a gray placeholder.
- Force a preview render by opening the Material Manager and letting thumbnails regenerate before running this script.
- For multi-layer or metallic RS materials, the sampled color is an approximation — use it for identification (which material is roughly red vs. blue) rather than precise color matching.
- Cross-reference with `MODATA_CLONE` indices to build a clone -> material -> color lookup table.
- This also survives a lapsed RS license (it reads a cache, doesn't render) — see the note under "Fallback: Preview Bitmap Sampling" above.

## Zero-click backend workflow

The MCP plugin auto-starts its socket server when Cinema boots (headless
MessageData pump — no dialog needed; commit 94f9cbb in the plugin repo).
To (re)start Cinema as a backend from a shell, music-shader has the
pattern:

```sh
./scripts/c4d-backend.sh --restart [scene.c4d]   # kill -> open -> wait for port 5555 -> READY
```

Deadlock warning: do NOT call `c4d.documents.InsertBaseDocument` /
`SetActiveDocument` from MCP scripts — they hang Cinema from the plugin
dispatch thread (same class as the RenderDocument deadlock). Build probe
objects INSIDE the already-active document instead, hide originals, and
clean up after.

## The emission-probe method: sampling a renderer's procedural field

When you need a renderer's EXACT procedural field (noise, gradient, any
shader node) and CPU reimplementation fails, use the renderer as an oracle:

1. Clone the material; rewire `<node>.outcolor -> standardmaterial
   .emission_color` (weight 1); zero base/refl/refr weights. Undo any node
   colorization when decoding (e.g. black->green ramp: value = G channel,
   sRGB-linearized).
2. Put it on a plane at known world coordinates; a long-lens perspective
   camera is fine — the projection of a PLANE at fixed depth is exactly
   affine, no ortho needed (RS + parallel cameras can be flaky anyway).
3. Every rendered pixel is a field sample at a known coordinate. Sweep the
   plane's z for volume slices; scene time for the temporal axis.
4. Emission-only renders converge in seconds even under a heavy render
   preset.

Verified findings that motivated this (YM shader project): Redshift's
"Maxon noise" is NOT lattice-compatible with `c4d.utils.noise.C4DNoise`
(max field correlation 0.23 across scale/octave/orientation sweeps) — CPU
bakes can only ever be statistical cousins. Camera gotcha: a camera at -z
looking toward +z renders the plane X-MIRRORED relative to world axes —
verify orientation against a known-asymmetric reference before trusting
the decode.

Batch-render the sweep: single-frame Picture Viewer autosave is
unreliable, but the Batch Render queue (`c4d.documents.GetBatchRender()`)
saves every frame of a MANUAL frame-range job dependably. Save one .c4d
variant per configuration (SaveDocument creates no directories — mkdir
first), AddFile them all, SetRendering(BR_START). 360 emission renders
took ~25 min.

## Rendering ground truth via Picture Viewer (Redshift)

Scripted `c4d.documents.RenderDocument()` may return `RENDERRESULT_OK` with an
all-black bitmap on some Redshift builds (every variant: main thread, clone,
autosave, BatchRender). The reliable path is the async Picture Viewer render:

```python
import c4d
doc = c4d.documents.GetActiveDocument()
rd = doc.GetActiveRenderData()
# CRITICAL: default frame sequence may be "All Frames" — firing PV then
# renders the entire timeline (an accidental 148-frame overnight job).
rd.GetDataInstance()[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_CURRENTFRAME
doc.SetTime(c4d.BaseTime(FRAME, doc.GetFps()))
doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
c4d.CallCommand(12099)   # Render to Picture Viewer — ASYNC, returns immediately
```

- Poll completion with `c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING)`
  (1 while rendering, 0 when done).
- Stop a running PV render programmatically: `c4d.CallCommand(430000731)`.
- **No manual save needed**: if the render settings have a save path, Picture
  Viewer AUTOSAVES each finished frame to
  `<save-path>/<scene-name>/<scene-name>_NNNN.png` — check there before asking
  a human to File→Save As. (Discovered after two sessions of manual saving.)
- Never call `RenderDocument()` from code already on C4D's main thread (the
  plugin dispatch queue) — it deadlocks: rendering needs the event loop the
  blocked call is holding.

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ExecutePasses()` fails or returns wrong data | `SetTime()` called after `ExecutePasses()` instead of before | Always: `SetTime` → `ExecutePasses` → read data |
| MoGraph matrices all identical across frames | Jumped to frame without sequential stepping | Step frames 0→N in order, never skip |
| World positions far off from viewport | Not applying global matrix | `world_pos = cloner.GetMg() * m.off` |
| `GeGetMoData()` returns None | Cloner not yet evaluated at that frame | Ensure `ExecutePasses` ran; check cloner is not muted |
| Clone count changes per frame | Object cloner with animated child visibility | Read `md.GetCount()` per frame, don't assume fixed count |
| Script times out on large range | Frame range too large for single MCP call | Chunk into 100-200 frame batches, merge results |
| `MODATA_CLONE` all 0.0 | Single-child cloner or no child cycling | Expected behavior — all clones share one child |
| Keyframes on effector not animating output | Takes system overriding take | Check `doc.GetTakeData().GetCurrentTake()` |
| Every batch job errors instantly with Redshift "Out Of Memory", or an interactive PV render (`CallCommand(12099)`) never errors but `CheckIsRunning(CHECKISRUNNING_EXTERNALRENDERING)` stays `1` far longer than a trivial scene should take to converge | Don't assume real memory contention — a lapsed/expired Redshift license produces exactly these two symptoms (misleading instant "OOM" on batch jobs; license-check stall reads as an infinite hang on PV) | Isolate: load one scene directly (not the batch queue), fire a trivial single-frame PV render (ideally an emission-probe scene, which should converge in seconds per above), and poll `CHECKISRUNNING_EXTERNALRENDERING`. Hangs well past that with no error = check the RS license, not RAM. Freeing system memory will not fix a license problem. |

## Known Errors & Workarounds

See [references/errors.md](references/errors.md) for complete Python API and MCP tool error tables.

## Advanced Debugging

### Raw Socket Fallback

If MCP tools fail entirely but the C4D socket server is alive at `127.0.0.1:5555`, you can bypass the MCP layer and send commands directly. This is a last-resort diagnostic tool, not a normal workflow path.

**When to use:**
- All MCP tool calls return connection errors
- `execute_python_script` fails at the transport level (not a Python error)
- You need to confirm the C4D server process is alive at all

**Working example:**
```python
import json
import socket

def c4d_raw(command_dict, host="127.0.0.1", port=5555, timeout=10):
    """
    Send a raw command to the C4D socket server and return the parsed response.
    Commands mirror the MCP tool names: get_scene_info, list_objects, execute_python_script, etc.
    """
    payload = json.dumps(command_dict) + "\n"
    s = socket.create_connection((host, port), timeout=timeout)
    try:
        s.sendall(payload.encode("utf-8"))
        # Read until newline (server responds with a single JSON line)
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:
                break
    finally:
        s.close()
    return json.loads(response.decode("utf-8").strip())

# Example: check connection
result = c4d_raw({"command": "get_scene_info"})
print(result)

# Example: run a Python expression
result = c4d_raw({
    "command": "execute_python_script",
    "params": {"script": "print(doc.GetDocumentName())"}
})
print(result)
```

**Notes:**
- The socket server may not be running if you started C4D without the MCP plugin loaded.
- Port `5555` is the default. Some forks or configurations may use different ports.
- Responses are newline-delimited JSON. Large responses (e.g., full scene data) will be chunked — loop on `recv` until you have a complete JSON object.

## Data Output

- Save to JSON with metadata (scene name, fps, frame range, sampling step)
- `json.dumps()` + `print()` for small results, `tempfile.gettempdir()` for large data
- Keep both raw extraction and derived model

## Additional References

- [references/errors.md](references/errors.md) — Python API and MCP tool error tables, security restrictions, key parameter IDs
- [references/mograph-baking-guide.md](references/mograph-baking-guide.md) — Detailed sequential frame stepping examples, chunked baking strategy, memory management
- [references/redshift-workarounds.md](references/redshift-workarounds.md) — Redshift color sampling, material verification patterns, node graph limitations

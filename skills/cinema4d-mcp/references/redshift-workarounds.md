# Redshift Data Access

This reference covers how to access Redshift material and scene data through the C4D Python API.

## Primary Path: maxon Node-Space API (Proven Working)

**RS node graphs ARE fully accessible** when Redshift is installed. Even though materials may appear as type 5703 (standard C4D wrappers) and the `inspect_redshift_materials` MCP tool may skip them as `not_redshift_like`, the actual RS node graph data is readable through the `maxon` Python API.

### Complete RS Material Extraction Pattern

```python
import c4d
import maxon

RS_NODESPACE = "com.redshift3d.redshift4c4d.class.nodespace"

doc = c4d.documents.GetActiveDocument()

for mi, mat in enumerate(doc.GetMaterials()):
    nm = mat.GetNodeMaterialReference()
    graph = nm.GetGraph(RS_NODESPACE)
    if graph.IsEmpty():
        continue

    root = graph.GetRoot()
    inner = root.GetInnerNodes(maxon.NODE_KIND.ALL_MASK, False)

    for n in inner:
        kind = n.GetKind()
        nid = str(n.GetId())

        if kind == 1:  # NODE
            print(f"Node: {nid}")
        elif kind == 8:  # INPORT
            short_name = nid.split('.')[-1]
            try:
                val = n.GetDefaultValue()
                if val is not None:
                    print(f"  {short_name} = {val}")
            except:
                pass
```

### What This Gives You

All RS shader node types and their port values:
- **RS Standard Material**: base_color, base_color_weight, metalness, refl_roughness, refr_weight, opacity_color, emission_color/weight, coat params, etc.
- **RS Incandescent**: color, intensity, temperature, colormode, alpha, doublesided
- **TextureSampler**: path (texture file), gamma, rotate, scale, offset, color_multiplier
- **MaxonNoise**: color1, color2, noise_type, octaves, animation_speed, coord_scale_global, seed, brightness, contrast
- **RSRamp**: ramp stops with position, color, interpolation
- **RSColorCorrection**: gamma, contrast, hue, saturation, level

### Finding Specific Node Types

```python
result = maxon.GraphModelHelper.FindNodesByAssetId(
    graph, "com.redshift3d.redshift4c4d.nodes.core.standardmaterial", True
)
```

Known RS asset IDs:
- `com.redshift3d.redshift4c4d.nodes.core.standardmaterial`
- `com.redshift3d.redshift4c4d.nodes.core.incandescent`
- `com.redshift3d.redshift4c4d.nodes.core.output`

### Node Kind Constants

| Kind | Value | Meaning |
|------|-------|---------|
| NODE | 1 | Shader node |
| INPUTS | 2 | Input ports container |
| OUTPUTS | 4 | Output ports container |
| INPORT | 8 | Individual input port (has readable value) |
| OUTPORT | 16 | Individual output port |

### Key API Notes

- `GetGraph()` returns `NodesGraphModelRef` — does NOT have `IsValid()`, use `IsEmpty()` instead
- `GetRoot().GetInnerNodes(maxon.NODE_KIND.ALL_MASK, False)` is the reliable traversal method
- `GetChildren()` on the root often returns empty — use `GetInnerNodes` instead
- `GetDefaultValue()` works for reading port values; `GetEffectivePortValue()` also works
- Color values print as `R:1.0, G:1.0, B:1.0`; Vec3 as `X:0.2, Y:0.2, Z:0.2`
- Ramp data includes nested knot entries with position, color, interpolation per stop

## Secondary Path: Legacy Redshift GraphView

For older RS shader-network materials where `GetGraph()` returns an empty graph:

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

This path is useful when the Cinema UI shows a Redshift Shader Graph but the maxon node-space API returns empty. Not all scenes need this — newer RS materials work with the primary path.

## Tertiary Fallback: Preview Bitmap Sampling

When Redshift is not installed at all, sample preview bitmaps for approximate colors:

```python
bmp = mat.GetPreview(0)
if bmp:
    w, h = bmp.GetBw(), bmp.GetBh()
    r, g, b = bmp.GetPixel(w // 2, h // 2)
```

This is an approximation — use it only for rough color identification when the above methods are unavailable.

## What You CAN Access

### With RS Installed (primary path)
- Full RS node graph: all shader nodes, all port values, texture paths, noise params, ramp stops
- Material assignments via `Ttexture` tags
- Material preview bitmaps
- `import redshift` module for legacy GraphView access

### Without RS Installed
- Material names, hierarchy, assignments
- Preview bitmaps (if cached)
- BaseContainer values (limited — RS params stored in node graph, not container)
- Object transforms, visibility, hierarchy
- Cloner clone-to-material index data (`MODATA_CLONE`)

### Still Not Accessible via Python API
- RS light color/intensity/exposure (stored at container IDs 10000+ but all read as defaults; likely need RS light node graph access which is not exposed the same way as materials)
- Node connections/wiring between RS material nodes (which output connects to which input) — `GetConnections()` exists but hasn't been tested
- RS environment settings internals

## RS Color Sampling via Preview Bitmap

RS materials store color in the node graph, not the legacy C4D color channel. `mat[c4d.MATERIAL_COLOR_COLOR]` will return black or zero for all RS materials.

### Basic Color Sampling

```python
import c4d
import json

doc_mats = doc.GetMaterials()
results = []

for mat in doc_mats:
    name = mat.GetName()
    bmp = mat.GetPreview(0)

    if bmp is None:
        results.append({"name": name, "error": "no_preview"})
        continue

    w = bmp.GetBw()
    h = bmp.GetBh()

    if w == 0 or h == 0:
        results.append({"name": name, "error": "zero_size_preview"})
        continue

    # Sample center pixel
    cx, cy = w // 2, h // 2
    r, g, b = bmp.GetPixel(cx, cy)

    results.append({
        "name": name,
        "color_rgb": [r, g, b],
        "color_hex": f"#{r:02x}{g:02x}{b:02x}",
        "preview_size": [w, h]
    })

print(json.dumps(results, indent=2))
```

### Multi-Point Sampling for Better Accuracy

Single-pixel sampling can hit specular highlights or dark shadow regions. Sample a grid and average:

```python
import c4d
import json

def sample_material_color(mat, grid_size=5):
    bmp = mat.GetPreview(0)
    if bmp is None:
        return None

    w = bmp.GetBw()
    h = bmp.GetBh()
    if w == 0 or h == 0:
        return None

    # Avoid edges (first and last 20% of dimensions) to skip shadow/highlight regions
    margin_x = w // 5
    margin_y = h // 5
    x_start, x_end = margin_x, w - margin_x
    y_start, y_end = margin_y, h - margin_y

    samples = []
    for i in range(grid_size):
        for j in range(grid_size):
            x = x_start + (x_end - x_start) * i // (grid_size - 1)
            y = y_start + (y_end - y_start) * j // (grid_size - 1)
            r, g, b = bmp.GetPixel(x, y)
            samples.append((r, g, b))

    avg_r = sum(s[0] for s in samples) // len(samples)
    avg_g = sum(s[1] for s in samples) // len(samples)
    avg_b = sum(s[2] for s in samples) // len(samples)

    return {
        "rgb": [avg_r, avg_g, avg_b],
        "hex": f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}",
        "sample_count": len(samples)
    }

for mat in doc.GetMaterials():
    color = sample_material_color(mat)
    print(f"{mat.GetName()}: {color}")
```

### Forcing Preview Regeneration

If `GetPreview()` returns None or a gray placeholder, the material has no cached preview. There is no reliable way to force preview generation from Python without user interaction. The workaround is:

1. Open C4D's Material Manager (Window → Material Manager)
2. Let all material thumbnails render (they render in the background)
3. Then re-run the sampling script

Alternatively, use the RS material sphere render approach (see below).

## RS Material Verification via Isolated Sphere Render

For precise color identification, temporarily assign each material to an isolated sphere and render a small preview frame:

```python
import c4d
import json

# This approach: create a sphere, assign each material, render one frame,
# sample the center of the rendered bitmap.
# WARNING: This modifies the scene temporarily. Always undo or restore.

doc_mats = doc.GetMaterials()
results = []

# Create a temporary sphere
sphere = c4d.BaseObject(c4d.Osphere)
sphere.SetName("__temp_color_sphere__")
doc.InsertObject(sphere)

for mat in doc_mats:
    name = mat.GetName()

    # Assign material to sphere
    tag = sphere.MakeTag(c4d.Ttexture)
    tag[c4d.TEXTURETAG_MATERIAL] = mat

    # Force scene update
    doc.SetTime(doc.GetTime())
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)

    # Read preview (this is the material's own preview, not a render)
    bmp = mat.GetPreview(0)
    if bmp:
        w, h = bmp.GetBw(), bmp.GetBh()
        r, g, b = bmp.GetPixel(w // 2, h // 2)
        results.append({"name": name, "color_hex": f"#{r:02x}{g:02x}{b:02x}"})
    else:
        results.append({"name": name, "color_hex": None})

    # Remove tag
    tag.Remove()

# Remove temporary sphere
sphere.Remove()
c4d.EventAdd()

print(json.dumps(results, indent=2))
```

## Material Assignment Verification

To confirm which material is assigned to which object (without relying on RS APIs):

```python
import c4d
import json

def find_material_assignments():
    assignments = []
    stack = [doc.GetFirstObject()]
    while stack:
        obj = stack.pop()
        while obj:
            # Check texture tags
            tag = obj.GetFirstTag()
            while tag:
                if tag.GetType() == c4d.Ttexture:
                    mat = tag[c4d.TEXTURETAG_MATERIAL]
                    if mat:
                        assignments.append({
                            "object": obj.GetName(),
                            "material": mat.GetName(),
                            "tag_projection": tag[c4d.TEXTURETAG_PROJECTION]
                        })
                tag = tag.GetNext()
            if obj.GetDown():
                stack.append(obj.GetDown())
            obj = obj.GetNext()
    return assignments

assignments = find_material_assignments()
print(json.dumps(assignments, indent=2))
```

## Clone-to-Material Color Mapping

Full pipeline: MODATA_CLONE indices → material name → sampled color:

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

def sample_color(mat):
    bmp = mat.GetPreview(0)
    if bmp is None:
        return None
    w, h = bmp.GetBw(), bmp.GetBh()
    if w == 0 or h == 0:
        return None
    r, g, b = bmp.GetPixel(w // 2, h // 2)
    return f"#{r:02x}{g:02x}{b:02x}"

fps = doc.GetFps()
cloner = find_obj("MyClonerName")

# Step to a representative frame first
doc.SetTime(c4d.BaseTime(0, fps))
doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)

md = mo.GeGetMoData(cloner)
clone_indices = md.GetArray(c4d.MODATA_CLONE)

# Get child objects of the cloner (the "cycle" objects)
children = []
child = cloner.GetDown()
while child:
    children.append(child)
    child = child.GetNext()

# Map: child index -> material -> color
child_colors = []
for child_obj in children:
    tag = child_obj.GetFirstTag()
    mat_name = None
    color = None
    while tag:
        if tag.GetType() == c4d.Ttexture:
            mat = tag[c4d.TEXTURETAG_MATERIAL]
            if mat:
                mat_name = mat.GetName()
                color = sample_color(mat)
            break
        tag = tag.GetNext()
    child_colors.append({"child": child_obj.GetName(), "material": mat_name, "color": color})

# Map each clone to its color
clone_color_map = []
for i, idx in enumerate(clone_indices):
    child_slot = int(round(idx * (len(children) - 1))) if len(children) > 1 else 0
    child_slot = max(0, min(child_slot, len(children) - 1))
    clone_color_map.append({
        "clone": i,
        "clone_index": float(idx),
        "child_slot": child_slot,
        "color": child_colors[child_slot]["color"] if child_slot < len(child_colors) else None
    })

print(json.dumps({
    "child_colors": child_colors,
    "clone_color_map": clone_color_map[:10]  # first 10 for verification
}, indent=2))
```

## RS Node Graph Parameter IDs

RS parameter IDs are **dynamic** — they depend on the RS version installed and the specific node type. There is no stable, version-independent list. However, known IDs found in practice:

| ID | Context | Meaning |
|----|---------|---------|
| `1041671` | RS Standard Material, RS Emission node | Emission color |
| `1100` | Random Effector | Seed value |
| `2000` | RS Material (various) | Base color slot (version-dependent) |

**Do not hardcode RS parameter IDs** without confirming them against the actual C4D version in use. Use `try/except` around any RS container access:

```python
try:
    color = mat[1041671]
    if color is not None:
        print(f"Emission color: {color}")
except Exception as e:
    print(f"Could not read RS param 1041671: {e}")
```

## Iterating RS Material Data Container

Attempting to iterate all keys in an RS material's data container will raise `Parameter value accessible (object unknown in Python)` on RS-type entries. Use defensive iteration:

```python
import c4d

for mat in doc.GetMaterials():
    bc = mat.GetDataInstance()
    if bc is None:
        continue
    # Iterate known safe ranges only — do NOT use bc.GetClone() or full iteration
    safe_ids = [c4d.MATERIAL_COLOR_COLOR, c4d.MATERIAL_LUMINANCE_COLOR, c4d.MATERIAL_USE_COLOR]
    for param_id in safe_ids:
        try:
            val = mat[param_id]
            if val is not None:
                print(f"  {param_id}: {val}")
        except Exception:
            pass  # RS material — this param doesn't exist in the standard container
```

## Known Limitations Summary

| Operation | Status | Method |
|-----------|--------|--------|
| Read RS material base color | **Working** | `maxon` node-space API: `GetDefaultValue()` on INPORT nodes |
| Read RS material all params | **Working** | Full node graph traversal via `GetInnerNodes()` |
| Read RS texture paths | **Working** | TextureSampler node `path` port |
| Read RS noise/ramp params | **Working** | MaxonNoise, RSRamp node ports |
| Read RS node graph connections | **Untested** | `GetConnections()` exists but not yet verified |
| Read RS light color/intensity | **Not working** | Container IDs 10000+ return defaults; light node graph not exposed |
| Read RS environment shader | **Not working** | No known API path |
| Confirm material assignment | **Working** | Iterate `Ttexture` tags |
| Get all material names | **Working** | `doc.GetMaterials()` |
| Preview bitmap color sampling | **Working (fallback)** | `mat.GetPreview(0).GetPixel()` |

# Redshift Data Access

This reference covers how to access Redshift material and scene data through the C4D Python API.

## Critical Gotcha: Never Resolve a Material by Name

C4D scenes routinely have **many materials with the identical name** (real-world example:
one scene had 18 materials all named "Emission"). `doc.SearchMaterial("Emission")` and any
`doc.GetMaterials()` loop filtered by `.GetName() == "..."` will silently return an
arbitrary one of them — not necessarily the one actually driving the object you care about.
This is far more dangerous than an obvious error: it returns a fully plausible node graph
with real-looking (but wrong) values, so you won't notice unless you cross-check.

**Always resolve the exact material via the object's own tag**, never by name:

```python
plane = doc.SearchObject("SomeObjectName")  # or walk the hierarchy
tag = None
for t in plane.GetTags():
    if t.CheckType(c4d.Ttexture):
        tag = t
        break

mat = tag[c4d.TEXTURETAG_MATERIAL]  # the ONE material this object's tag actually points to
```

Only then feed `mat` into the node-graph extraction pattern below. A real incident: querying
`doc.SearchMaterial("Emission")` returned a materially different (and much simpler — no
texture/color-correction chain at all) node graph than the material genuinely assigned via
the object's tag, leading to an incorrect "this object has real specular reflection" finding
that had to be walked back after re-resolving via the tag.

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
- Ramp data has nested knot entries (position, color, interpolation per stop) *structurally*,
  but as of 2026-07-23 `FindChild("ramp").GetChildren()` throws `no target to copy for
  '<net.maxon.graph.interface.graphmodel>'` on the tested maxon build — don't assume this is
  readable without re-verifying against the current version. See "Raw Byte-Level HyperFile
  Scanning" further down for a working fallback.

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
- Node connections/wiring between RS material nodes (which output connects to which input) — `GetConnections()` exists but hasn't been tested
- RS environment settings internals

> **Correction (2026-06):** RS light color/intensity/exposure **ARE** readable. See
> "RS Light Parameters" below. Earlier notes claiming they "read as defaults" were wrong —
> the values come through fine via `light.GetDataInstance()[param_id]` for the simple
> (non-Filename) params. What actually fails is the *Filename/texture* params on the light.

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
| Read RS material base color | **Working** | `maxon` node-space API: scalar/vector/color INPORT values via `graph.GetRoot().(GetChildren\|GetInnerNodes)` → `inputs.FindChild(portId).GetValue(maxon.EffectivePortValue)` |
| Read RS material all params | **Working, with a caveat** | Full node graph traversal via `GetInnerNodes()` — `GetDefaultValue()` on an `GetInnerNodes()`-sourced port returns the port's *schema* default, not its actual/effective value, and was `None` even for plain non-Filename float ports (`rotate`) that read fine as `0` via `FindChild(...).GetValue(maxon.EffectivePortValue)`. Use the `FindChild` + `GetValue(maxon.EffectivePortValue)` pattern, not raw `GetDefaultValue()` on inner nodes. |
| Read RS texture paths | **API limitation CONFIRMED — not an RS-install issue (2026-07-23, retested WITH `import redshift` succeeding, RS 3.5.24 / C4D 2024.2)** | Every method still returns `None` even with full Redshift installed: `GetValue(maxon.EffectivePortValue)`, `GetValue(maxon.PortValue)`, `GetDefaultValue()`. **The "maybe it needs the full RS engine" hypothesis is now REFUTED** — this is a maxon Python API gap in C4D 2024's bindings, full stop. Byte-level scanning remains the only path (see "Raw Byte-Level HyperFile Scanning" / "Filename/URL Port Value Format" below). Also reconfirmed at byte level: the tested file's `tex0/path` ports (13/13) genuinely carry no override — absence of data, not unreadability. Don't conflate the two; check bytes to tell them apart. |
| Read RS noise/ramp params | **Ramp knot sub-values confirmed unreachable on C4D 2024 + RS 3.5.24 — WITH Redshift installed (2026-07-23)** | Exhaustive retest with `import redshift` succeeding: `FindChild("ramp").GetChildren()` AND `FindChild("ramp").FindChild("_0")` both throw `no target to copy for '<net.maxon.graph.interface.graphmodel>'`; flat `GetInnerNodes(ALL_MASK)` traversal DOES list `ramp/_N/position`-style sub-ports but `GetValue()` returns `None` under both `maxon.EffectivePortValue` and `maxon.PortValue`, across all 32 materials in a production scene. **Partial breakthrough:** the ramp port's own value IS readable — it returns an `UnknownDataType` whose **`.ToString()` works** and dumps the knot dictionary, e.g. `{(_0, insertindex 1), (_1, insertindex 2), (_3, insertindex 4)}` — so knot COUNT, knot IDs, and insertion order are recoverable via API. Knot positions/colors are not (neither via API nor yet via bytes — see the ramp byte-encoding section below). A fresh unedited ramp node serializes NO knot data at all (schema defaults), so a serialized knot dict = a user-edited ramp. |
| Read RS node graph connections | **Unreadable via API, but solved via byte-level scan (2026-07-23)** | `graph.GetConnections(...)` — `NodesGraphModelRef` object has no such attribute in this maxon build; `port.GetConnections(direction)` throws `no target to copy for '<net.maxon.graph.interface.graphmodel>'` (same root cause as the ramp-knot API failure). **But the wiring IS recoverable from the raw file bytes** — see "Node Wire Connections — byte-level format" below. Do not rely on node-adjacency-in-serialization-order as a proxy for wiring; a real case in this session had a node appear *before* its actual downstream consumer in file order (texture sampler fanning out to two different destinations non-sequentially). Decode the actual wire records instead. |
| Read RS light color/intensity/exposure | **Working** | `light.GetDataInstance()[param_id]` — see RS Light Parameters |
| Read RS light/dome **texture** path | **Working (indirect)** | node-graph/branch string ports — NOT container subscript |
| Read RS environment shader | **Not working** | No known API path |
| Read any object/material **animation** | **Working** | CTrack/CCurve walk — renderer-independent, see Animation |
| Resolve texture ref → absolute file | **Working** | `c4d.GenerateTexturePath()` + doc-relative search |
| Confirm material assignment | **Working** | Iterate `Ttexture` tags |
| Get all material names | **Working** | `doc.GetMaterials()` |
| Preview bitmap color sampling | **Working (fallback)** | `mat.GetPreview(0).GetPixel()` |

## Shared Node-Graph Templates — a second duplicate-material trap

Beyond 18 materials literally named "Emission" (see the top gotcha), this scene's duplicate
materials also share the **same internal node-instance GUIDs** with each other — e.g.
`rscolorcorrection@O3D2pWdCL5MkjI28oZShTg` appeared identically in *18-24 different byte
locations* across one file, and even matched a node ID found in a **separate scene file**
(`AW_ANIM_v002.c4d`) from an earlier session. This is not a coincidence or a hash collision:
duplicating a Redshift material in C4D (Alt+drag / copy) apparently does **not** regenerate
internal node-graph IDs — only per-instance parameter *overrides* differ between copies. The
underlying node/port structure (including texture assignments and ramp shapes, if unedited
per-copy) is a shared template.

**Practical consequence:** you cannot assume "I found this node ID, therefore I found this
material's data" — the same node ID exists once per duplicate, each with potentially different
override values. If you need data for one *specific* material instance (resolved correctly via
its object's tag, per the top gotcha), and the API and/or byte scan turns up multiple candidate
values, disambiguate by using an already-known-correct value from that instance (read live via
the API) as a fingerprint to locate the right byte block — see next section.

## Raw Byte-Level HyperFile Scanning (No C4D/Redshift Required)

When the maxon API hits a dead end (Filename ports, ramp knots, connections) — or when you
don't have C4D running at all — the `.c4d` file on disk is directly parseable. Confirmed working
2026-07-23 against an **uncompressed** HyperFile (`AW_ASSEMBLE_v002_432521.c4d`, ~1.6MB,
`import redshift` failing on the machine that produced this).

### Value record format

Every RS node-graph port with a **non-default, explicitly-overridden** value is serialized as:

```
<full ASCII port-id string, e.g. "com.redshift3d.redshift4c4d.nodes.core.rscolorcorrection.hue">
<~45 bytes of zero-padded flags>
<3-byte type/flag marker, e.g. 10 21 11, 10 21 10, 10 23 11, 10 23 10, 10 1e 11, 10 1e 10>
<2 more bytes>
<8-byte little-endian float64>
<next port-id string starts immediately>
```

The exact marker bytes vary by port/value-type across files (`10 23 11` in one file, `10 21 11`
in another) — don't hardcode one marker. Scan for the port-id string, then search the following
~90 bytes for *any* of the known marker byte-triples, then decode the 8 bytes starting 5 bytes
after the marker as `struct.unpack("<d", ...)`.

**Absent value = no override, not unreadable.** If the port-id string is immediately followed
(after ~2 zero bytes) by the *next* port-id string with no marker/payload in between, that port
has no override in this file — it uses the schema default (or, for a duplicated-template node,
inherits from wherever the template's real value lives). This is a genuine finding, not a parse
failure — confirmed this way for `tex0/path` and most ramp-knot sub-ports on one specific
material instance in this session.

### Disambiguating shared-template duplicates by fingerprint

1. Resolve the material correctly via the object's tag (top gotcha) and read ONE scalar value
   live via the maxon API that you're confident is unique to this instance (e.g. `hue`).
2. Byte-scan the whole file for that port-id string's value records; decode all occurrences.
3. The occurrence whose decoded value matches your live API reading pins down the byte offset
   range for *this specific* material's block. Use the node-instance markers around that offset
   (`nodetype@GUID` strings — no port suffix) to find the block's rough start/end.
4. Extract everything else (other scalar ports, ramp-knot presence/absence, texture-path
   presence/absence) from within that specific offset window, not from the first match anywhere
   in the file.

### Texture path / filename strings

RS texture references were **not found in ASCII** in the tested file. C4D internally uses
UTF-16LE for some string tables — a UTF-16LE search (`word.encode("utf-16-le")`) surfaced a
`bokeh_tex_1.png` reference elsewhere in the same file that a plain ASCII `re.finditer` missed
entirely. Always try both encodings before concluding a filename isn't present.

### Node-instance ID strings

Node declarations look like `<nodetype>@<22-char-GUID>` (e.g.
`texturesampler@ISGuK$ndFNyptHY0S5rfnj`) with no port suffix — these are useful anchors for
finding a node's block boundaries, separate from the `<nodetype>.port` value-record strings.

### Filename/URL Port Value Format (solves texture-path decoding, when one exists)

Confirmed 2026-07-23 using a real populated example (`big_data.jpg`, found via `tex0/path` in
`AW_ANIM_v002.c4d`). When a Filename-typed port (e.g. `texturesampler.tex0/path`) actually has a
value, it's a `maxon.Url` struct serialized as:

```
<port-id string>
<~40 bytes padding/flags>
10 1e 10 1e 01 00 00 00 00 00 01 00 00 00 00 00 00 00   <- one flag block
10 23 1a 00 00 03 13 00 00 00 00                          <- type marker
<1-byte length><scheme bytes, e.g. "relative"><0x00>       <- scheme string
<1-byte length><path bytes, e.g. "big_data.jpg"><padding>  <- path string
<next port-id string starts>
```

i.e. two Pascal-style (length-byte-prefixed) ASCII strings back to back: scheme, then path. An
**unpopulated** Filename port (no override) looks completely different — the port-id string is
followed immediately (~2 zero bytes) by the *next* port-id string, with none of the above marker
or string structure at all. This distinguishes "genuinely no texture assigned" from "texture
assigned but unreadable" — check for the `10 23 1a` marker + Pascal-string pair, not just for the
raw filename text (which may not be present at all if the port has no override).

**Confirmed limitation:** if a scene stores texture refs as `relative:///`-style paths this
decodes cleanly. A separate scene (`AW_ASSEMBLE_v002_432521.c4d`) was found to have **zero**
populated Filename ports anywhere (13/13 `tex0/path` instances checked, whole-file search for
`relative`/`asset`/`file`/known filenames all came up empty except for an unrelated
`bokeh_tex_1.png` reference elsewhere) — genuinely no textures wired into any RS material node in
that file, not a decode failure. Separately, that file's `net.maxon.class.assetlink` mechanism
(31 occurrences) turned out to be exclusively for **node-template** references (`_type` always
resolves to `net.maxon.node.assettype.nodetemplate` — i.e. "this node instance is an RS Standard
Material", not a texture asset) — don't confuse this with a media/texture database reference
system; no such system was found for textures in either tested file.

### RS Environment Shader — where it would live, if used

The RS Environment shader is **not** a `nodes.core.*` node type — an exhaustive scan of two
different production `.c4d` files for `environment`/`dome`/`sky`/`hdri`/`world` found no such
node type anywhere. It's instead represented as a dedicated **port on the scene-level `output`
node** (distinct from each material's own per-material `output` node) —
`com.redshift3d.redshift4c4d.node.output.environment`, alongside `.contour`. Confirmed by
wire-tracing (see "Node Wire Connections" below): in the tested file, only `.surface` on that
scene-level output node has an incoming wire (from `standardmaterial.outcolor`); `.environment`
is declared but has nothing connected. This is a genuine "not used in this scene," not a read
failure — if a future scene DOES have an environment shader, look for a wire feeding
`output@<scene-level-GUID>.environment` using the same wire-decoding method used for materials.
Still unknown: what an actual populated environment-shader node/value would look like, since no
example was found to reverse-engineer from. The existing "RS Environment — confirmed not
extractable" section below (API-level, Maxon forum sourced) still holds for the live-API path;
this section is about the file-byte path specifically.

## 2026-07-23 Full-Redshift Session Results (RS 3.5.24 on C4D 2024.2)

`import redshift` finally succeeded on a machine (version 3.5.24). Definitive outcomes:

- **The maxon-API failures are NOT Redshift-install-dependent.** Filename ports, ramp knot
  sub-values, `port.GetConnections()`, and `FindChild()` on bundle ports all fail identically
  with full RS installed. These are C4D 2024 maxon Python binding gaps. Stop re-testing them
  per-install; re-test per-C4D-version instead.
- **`UnknownDataType.ToString()` is the sleeper API win**: any port value that comes back as
  `UnknownDataType` (ramp dicts, etc.) will usually stringify via `.ToString()` even though
  nothing else works on it. `.GetType()` names the maxon type. `MaxonConvert()` does NOT work.
- **`redshift` module useful IDs**: `Orsenvironment=1036757`, `Orssky=1036754`, `Orsvolume`,
  `Orslight`, `Frsproxyexport`/`Frsproxyimport` (proxy format plugin ids), `VPrsrenderer=1036219`.
  `GetRSMaterialNodeMaster(mat)` returns `None` for node-space materials (legacy-only API).
  `ShaderGraphVisitor.Visit(mat)` returns `False` on node-space materials — also legacy-only.
- **RS proxy export via `SaveDocument(doc, path, ..., redshift.Frsproxyexport)` works** but
  materials export as `<<RedshiftGlobalInvalidMaterial>>` placeholders (geometry + object paths
  only — zlib-compressed `SGMTMRKRZLIB` container, streams inflate fine). Not a material
  extraction path, at least not via plain SaveDocument without the export dialog's settings.
- **`maxon.GraphDescription.ApplyDescription(graph, {...})` works on 2024** for authoring —
  `"$type"` accepts `"#<raw.asset.id>"` (hash prefix = raw ID, bypasses the en-US label
  lookup). But gradient/ramp VALUES are not settable: `c4d.Gradient` → "Unsupported graph
  description value type"; `maxon.GradientKnot()` can't even be constructed from Python here
  ("expected generic datatype capsule"). Scalar/simple port writes look viable; ramps aren't.
- **RS Environment triple-confirmed absent** in the tested scene at every level: zero
  `Orsenvironment`/`Orssky`/`Orsvolume` objects (API object walk), `.environment` port on the
  output node unwired (byte-level), zero env-related entries in the RS renderer videopost
  container (API). The three checks together are the template for "does this scene use an RS
  environment at all."

### Ramp Knot Values — ROOT CAUSE CONFIRMED: official Maxon SDK bug, not a technique gap

**2026-07-23, closed out via Maxon's own documentation.** Every API attempt at ramp knot values
(`FindChild("ramp").GetChildren()`, `FindChild("_0")`, flat traversal + `GetValue()` on
`ramp/_N/position` etc.) throws `no target to copy for '<net.maxon.graph.interface.graphmodel>'`
— tested exhaustively across a no-RS machine, a full-RS-installed machine, and again after fixing
a separate "Missing Asset" node-template-resolution issue. All three environments fail
identically. The Graph Descriptions Manual (`developers.maxon.net/docs/py/2024_3_0/manuals/
manual_graphdescription.html`) states outright: **"Variadic port references are currently
bugged, preventing both label and identifier references in some cases. It is also not possible
to create variadic ports at the moment."** A ramp's knot list is exactly this: a variadic
`Points` port on a `net.maxon.render.portbundle.spline`-typed bundle, each element itself a
`splinepoint` bundle (position/color/etc). **This is a documented Maxon SDK bug, not fixable by
any technique, RS install state, or asset-resolution fix on the tested C4D 2024.x line.**

The bug's wording changed by the 2026.0.0 docs to a narrower framing (0-based vs 1-based
indexing on variadic port *label* references, "will be fixed in the next release") — possibly
improved on C4D 2025/2026, but **unconfirmed**; don't assume fixed without testing on that
version specifically. If a newer C4D is ever available, retry the exact `FindChild`/flat-traversal
methods above first before falling back to anything else.

**What DOES work around this bug, in order of value:**
1. `UnknownDataType.ToString()` on the ramp's own top-level port value — gives knot *count* and
   *insertion-order IDs* (e.g. `{_0: insertindex 1, _1: insertindex 2, _3: insertindex 4}`),
   proving real per-instance data exists even though the position/color inside each knot stays
   unreachable via this API.
2. Byte-level scanning of the saved `.c4d` file (next section) — the only path that gets
   anywhere near the actual position/color values, though the value encoding itself remains
   uncracked (see below).
3. Manual UI edit + Save As + byte-diff — not yet executed, but the logical next step: since the
   API is confirmed structurally incapable of reading these values (not just "hard to find the
   right call"), diffing a before/after file pair is the only remaining way to learn the on-disk
   encoding without waiting on a Maxon SDK fix.

### Ramp Knot Values — CRACKED (2026-07-23, via controlled UI-edit + byte diff)

**Resolved.** The API is still broken (Maxon SDK bug, see above — that part never changed). But
the byte-level encoding is now fully confirmed via a controlled experiment: dragged one ramp knot
in the live C4D UI (0.5 → 0.4 position), saved a copy, and diffed against the original.

**Key finding: it's the exact same scalar record format already used for `hue`/`gamma`/`level`**
— marker `10 23 11 00 00` immediately followed by an inline little-endian float64. The edited
knot's position decoded as `9a 99 99 99 99 99 d9 3f` = `0.4` exactly (that repeating `99` byte
pattern is the IEEE754 signature of a decimal like 0.4 that isn't a clean power of 2 — a good
sanity marker when eyeballing hex for suspected float64 values). Right after it, `bias = 0.0` for
the same knot, same marker pattern.

**Why this looked uncrackable before:** the *original* file's ramp knots (before any UI edit,
saved via whatever pipeline originally authored the file) had **no position/bias override data
stored at all** for most knots — genuinely empty, not a different/harder encoding (matches the
"declaration only, no payload" pattern documented earlier in this doc). A fresh Cinema 4D 2024.2
save re-serializes the *entire* node graph in a much more verbose form — full type strings spelled
out (`float64`, `net.maxon.parametrictype.col<3,float64>`, `smoothknot`, `internedid`, etc.) where
they were previously terser/absent — and populates real values for every knot that has one. Two
different files, two different verbosity levels, same core value-record format underneath.

**Practical recipe for extracting real ramp data going forward:**
1. Fingerprint the target material's block using any already-known live value (see the
   fingerprinting method earlier in this doc) — re-verify per file, GUIDs and offsets shift on
   every resave since the whole graph re-serializes with different padding.
2. Within that block, scan for `10 23 11 00 00` (scalar) and `10 23 10 00 00` (start of a 3×
   float64 vector, e.g. knot color) — the same markers used for ordinary scalar overrides.
3. `position`/`bias`/`color` field-name strings are written out in full **only for the first
   knot encountered in the file**; subsequent knots' fields are unlabeled value records relying
   on interned string references — don't expect to find a literal `"position"` string next to
   every knot. Reconstruct grouping by proximity/order instead (color triple, then a scalar,
   then another scalar, repeating per knot), and cross-check against the API's
   `UnknownDataType.ToString()` knot-count/insertindex dict (still the only reliable "how many
   knots and in what slots" signal) to make sure you've accounted for all of them.
4. A `KNOT_LABEL` marker (a length-prefixed `_N` string, e.g. `_3`, followed by a 4-byte int32
   insertindex) appears near each knot's data but its exact position relative to that knot's
   fields (before vs. after) was inconsistent between the two ramps checked in this session —
   treat it as a confirmation anchor for which knot you're looking at, not a strict "data always
   follows/precedes this label" rule.

**Earlier false lead, corrected:** an initial pass on the *unedited* original file found small
`10 XX` two-byte clusters near knot strings (e.g. `10 9a`, `10 71`, `10 b0`) that looked like
possible local/interned-pool references distinct from the scalar-record format. The controlled
UI-edit experiment above superseded this — those files simply had no knot override data at all
for most knots; the clusters weren't a hidden reference format to crack, there was nothing there
to reference. Don't waste time on that theory again.

### Node Wire Connections — byte-level format (solves the "connections unreadable" gap)

Confirmed 2026-07-23 on the same file. A wire is stored as a **plain textual adjacency**, no
binary offset table:

```
<source node's own "...nodes.core.<type>.outcolor" port-declaration string>
<immediately followed by, no separator>
<destination node's "<type>@<GUID>" instance string>
<destination node's "...nodes.core.<type>.<inputport>" port-declaration string>
```

Real example (verified against known-must-be-true and independently-confirmed-live-API facts):

```
...nodes.core.rscolorcorrection.outcolor        <- source: rscolorcorrection's own output
rsramp@IghKm8vqLBHpLijl_lj4TI                    <- destination node instance
...nodes.core.rsramp.input                       <- destination port
```
decodes as: `rscolorcorrection.outcolor → rsramp@IghKm....input`.

When a node has already been fully declared earlier in the file (so its `.outcolor` string
already exists elsewhere), a later wire from that same node can appear as just the **bare
`type@GUID` instance string** immediately before the destination's port declaration, with no
repeated `.outcolor` label — e.g. `rsramp@BMFaQb...` immediately followed by
`standardmaterial@PZkm...opacity_color` with only type/flag bytes (no more text) in between.
Treat a bare node-instance string sitting immediately before a destination port declaration,
with no other source-port text intervening, as an implicit "this node's main output" wire.

**Practical extraction method:**
1. Extract every `<type>@<GUID>` and `<type>.port` string in file order within your pinned
   material's byte block (see the fingerprinting method above for pinning the block).
2. Walk them in order. Whenever a `...outcolor` (or bare node-instance) string is immediately
   followed by another node's `type@GUID` + input-port string with no other port declaration
   between them, that's a wire: `source → destination`.
3. **Don't trust file order alone as "signal flow order"** — a single source port can fan out to
   *multiple* destinations listed back-to-back (a real Y-split was found this way: one
   texturesampler's `outcolor` fed both a `rscolorcorrection.input` and a second ramp's `.input`
   directly, bypassing color-correction for that second path). Read the actual destination
   strings, don't assume the graph is a simple linear chain just because the task description
   said so — verify.

## RS Light Parameters

RS light **non-Filename** params read fine straight from the data container. A scene-wide
walk of all 19 lights in a production scene captured intensity/color/exposure/area for every
one. Key IDs (RS Light type id `1036751`):

| ID | Meaning | ID | Meaning |
|----|---------|----|---------|
| 10000 | light_type (3=area, 4=dome) | 11003 | temperature (K) |
| 10005 | visible_to_camera | 11004 | intensity |
| 10018 | intensity_multiplier | 11009 | area_width |
| 10031 | normalize_intensity | 11010 | area_shape |
| 10041 | exposure | 11019 | spread |
| 11000 | color (Vector RGB) | 11020 | softness |
| 11002 | color_mode | 11022 | contribution_mode |
| 12000 | dome_texture_0 (**Filename — see below**) | 11023 | contribution_scale |

```python
bc = light.GetDataInstance()
intensity = bc[11004]      # works
color     = bc[11000]      # works (c4d.Vector)
tex       = bc[12000]      # FAILS: "object unknown in Python" — Filename param
```

### Filename params on lights (the `12000`/`12008` trap)

The dome/area **texture** params are Filename-typed and the container iterator/subscript
throws `Parameter value not accessible (object unknown in Python)`. This is the same class
of failure as iterating an RS material container. Do **not** trust container subscript here.

Recovery order (most → least reliable):
1. **Node-graph / branch string-port walk** — the dome HDRI in recent RS lives in the
   maxon node graph or a `BaseShader` parked in a light branch (`GetBranchInfo`). Walk those
   and read string ports / shader container Filenames. This is the *proven* mechanism (same
   one that recovers `big_data.jpg` from materials).
2. `obj.GetParameter(c4d.DescID(c4d.DescLevel(12000)), c4d.DESCFLAGS_GET_0)` — sometimes
   succeeds where the subscript fails.
3. `str()` on whatever any of the above returns.

## Version / API Compatibility (2024–2026)

- **`c4d.Filename` was REMOVED.** In 2024–2026 it does not exist as a type. Code like
  `isinstance(v, c4d.Filename)` raises `module 'c4d' has no attribute 'Filename'` — this is a
  real crash seen in 2026. Guard with `getattr(c4d, "Filename", None)`.
- **Filename/texture params are returned as plain `str`** in 2026.3 (confirmed in the docs) —
  not `maxon.Url`, not a `Filename` object. So a `str`-first handler is correct; keep a
  `maxon.Url` fallback for in-between versions (2024 returned Url in some cases).
- `c4d.GenerateTexturePath(docpath, srcname, suggestedfolder)` still exists in 2026.3, returns
  `str`. The 3-arg call is safe (`service`/`bt` default). Use it to resolve `relative:///`.
- `DESCFLAGS_GET_0` vs `DESCFLAGS_GET_NONE` differ by version — resolve with `getattr`.
- **Check the docs for a specific version by editing the URL version segment**, e.g.
  `https://developers.maxon.net/docs/py/2026_3_0/modules/c4d/index.html` — swap `2026_3_0`
  for the version your machine (or a colleague's) runs. Always verify against the *actual*
  installed version, not memory.

## Animation Extraction (CTrack — renderer-independent)

Keyframes live on `CTrack` → `CCurve` → `CKey`, attached to **any** `BaseList2D` (objects,
tags, materials). This is **core c4d**, fully independent of Redshift — it works regardless of
renderer and never hits the Filename/maxon-typed failures. Walk every object AND every material
for exhaustive coverage (don't hand-pick objects).

```python
def dump_tracks(node, fps):
    out = []
    track = node.GetFirstCTrack()
    while track:
        desc = track.GetDescriptionID()           # which param is animated
        levels = [int(desc[i].id) for i in range(desc.GetDepth())]
        curve = track.GetCurve()
        keys = []
        for i in range(curve.GetKeyCount()):
            k = curve.GetKey(i)
            keys.append({
                "frame": k.GetTime().GetFrame(fps),
                "value": k.GetValue(),
                "tL": [k.GetTimeLeft().Get(),  k.GetValueLeft()],   # bezier tangents
                "tR": [k.GetTimeRight().Get(), k.GetValueRight()],
            })
        out.append({"name": track.GetName(), "param_levels": levels, "keys": keys})
        track = track.GetNext()
    return out
```

- `desc[i].id` (top level) often maps to a known param ID — e.g. an RS light intensity (11004)
  or DoF — so you can *label* the animated param using the light/material ID tables.
- `k.GetValue()` is for float curves; for data-typed keys fall back to `k.GetGeData()`.
- This replaces hand-curated keyframe JSON: an exhaustive walk catches animation on objects
  nobody thought to scan.

## Render-Level Post (videoposts) — NOT in lights/materials

Redshift's render post-processing — photographic exposure, tonemapping, in-render bloom/flare,
AOVs, OCIO/color management — lives in the **render-settings videopost stack**, not in any
light or material. Other grade posts (e.g. **Magic Bullet Looks**) sit in the same stack. Miss
this and you miss the entire RS post layer.

```python
rdata = doc.GetActiveRenderData()
vp = rdata.GetFirstVideoPost()
while vp:
    is_rs = vp.GetType() == 1036219          # Redshift render videopost type id
    bc = vp.GetDataInstance()                 # full post params (dump_container)
    # videoposts can be keyframed (exposure ramps) — run dump_tracks(vp, fps) too
    vp = vp.GetNext()
```

RS camera DoF (aperture/focus/lens offset — the bokeh gate) is on the **camera object container
or a Redshift Camera tag**, not the videopost.

## CUSTOMDATATYPE_RSFILE — texture path + colorspace + gamma

RS texture/file ports are a wrapped `CUSTOMDATATYPE_RSFILE` whose whole value is inaccessible in
Python. Read the **sub-channels** instead (per Maxon forum 16316). In the legacy GraphView/Xpresso
path: `node[pid[0].id, c4d.REDSHIFT_FILE_PATH]`, `..., c4d.REDSHIFT_FILE_COLORSPACE]`. In the
maxon node-space path, walk the port's child ports (`GetChildren()`) for `path`/`colorspace`/
`gamma` sub-ports. The colorspace (sRGB vs raw) is make-or-break for color matching.

## Node Connections (wiring) — best-effort only

There is **no clean public API** for graph wiring (Maxon forum 16316/15356: "no abstracted way
in Python"). `port.GetConnections(direction, ...)` exists in the maxon Nodes API but is
undocumented and signature-unstable across versions. Capture it inside try/except and accept that
it may yield nothing — port *values* are reliable, wiring is not.

## Takes — the silent mismatch trap

If the final render came from a non-base **Take** with material/render/camera overrides, an
active-document dump silently captures the wrong state. Always enumerate takes and flag overrides:

```python
td = doc.GetTakeData()
for take in <walk td.GetMainTake() children>:
    take.GetOverrides()         # list of BaseOverride (overridden nodes)
    take.GetRenderData(td)      # per-take render override
    take.GetCamera(td)          # per-take camera override
```

## Procedural (field / Xpresso) animation — CTracks don't see it

The CTrack walk only captures **keyframed** values. Field-driven effects (e.g. a Spherical Field
reveal) and Xpresso/expression drivers are procedural — you get the field's keyed `Size` but not
the falloff/remap relationship. Detect and flag them (Field objects by type-name; Xpresso tags by
`tag.GetType() == 1001149 (Texpresso)`) so you know the keyframe dump isn't the whole story.

## RS Environment — confirmed not extractable

Per Maxon forums 16316 and 15356, **Redshift Environment shader attributes are not exposed in
either the C++ or Python API.** A generic object-container dump catches the Environment object's
basic fields and any node-graph string-port file refs, but the true shader internals stay
unreadable. This is a Maxon-side limitation — do not burn time trying to enumerate them; read the
values off the rendered reference (MP4) instead.

## What a parameter dump fundamentally CANNOT give you

Be honest about the ceiling. A dump captures **inputs**, not the rendered **result**:
- The RS-rendered *look* (refraction, caustics, volumetrics, SSS, in-render bloom) is emergent —
  without Redshift installed you cannot render to see what the numbers produce. The reference
  MP4/stills stay the ground truth for appearance.
- **After Effects post** (grade, tritone, lens warp, flares, blend modes) is a separate app —
  not in any C4D/Redshift dump. The final-comp look is often AE-dominated.

## Reference Implementation

A complete, defensively-wrapped extractor combining all of the above lives at
`scripts/c4d/dump_redshift_lights.py` in the refraction repo. One run captures: lights, RS
material graphs (values + best-effort connections + RSFile sub-channels), cameras (incl. RS DoF),
render-settings videoposts (RS post + Magic Bullet grade), object tags (texture projection + RS
displacement), exhaustive CTrack animation, procedural-driver flags, takes (with override
warning), and `relative:///` → absolute asset resolution. Every pass is try/except-isolated so a
single unsupported API on a given version degrades to an empty field instead of aborting the dump
with a dialog traceback.

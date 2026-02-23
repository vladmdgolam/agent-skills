# MoGraph Baking Guide

This reference covers the mechanics of baking MoGraph animation to per-frame data. Read this when the main SKILL.md workflow is not enough — e.g., when dealing with large scenes, variable clone counts, or performance issues.

## Why Sequential Stepping Is Mandatory

MoGraph effectors (Random, Step, Formula, etc.) maintain internal state that is evaluated incrementally. The C4D scene graph does not store a precomputed result for each frame — it computes results on demand based on the current time. This means:

- Jumping directly to frame 50 without evaluating frames 0-49 gives **wrong results** for stateful effectors like Step Effector.
- The Random Effector with seed-based offsets is stateless — it appears to work when jumping frames — but any effector that accumulates state (Step, inheritance chains, fields with time offsets) will silently produce incorrect output.

**Always step 0 → N even if you only need a subset of frames.**

If you need only every 5th frame, still step through every frame but only store data on the frames you need:

```python
for frame in range(start, end + 1):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
    if frame % 5 == 0:
        # store data for this frame
        ...
```

## ExecutePasses Arguments

```python
doc.ExecutePasses(
    bt,           # BaseThread — pass None for main thread
    animation,    # bool — evaluate animation tracks
    expressions,  # bool — evaluate XPresso and Python tags
    caches,       # bool — evaluate caches (generators, cloners, deformers)
    flags         # c4d.BUILDFLAGS_NONE is the correct default
)
```

All three bool arguments should be `True` for MoGraph baking. Passing `False` for `caches` skips cloner evaluation entirely and `GeGetMoData()` will return stale or empty data.

## Chunked Baking Strategy

MCP scripts time out if they run too long (15-60 seconds depending on the server fork). For long animations or dense clone counts, split the bake into chunks and merge the resulting files.

### Chunk Size Guidelines

| Clone Count | Frames per Chunk |
|-------------|-----------------|
| < 50 clones | 500 frames |
| 50-200 clones | 200 frames |
| 200-500 clones | 100 frames |
| > 500 clones | 50 frames |

These are conservative estimates. Always test with a small range first and time it.

### Chunked Bake Script (Parameterized)

Run this multiple times with different `chunk_start` / `chunk_end` values:

```python
import c4d
from c4d.modules import mograph as mo
import json

CHUNK_START = 0    # change per run
CHUNK_END = 199    # change per run
CLONER_NAME = "MyClonerName"
OUTPUT_PATH = f"/tmp/bake_chunk_{CHUNK_START}_{CHUNK_END}.json"

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
cloner = find_obj(CLONER_NAME)
if cloner is None:
    print(f"ERROR: cloner '{CLONER_NAME}' not found")
else:
    mg = cloner.GetMg()
    frames_data = {}

    # ALWAYS start from frame 0 to ensure stateful effectors are correct
    for frame in range(0, CHUNK_END + 1):
        doc.SetTime(c4d.BaseTime(frame, fps))
        doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)

        if frame < CHUNK_START:
            continue  # step through but don't store

        md = mo.GeGetMoData(cloner)
        if md is None:
            print(f"Frame {frame}: no MoData — skipping")
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

        frames_data[str(frame)] = frame_clones

        if frame % 25 == 0:
            print(f"Progress: frame {frame}/{CHUNK_END}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            "chunk_start": CHUNK_START,
            "chunk_end": CHUNK_END,
            "fps": fps,
            "frames": frames_data
        }, f)

    print(f"Saved chunk to {OUTPUT_PATH}, frames: {len(frames_data)}")
```

### Merging Chunks

After all chunks are saved, merge with this script (run outside C4D, in a normal Python environment):

```python
import json
import glob
import os

chunk_files = sorted(glob.glob("/tmp/bake_chunk_*.json"))
if not chunk_files:
    print("No chunk files found")
    exit(1)

merged_frames = {}
fps = None
min_start = None
max_end = None

for path in chunk_files:
    with open(path) as f:
        chunk = json.load(f)
    fps = chunk["fps"]
    min_start = min(min_start, chunk["chunk_start"]) if min_start is not None else chunk["chunk_start"]
    max_end = max(max_end, chunk["chunk_end"]) if max_end is not None else chunk["chunk_end"]
    merged_frames.update(chunk["frames"])

output = {
    "fps": fps,
    "start_frame": min_start,
    "end_frame": max_end,
    "total_frames": len(merged_frames),
    "frames": merged_frames
}

with open("/tmp/bake_merged.json", "w") as f:
    json.dump(output, f)

print(f"Merged {len(chunk_files)} chunks → {len(merged_frames)} frames")

# Clean up chunks
for path in chunk_files:
    os.remove(path)
print("Chunk files removed.")
```

## Variable Clone Count

Object-mode cloners and cloners with animated count parameters can change their clone count per frame. Always check `md.GetCount()` rather than assuming a fixed count:

```python
md = mo.GeGetMoData(cloner)
count = md.GetCount()
matrices = md.GetArray(c4d.MODATA_MATRIX)
assert len(matrices) == count, f"Matrix array length mismatch: {len(matrices)} vs {count}"
```

If the count varies, your output JSON should store the actual count per frame. Downstream consumers (Three.js, etc.) must handle variable clone counts — typically by showing/hiding mesh instances beyond the current frame's count.

## Memory Management

For very large bakes (500+ clones × 1000+ frames), the `frames_data` dict can grow large. Consider writing results incrementally to a file rather than accumulating in memory:

```python
import json

OUTPUT_PATH = "/tmp/bake_streaming.json"

with open(OUTPUT_PATH, "w") as f:
    f.write('{"frames":{')
    first = True
    for frame in range(start, end + 1):
        doc.SetTime(c4d.BaseTime(frame, fps))
        doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
        md = mo.GeGetMoData(cloner)
        # ... build frame_clones list ...
        if not first:
            f.write(",")
        f.write(f'"{frame}":' + json.dumps(frame_clones))
        first = False
    f.write("}}") # close frames and root object

print("Streaming bake complete.")
```

Note: This produces valid JSON only if no exception is raised mid-loop. Wrap the loop in a try/except and write a sentinel if interrupted.

## Diagnosing Stateful vs. Stateless Effectors

To determine whether an effector is stateful (requires sequential stepping) or stateless (safe to jump to arbitrary frames):

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
cloner = find_obj("MyClonerName")
mg = cloner.GetMg()

def get_positions_at_frame(frame):
    doc.SetTime(c4d.BaseTime(frame, fps))
    doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
    md = mo.GeGetMoData(cloner)
    matrices = md.GetArray(c4d.MODATA_MATRIX)
    return [list(mg * m.off) for m in matrices]

# Method A: sequential
sequential_f10 = None
for f in range(0, 11):
    pos = get_positions_at_frame(f)
    if f == 10:
        sequential_f10 = pos

# Method B: jump directly
jump_f10 = get_positions_at_frame(10)

# Compare
match = all(
    abs(sequential_f10[i][j] - jump_f10[i][j]) < 0.001
    for i in range(len(sequential_f10))
    for j in range(3)
)
print("Stateless (jump safe):" if match else "STATEFUL — must step sequentially")
```

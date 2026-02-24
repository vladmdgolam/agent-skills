# Agent Skills

A collection of skills for AI coding agents. Skills are packaged instructions that extend agent capabilities with domain-specific knowledge.

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Install

```bash
npx skills add vladmdgolam/agent-skills
```

Or install a specific skill:

```bash
npx skills add vladmdgolam/agent-skills --skill cinema4d-mcp
```

## Available Skills

### cinema4d-mcp

Cinema 4D MCP expert for extracting scene data, writing C4D Python scripts, and controlling Cinema 4D through MCP tools.

**Use when:**
- Using Cinema 4D MCP tools (`get_scene_info`, `list_objects`, `execute_python_script`, etc.)
- Writing Python scripts for C4D extraction or manipulation
- Working with MoGraph cloners, effectors, and fields
- Baking animation data from C4D scenes
- Debugging C4D Python API errors

**Covers:**
- 7 critical C4D API gotchas (world/local coords, visibility constants, sequential stepping, etc.)
- MoGraph extraction and animation track discovery patterns
- When to use structured MCP tools vs `execute_python_script`
- Known error tables with fixes (Python API + MCP tool errors)
- Redshift availability matrix
- Timeout management and chunked baking strategies

### blender-mcp

Blender MCP expert for scene inspection, Python scripting, GLTF export, and material/animation extraction.

**Use when:**
- Using Blender MCP tools (`get_scene_info`, `execute_python`, `screenshot`, etc.)
- Writing Blender Python scripts for scene extraction or manipulation
- Exporting scenes to GLTF/GLB for web (Three.js, R3F)
- Debugging material or texture export losses
- Optimizing GLB files with gltf-transform
- Using asset integrations (PolyHaven, Sketchfab, Hyper3D Rodin, Hunyuan3D)

**Covers:**
- 7 critical rules (export timeouts, modifier handling, Draco pitfalls, name mapping, etc.)
- Scene hierarchy, material, and animation extraction patterns
- Headless CLI export (bypasses MCP timeout)
- Material export survival matrix (what survives GLTF, what doesn't)
- Texture optimization pipeline (resize → WebP → Draco)
- Known error tables with fixes (MCP, export, Python API, texture paths)

### time-lens

Analyze and visualize time spent on software projects by combining data from multiple sources: WakaTime coding time, git commit session detection, Claude Code usage, and Codex CLI usage.

**Use when:**
- Analyzing work hours or calculating time spent on a project
- Generating a work hours report or visualizing coding activity
- Creating a project time breakdown
- Summarizing development effort across date ranges

**Covers:**
- 4 data sources: WakaTime API, git sessions, Claude Code prompts, Codex CLI prompts
- Interactive HTML dashboard (dark-themed, Chart.js)
- Markdown report with ASCII charts
- Reconciliation logic across overlapping sources

### visual-feedback-loop

AI agent visual feedback loop for capturing and inspecting rendered output from any web app during iterative development.

**Use when:**
- Iterating on visual code (UI, canvas, 3D, SVG, charts, animations)
- You need to SEE the rendered result to evaluate quality
- Doing visual QA or A/B comparison of render variants

**Covers:**
- Dev-screenshot API pattern (GET trigger → SSE → client capture → POST back → file saved)
- Parameterized offscreen rendering with custom params
- WebMCP tool registration for Chrome Canary agents
- Console and Chrome MCP fallbacks
- Next.js reference implementation

## Adding Skills

Each skill lives in `skills/<skill-name>/` with a required `SKILL.md` and optional `references/`, `scripts/`, and `assets/` directories.

## License

MIT

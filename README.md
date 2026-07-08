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

### 🎬 cinema4d-mcp

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

### 🧊 blender-mcp

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

### ⏱️ time-lens

Analyze and visualize time spent on software projects by combining data from multiple sources: WakaTime coding time, git commit session detection, Claude Code usage, Codex CLI usage, and Cursor IDE usage.

**Use when:**
- Analyzing work hours or calculating time spent on a project
- Generating a work hours report or visualizing coding activity
- Creating a project time breakdown
- Summarizing development effort across date ranges

**Covers:**
- 5 data sources: WakaTime API, git sessions, Claude Code prompts, Codex CLI prompts, Cursor IDE prompts
- Interactive HTML dashboard (dark-themed, Chart.js)
- Markdown report with ASCII charts
- Reconciliation logic across overlapping sources

### 🖨️ pdf-look-scanned

Make PDF documents look like they were scanned on a physical scanner, with optional signature replacement.

**Use when:**
- Making a PDF look scanned (grayscale, noise, blur, rotation, edge shadows)
- Replacing digital signatures with real handwritten ones from a source PDF
- Preparing documents that need a "printed and scanned" appearance

**Covers:**
- Configurable scan effects (DPI, noise, blur, contrast, JPEG quality)
- Signature extraction from source PDFs (phone photos, scans)
- Multi-signature replacement on different pages
- Coordinate discovery workflow for signature placement
- Metadata considerations

### 🎨 figma-context-mcp

Expert guide for using the Figma Context MCP (Framelink) efficiently while avoiding 429 rate-limit errors.

**Use when:**
- Using Framelink Figma MCP tools (`get_figma_data`, `download_figma_images`)
- Fetching Figma designs for code generation
- User hits 429 rate limits from Figma API
- Extracting design tokens or component data from Figma
- Downloading Figma assets/images
- Any design-to-code workflow involving Figma URLs

**Covers:**
- Metadata-first, prune-first, fetch-last pipeline (2-3 API calls instead of dozens)
- Depth-limited node tree fetching to keep responses <500 KB
- Batch image downloads with deduplication
- Plan-tier awareness (limits tied to file owner's plan, not yours)
- Rate-limit diagnostics and recovery steps
- Common anti-patterns that cause 429 lockouts
- Alternative workflows when rate-limited (screenshots, manual export)

### 📚 apple-books-mcp

Extracts highlights, annotations, and book data from Apple Books via MCP.

**Use when:**
- Exporting book highlights with colors and notes
- Extracting annotations from specific books or a reading list
- Searching highlights across your entire library
- Matching books from an external list against Apple Books library

**Covers:**
- Efficient batch color extraction (5 API calls instead of 150+)
- Color map building via `get_highlights_by_color` + Python cross-referencing
- Annotation data structure (style values, color mapping, underlines)
- Markdown export patterns with color-coded emoji indicators
- Book matching strategies (translations, partial titles, multiple editions)
- Troubleshooting common issues (empty results, null colors, large outputs)

### 👁️ visual-feedback-loop

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

### 🪛 reverse-engineer-js

LLM-assisted deobfuscation of minified or obfuscated JavaScript bundles. Wraps [humanifyjs](https://github.com/jehna/humanify) with the right defaults, the pseudo-TTY workaround, and patterns for both whole-bundle and single-module workflows.

**Use when:**
- Deobfuscating `bundle.js`, fxhash projects, or any minified JS
- The user says "humanify this", "deobfuscate this", "rename mangled vars", "what does bundle.js do"
- Working in a project with an `og/` or `modules/` folder fed by humanify
- humanify crashed with `cursorTo is not a function`

**Covers:**
- Default model: `gemini-3.1-flash-lite-preview`
- Pseudo-TTY workaround (`script -q /dev/null ...`) for non-interactive shells
- Single-module extraction from large bundles
- `webcrack` pre-split for webpacked bundles
- Sourcemap-first check (often beats LLM rename for free)
- Common backends: gemini / openai / local

### 🔍 agent-sessions

Search, list, and resume AI agent sessions across Claude Code, Codex CLI, Gemini CLI, opencode, Hermes Agent, and Cline CLI from the terminal.

**Use when:**
- Finding a past conversation ("find that session where I worked on...")
- Reading latest/last messages from a session id (`ses_...`, UUID, or Cline id)
- Resuming a previous Claude Code session by ID
- Listing recent activity across agents
- Searching session history for a topic or project

**Covers:**
- CLI tool at `~/Play/radar/tools/agent-sessions` with `--agent`, `--search`, `--search-scope`, `--project` filters
- Direct handoff flow: `--pack <session-id> --max-chars 8000` before manual filesystem or database inspection
- Compact JSON output for scripting; `--include-search-text` is opt-in for transcript indexes
- Compact handoff snippets via `--context <session-id...>`
- Bounded evidence packs and excerpts via `--pack <id...>` and `--read <id...> --query`; use `--role user` for user-only messages
- Claude session resume via `--resume <id>`
- Data sources: `~/.claude/projects/`, `~/.codex/sessions/`, `~/.gemini/tmp/*/chats/`, `~/.local/share/opencode/opencode.db`, `~/.hermes/state.db`, `~/.cline/data/db/sessions.db`
- Companion tools: `claude-history` (TUI), Claude Code History Viewer (GUI)

### 🌊 fluid-interfaces

Design and review principles for fluid, gestural, physically-responsive interfaces, distilled from Apple's WWDC 2018 "Designing Fluid Interfaces" talk (the team that built the iPhone X gestural UI).

**Use when:**
- Designing or reviewing touch/gesture interactions (drag, swipe, dismiss, dock)
- Tuning spring-based motion, elastic/rubberband behaviors, or scroll physics
- Something "feels off", "feels janky", or "doesn't feel native"
- Deciding between timed animations and continuous spring behaviors

**Covers:**
- 8 core principles: instant response, redirectability/interruption, spatial consistency, gesture hinting, lightweight-input/amplified-output, rubberbanding, smooth frames of motion, behavior-over-animation
- Spring tuning via `damping`/`response` instead of raw mass/stiffness/duration
- Momentum projection formula for "throw to nearest endpoint" interactions (with Swift code)
- Gesture mechanics checklist: taps, swipes, one-to-one tracking, continuous feedback, resolving competing gestures
- Teaching techniques for gestural UI (visual cues, elevation, paired animations, explanations, designing for play)

## Adding Skills

Each skill lives in `skills/<skill-name>/` with a required `SKILL.md` and optional `references/`, `scripts/`, and `assets/` directories.

## License

MIT

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

## Adding Skills

Each skill lives in `skills/<skill-name>/` with a required `SKILL.md` and optional `references/`, `scripts/`, and `assets/` directories.

## License

MIT

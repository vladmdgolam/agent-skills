# agent-skills repo

Collection of Claude Code / multi-agent skills published to [skills.sh](https://skills.sh).

## Installing skills via `npx skills`

`npx` is aliased to `nvm` in this shell — use the full binary path:

```bash
~/.nvm/versions/node/v22.21.1/bin/npx skills <command>
```

### Install this repo's skills globally to Claude Code

```bash
~/.nvm/versions/node/v22.21.1/bin/npx skills add vladmdgolam/agent-skills -g -a claude-code -y
```

### Install a specific skill

```bash
~/.nvm/versions/node/v22.21.1/bin/npx skills add vladmdgolam/agent-skills --skill time-lens -g -a claude-code -y
```

### List installed skills

```bash
~/.nvm/versions/node/v22.21.1/bin/npx skills list
```

## Adding a new skill

See `references/building-skills-guide.md` for the complete guide to building skills (frontmatter, progressive disclosure, composability, testing, distribution).

1. Create `skills/<name>/SKILL.md` with `name` and `description` frontmatter
2. Add scripts/references/assets as needed
3. Update `README.md` with the new skill entry
4. Commit and push
5. Install globally: `~/.nvm/versions/node/v22.21.1/bin/npx skills add vladmdgolam/agent-skills --skill <name> -g -a claude-code -y`

Skills appear on [skills.sh](https://skills.sh) after push + install (install count tracks discoverability).

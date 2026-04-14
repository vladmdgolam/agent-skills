https://github.com/sobotka/blender-addons-contrib

/Users/vladmdgolam/Play/flowers-p

- lets run time
  tracker for this directory and its directories that
  contain .git folders

❯ is wakatime counted for this and all of the folders that are here? i meean  
 sber-experiments, bloom-metal

⏺ Good question. I only queried WakaTime with --project sber-experiments, which may  
 have missed sub-projects tracked under different names. Let me check what WakaTime  
 project names exist.

# ~~are skills os-specific? should be cross-platform~~ DONE

# ~~also should be framework-agnostic~~ DONE

## visual-feedback-loop enhancements

- [ ] **pixelmatch diffing** — save golden screenshots, diff against new captures, output mismatch % + diff image. Pure JS (`pixelmatch`), zero deps. Could wire into `pnpm chamfer:regression`. Highest value, lowest effort.
- [ ] **headless single-letter render** — use `headless-gl` + Three.js in Node to render isolated letters without a browser. Won't work for full scene (needs env maps) but covers the `?letter=` endpoint.
- [ ] **Gemini API visual comparison** — send before/after screenshots to a vision model for semantic QA ("did the artifact improve?"). Useful for batch/automated QA. Lower priority since the agent can already do this via `Read`.
- [ ] **Maybe add commit hash + hashsum (uncommited chandes) for screenshots** — helps track which code changes caused visual regressions. Could be added to the screenshot metadata or filename.

https://davidgomes.com/cursor-debug-mode/

## new skills ideas

- [ ] **`/document-knowledge`** — distills everything Claude learned in the conversation into a structured `.md` file saved to disk. Useful after codebase exploration, debugging, research, design discussions.
- [ ] **`/update-claude-md`** — appends thoughts/instructions to the nearest `CLAUDE.md`. E.g. `/update-claude-md always use pnpm` → finds CLAUDE.md and adds it cleanly.

---

/report - will upd \ create a report
/copy - will copy improtant stuff to clipboard via pbcopy

visual explainer 
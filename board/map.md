# Board Lookup Map

Read only the row required by your current task. Paths resolve relative to `{{WORKSPACE_ROOT}}`.

## Shared Artifacts

| Artifact | Location |
|---|---|
| PRDs | `{{PLANNING_DIR}}/ready/` (`Draft` → `Ready for Implementation` → `In Review`) → `archive/` · queue in `progress.md` |
| PRD Template | `{{PLANNING_DIR}}/_template_prd.md` |
| Manager Decisions | `{{PLANNING_DIR}}/notes/<date>-<slug>-decisions.md` |
| Execution State & Proofs | `{{PLANNING_DIR}}/runs/` |
| UI HTML Options | `{{PLANNING_DIR}}/design/<slug>/` |
| Notes (research, copy) | `{{PLANNING_DIR}}/notes/` |
| Project Sheet | `{{PLANNING_DIR}}/project-sheet.md` |
| Brand Voice | `templates/voice/brand-voice.md` |
| Visual Taste & Anti-Slop | `templates/design/taste-rules.md` · `templates/design/anti-slop.md` |

## Skills by Role

| Role | Preload | On Demand |
|---|---|---|
| Manager | `grill-me`, `concise-output` | `product-eval`, `maestri-manager`, `maestri-routines`, `canvas-manager`, `canvas-retro` |
| Explorer | — | `prd`, `prd-ship`, `epic-ship`, `commit`, `deep-research`, `audit-codebase`, `infra-preflight`, `verify-claims` |
| Writer | `humanizer` | `humanizer-compact` |
| Designer | — | `design-decide`, `design-port` |
| Dev | — | `design-port`, `tdd-workflow`, `react-doctor`, `infra-preflight`, `commit` |
| QA | — | `prd-ship`, `verify-ui`, `security-review`, `prd-demo`, `maestri-portal` |

## Project Configuration (`{{PROJECT_NAME}}`)

| Dimension | Value / Path |
|---|---|
| Repository & Rules | `{{PROJECT_DIR}}` · `CLAUDE.md` |
| Development Directories | `{{DEV_DIRS}}` |
| Local Stack | `docker compose up -d` at `{{PROJECT_DIR}}` (if containerized) |
| QA Browser | Portal `QA` (`maestri-portal`) + headless Playwright for repeatable flows |
| Rollout & Guardrails | `{{WORKSPACE_ROOT}}/.maestri/board/rollout-manual.md` + `hooks/prod-guard.py` via `settings/rollout-settings.json` |
| Sprint Metrics | `{{PLANNING_DIR}}/runs/sprint-metrics.md` |

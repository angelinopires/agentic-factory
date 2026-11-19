---
name: init-board
description: Hybrid interactive onboarding for Agentic Factory. Runs scripts/diagnose.py to inspect installed AI CLIs (maestri, claude, codex, agy) and repository topology, interviews the user on topology, active roles, language, and production markers, writes board.config.json, and compiles the Maestri board via scripts/compile-board.py.
---

# `/init-board` — Hybrid Board Onboarding & Compiler

Use this skill to bootstrap or reconfigure an **Agentic Factory** Maestri board on any new or existing repository.

## Workflow

### Step 1 — Run Environment & Repository Diagnosis

Run `scripts/diagnose.py` against the target repository path (defaults to current working directory):

```bash
python3 scripts/diagnose.py --repo <target-repo-path> --json
```

Read the JSON report:
- `maestri_installed`: whether the Maestri CLI is available in `PATH`.
- `installed_ai_clis`: detected AI CLIs among `claude`, `codex`, and `agy`.
- `routing_mode`: `"multi-harness"` (when ≥2 AI CLIs are installed) or `"single-harness"` (when only 1 AI CLI is installed, mapping all active roles across that provider's model tiers).
- `topology_recommendation`: `"workspace"` (parent directory holds `planning/` and `projects/`) or `"single-repo"` (standalone repository with sibling or git-excluded `planning/` so `prd/<n>` feature branches never diverge `planning/` state).
- `is_monorepo` / `split_dev_recommended`: whether `web/`+`server/` (or `frontend/`+`backend/`) split directories exist.
- `has_ui`: whether frontend frameworks (React, Next.js, Vite, Tailwind, Vue, Svelte) were detected.
- `lockfiles`: detected dependency lockfiles for cryptographic `qa-proof.py` binding.

### Step 2 — Interview the User (Confirm Configuration)

Present the diagnosis summary and ask the user to confirm or adjust the 4 key configuration axes (using numbered options):

1. **Topology & Planning Location:**
   - `(Recommended)` Use the detected topology (`workspace` vs `single-repo`) and planning path (`../planning/<project>` or `./planning/<project>` excluded via `.git/info/exclude`).
2. **Board Roster (Modular Roles):**
   - Core roles (`Manager`, `Explorer`, `Dev`, `QA`) are always enabled.
   - Ask whether to enable:
     - `Dev Front` + `Dev Back` split (recommended if `split_dev_recommended` is `true`)
     - `Designer` (recommended if `has_ui` is `true`)
     - `Writer` (recommended for user-facing products with brand copy)
     - `Rollout` + `VPS` (recommended if the project is deployed to a live production server)
     - `Reviewer` (recommended in `multi-harness` mode for blind dual research and second opinions)
3. **Conversational Language:**
   - Language in which the Manager communicates with the user (`en`, `pt-BR`, `es`, etc.), while keeping all repository code, commits, and role mechanics in English.
4. **Skill Installation Scope & Production Guardrails:**
   - Install portable skills at `project` level (`.claude/skills/`, `.agents/skills/`) or `global` level (`~/.claude/skills/`, `~/.agents/skills/`, `~/.gemini/config/skills/` with automatic backup of existing files).
   - If `Rollout` is enabled, collect production markers (hosts, domains, compose files, health URL) for `hooks/prod-guard.py`.

### Step 3 — Write `board.config.json`

Construct `board.config.json` following the canonical schema in `board.config.example.json`:
- Populate `project_name`, `language`, `topology`, `paths`, `maestri`, `roles`, `routing`, `qa_proof`, `context_ceiling`, and `production`.
- When `routing.mode` is `"single-harness"`, assign all active roles to the single installed CLI using `"high"` tier for `Manager`, `"browser"` tier (`--chrome` if Claude) for `QA`, and `"medium"` tier for workers.

### Step 4 — Validate Budgets & Compile the Board

Run the budget check and board compiler:

```bash
python3 scripts/compile-board.py --check-budgets
python3 scripts/compile-board.py --config board.config.json --out <workspace_or_repo>/.maestri --install-skills <project|global>
```

### Step 5 — Report Next Steps

Print the generated files and the exact startup sequence for the user:
1. Run `<out>/board/assemble-roles.sh` inside the Maestri workspace to register the compiled role prompts.
2. Start the **Manager** terminal with Maestro mode enabled.
3. Run `<out>/board/recruit.sh` from the Manager terminal to spawn and connect the active board roster.

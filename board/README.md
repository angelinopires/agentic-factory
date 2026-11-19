# Unified Maestri Board

One workspace per project. The **Manager** is the sole team lead, connected to every terminal on the canvas.

| Team | Terminal | Default Model / Harness | Prompt Source |
|---|---|---|---|
| Lead | Manager | Claude Opus 5.5 (`effort medium`, Maestro mode) | `manager.md` |
| Product | Explorer | Antigravity Gemini 4 Neon High (fallback: Claude Sonnet 5.5) | `explorer.md` |
| Product | Writer | Antigravity Gemini 4 Neon High (fallback: Claude Sonnet 5.5) | `writer.md` |
| Product | Designer | Codex GPT-6.1 Sol (`effort medium`) | `designer.md` |
| Engineering | Dev (`Dev Front` · `Dev Back` or unified `Dev`) | Codex GPT-6.1 Sol (`effort medium`; fallback: Claude Sonnet 5.5) | `dev.md` |
| Engineering | QA | Claude Sonnet 5.5 (`--chrome`) | `qa.md` |
| Engineering | Rollout (+ human `VPS` shell terminal) | Claude Sonnet 5.5 | `rollout.md` + `rollout-manual.md` |

All terminals are persistent and reset at PRD boundaries. One PRD executes at a time on a `prd/<n>` branch in the project repository. There is no separate Orchestrator, Planner, or Secretary: the Explorer authors and closes PRDs in `{{PLANNING_DIR}}`, and Devs commit code. Every terminal's role prompt equals `core.md` concatenated with its role file. On-demand reference files: `playbook.md`, `map.md`, `plan.md`, `qa-manual.md`.
Word budgets: `core.md` <= 500 words (target ~300), role files <= 400 words each, `playbook.md` <= 120 lines. Long post-mortems live in `cases.md` (read only by the Manager).

## Assemble Roles

Use `V=create` on first setup; `V=write` to update an existing role (restarts the terminal immediately — run only when idle).

```bash
B={{WORKSPACE_ROOT}}/.maestri/board; V=create
for p in manager:Manager explorer:Explorer writer:Writer designer:Designer qa:QA; do
  maestri role $V "${p#*:}" "$(cat $B/core.md $B/${p%%:*}.md)"; done
maestri role $V "Dev" "$(cat $B/core.md $B/dev.md)"
maestri role $V "Rollout" "$(cat $B/core.md $B/rollout.md $B/rollout-manual.md)"
```

## Recruit Terminals

The human creates the **Manager** terminal manually (preset `Claude Code`, cwd at project root, **Maestro mode enabled**):
`claude --model claude-opus-5-5 --effort medium --permission-mode auto --remote-control "Manager"`.
The Manager recruits the rest of the board (or runs the generated `recruit.sh` from `scripts/compile-board.py`):

```bash
R={{PROJECT_DIR}}; B={{WORKSPACE_ROOT}}/.maestri/board
C='claude --model claude-sonnet-5-5 --permission-mode auto --disallowedTools SendMessage'
X='codex -p maestri -m gpt-6.1-sol -c model_reasoning_effort="medium" --approve-for-me'
G="agy --add-dir {{WORKSPACE_ROOT}} --mode auto --settings $B/settings/agy-settings.json --model"
maestri recruit "Explorer"  --preset "Antigravity" --command "$G gemini-4-neon-high" --role "Explorer" --dir $R
maestri recruit "Writer"    --preset "Antigravity" --command "$G gemini-4-neon-high" --role "Writer" --dir $R
maestri recruit "Designer"  --preset "Codex" --command "$X" --role "Designer" --dir {{PLANNING_DIR}}
maestri recruit "Dev Front" --preset "Codex" --command "$X" --role "Dev" --dir $R/web
maestri recruit "Dev Back"  --preset "Codex" --command "$X" --role "Dev" --dir $R/server
maestri recruit "QA"        --preset "Claude Code" --command "$C --chrome --strict-mcp-config --settings $B/settings/qa-settings.json" --role "QA" --dir $R
maestri recruit "Rollout"   --preset "Claude Code" --command "$C --settings $B/settings/rollout-settings.json" --role "Rollout" --dir $R
maestri recruit "Reviewer"  --preset "Antigravity" --command "$G gemini-4-argon-medium" --role "Explorer" --dir $R
maestri connect "QA" "Dev Front"; maestri connect "QA" "Dev Back"
```

> **Antigravity (`agy`) sandbox note:** `--mode auto` enables the terminal sandbox; `settings/agy-settings.json` allows `docker`, `maestri`, and `git` outside the sandbox without interactive prompts while `hooks/pre-tool-use.js` enforces hard safety blocks (`git push`, `--amend`, `hooksPath`, `compose down`, `rm -rf`, `sudo`, `prod-guard`). Before recruiting any `agy` terminal, pre-trust role folders with `python3 {{WORKSPACE_ROOT}}/scripts/agy-trust.py`.

## Quota Fallbacks & Connections

- **Connections:** `maestri recruit` automatically links terminals to the Manager. Connect QA directly to Dev terminals (`maestri connect "QA" "Dev Front"` / `"Dev"`) so QA and Dev resolve HOLD loops without Manager bottlenecks. For Rollout, the human links a standard shell terminal (`VPS`) to `Rollout` on the canvas.
- **Quota Fallbacks:** The Manager swaps providers automatically on quota exhaustion, logs the swap in `notes/`, and restores defaults upon reset:
  - Claude Code exhausted: Explorer/Writer/Rollout/Dev Front switch to `Antigravity` (`$G claude-sonnet-5-5-high`). QA waits (requires `--chrome`).
  - Codex exhausted: Designer switches to `$G gemini-4-neon-high`; Dev switches to `$G claude-sonnet-5-5-high`.
  - Single-harness mode: When only one AI CLI is installed, `compile-board.py` maps all active roles across that CLI's model tiers (`high` / `medium`).

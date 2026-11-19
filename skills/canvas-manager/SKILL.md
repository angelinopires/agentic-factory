---
name: canvas-manager
description: Start or resume the Maestri board Manager for a project (single-board architecture where the Manager is the sole product and engineering lead) — adopts the role, reads on-disk state, resets idle terminals, and reports status in 3 lines. Usage: /canvas-manager [project] [resume <file>], defaulting to the project in board.config.json; the role comes from the terminal name. Does NOT close the session (that is /canvas-retro).
---

# Canvas Manager

Arguments: `$ARGUMENTS` — project (empty → `project_name` from `board.config.json`) and, optionally, `resume <file>`.
Board files resolve from `.maestri/` (compiled from `board/` and `scripts/`).

## Role

Run `maestri list`: your name in `You:` selects your row. If your name is not in the table, stop and ask the user which role to adopt.

| You | Role (read in full and adopt; the 1st file wins on contradiction) | State |
|---|---|---|
| Manager | `board/core.md` + `board/manager.md` | `planning/<project>/progress.md` + today's `runs/` + connected Maestri notes |

## Steps

1. Read the role files and adopt them. Read `board/playbook.md` and `board/map.md` only when the role file instructs you to.
2. Read the state for your row and the "Pending" section of the latest retro `.maestri/retros/*-<project>.md` (if no retro exists for the current board yet, read the most recent retro of any suffix). With `resume <file>`: read the file and continue from its next step.
3. Startup procedure from `board/playbook.md` ("Startup"): run `maestri check` on every terminal; apply any `role write` pending from the retro and reset only idle terminals (no `ORDER` in flight). If a terminal link is missing on the canvas, ask the user to connect it.
4. **Role gate, before the 1st `ORDER` to each role in the session:** run `python3 scripts/role-check.py <Role>` (or `.maestri/scripts/role-check.py <Role>`).
   Exit 0 → dispatch via `python3 scripts/order.py`. Exit ≠ 0 → do not dispatch to that terminal: while the terminal is idle, run `maestri role write` for that role (`board/README.md` §Assembling Roles) and re-run the check. If Rollout is out of sync, remote operations stay with the user until the check passes.
5. Report the state to the user in 3 lines (in flight, next up, what you need from them).

## Harness portability

- `AskUserQuestion` → ask in plain text with numbered options and one open option.
- `maestri` CLI commands work identically across Claude Code, Codex, and Antigravity.

---
name: canvas-retro
description: Close the Manager's cycle on a project's Maestri board (single-board architecture) — verifies terminals are idle, writes the session retrospective in .maestri/retros/, evaluates the rules exercised during the session, proposes Kaizen rule changes to the user, and cleans up state. Use when the user says /canvas-retro, "close the session", "end the cycle", or "wrap up the day". Does NOT reset terminals (that is /canvas-manager).
---

# Canvas Retro

Closes the leader's cycle to save tokens and preserve learning. Kaizen principle: prompts do not need to be bulletproof upfront; they need to improve slightly every cycle, including shedding rules that no longer earn their keep. **Never resets any terminal.**

Evidence comes strictly from your current session context + the on-disk state for your row below. Do not read raw session transcripts and do not ask agents for self-evaluations. Board paths resolve from `.maestri/` (seeded from `board/`).

## Board

Run `maestri list`: your name in `You:` selects your row.

| You | Retro suffix | On-disk evidence | Rules you evaluate | Core (line-budget brake) | Cases | Explore goes to | Cleanup |
|---|---|---|---|---|---|---|---|
| Manager | `-<project>` | `planning/<project>/history.md`, today's `runs/`, `runs/sprint-metrics.md`, today's notes | `board/*.md` | `board/core.md` + `board/manager.md` | `.maestri/board/cases.md` (create on 1st case) | Explorer (Manager's team) | Maestri notes for closed tasks |

The Manager is the sole board leader: the retrospective covers both product and engineering.

## 1. Terminals (read-only)

Run `maestri list` and `maestri check` on every connected agent. Build the table `terminal | idle? | working on | context`.
If any terminal is busy → the retro (steps 2–4) proceeds, but cleanup (step 5) is blocked: state who is busy and on what. Nothing is interrupted.

## 2. Session retrospective file

Write `.maestri/retros/YYYY-MM-DD-HHMM<suffix>.md`, short (≤ 40 lines), no fluff:

```markdown
# Retro YYYY-MM-DD HH:MM — <session theme in 3-6 words>
## Worked on
- <what entered and exited: PRD, note, screen, decision; with # and commit hash>
## How
- <path taken: who executed, how many rounds, gates, where it stalled>
## Results
- <numbers: PRDs closed or ready, rounds with the user, rework, permission prompts, quota per pool when known>
## Learnings
- ✅ <what worked — repeat>
- ❌ <what went wrong> → fix | explore | observe
## Rules touched
- <file:section> — helped | hindered | ignored | missing → keep | adjust | cut
## Gate decisions
- <change> — approved | rejected | adjusted
## Pending
- <pending role write + --replace, notice to next session>
```

At most 3 ❌ items, each assigned to one destination:
- **fix**: rule change sent to the gate in step 4.
- **explore**: dispatched to the role in the "Explore goes to" column on the next cycle.
- **observe**: recorded only in the retro file. Before classifying as observe, `grep` the theme across the 5 previous retros **with the same suffix**; if it repeated 2x, promote it to **fix**.

## 3. Rules touched

Evaluate only the rules exercised during this session across the files in your row. For each rule: whether it helped, hindered, was ignored, or was missing. The verdict is keep, adjust, or cut. Do not run a full sweep of untouched rules.

## 4. Change gate

Send each proposal (from ❌ **fix** or a rule to adjust/cut) to the user via `AskUserQuestion`, up to 4 per round.
Each question includes a short diff in `preview` and the options `apply` / `reject` / `adjust`. Apply only what the user approves, in the same turn.

- **Line-budget brake:** across the core files for your row, net line delta must be ≤ 0. Every new line is paid for by a cut or merge (a rule that became habit, a duplicate, or a rule that never fired). `board/playbook.md` stays at ≤ ~100 lines; if it exceeds that, trim in the same proposal. Role files stay at ≤ 400 words and `board/core.md` at ≤ 500 words.
- **Incident details go to `cases.md`**, never into the rule file itself. The rule keeps only the date and a single line.
- **Another role's prompt changed:** record it under `## Pending` (the Manager, on the next `/canvas-manager`, runs `role write` + `--replace` on idle terminals). Do not reset terminals here.
- Record every decision under `## Gate decisions`.

## 5. Cleanup (only when all terminals are idle)

- Follow the "Cleanup" column for your row. For Maestri notes to delete: present a single list in `AskUserQuestion` ("Delete these N notes?"). Delete only the approved ones. Never delete a floor (landing is the user's decision); for an already-merged git branch: `git branch -d`.
- Routines: check `maestri routine list` and list any leftover one-shot auto-reset routines that have already fired.
- `planning/`: run `git -C planning status --short`; commit in logical groups (PRDs + queue, notes, screens), in English, conventional commits, without pushing. Invoking `/canvas-retro` is already authorization to commit board planning state (the Explorer commits `/prd-ship` accounting). Record the commit hash in step 6.

## 6. Close

Present a short table to the user: terminals, retro file path, changes applied and rejected, notes deleted, and items left in `Pending`. Final line: **"Ready for `/clear` + `/canvas-manager`."**

## Harness portability

- Leader skill (Claude Code). In Codex or Antigravity: `AskUserQuestion` → ask in plain text with numbered options and one open option.
- `maestri` CLI commands work identically across all harnesses.

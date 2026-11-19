---
name: canvas-sprint
description: Start or resume an autonomous sprint on the Maestri board — executes Ready PRDs sequentially, one at a time, each with full QA, nothing merged to main; the user reviews at the end (merge, adjust, or discard). Usage: /canvas-sprint <area> <#PRD…> (start, usually triggered by a routine) | /canvas-sprint --continue <area> (resume). Manager terminal only. Does NOT plan the sprint (that happens with the user beforehand) or close the session (/canvas-retro).
disable-model-invocation: true
---

# Canvas Sprint

Arguments: `$ARGUMENTS`. Read `board/core.md` + `board/manager.md` (from `.maestri/board/`) and adopt the Manager role.

Paths resolve from `board.config.json`: project `<project>`, repo `R=<paths.project_dir>`, sprint run log `F=planning/<project>/runs/<date>-sprint-<area>.md`.

**Invoking `/canvas-sprint` with named PRDs is the user's authorization** to execute them (not to merge). The sprint was planned with the user beforehand; do not reopen settled decisions.

**Zero questions to the user during the sprint.** All questions happen before scheduling, during the planning conversation. If a new decision arises mid-sprint: pick the recommended option (the most conservative and reversible choice, without touching `main` or production), record in `F` `"Manager Decision: <what>, <why>, alternative <X>"`, and continue; it will appear in the final test note for the user to review. Actions that only the user can perform (merge to `main` when gated, `git push`, production writes) wait until the End phase without interrupting the sprint. Do not call `AskUserQuestion` or `maestri notify` asking for decisions until the End phase.

## Start (`<area> <#PRD…>`)

1. **Precondition:** run `maestri list` (confirm Dev / Dev Front + Dev Back and QA are connected) and `git -C $R status --short`. A dirty working tree does not block (record it in `F`); only an in-progress merge or rebase blocks.
2. **Filter:** every named PRD must exist in `planning/<project>/ready/` with `**Status:** Ready for Implementation` and have no `🔒` user/PENDING lock in `planning/<project>/progress.md`. If a PRD fails the filter → drop it from the sprint, record why in `F`, and proceed with the remaining PRDs.
3. **Quota:** check provider quota via the command in `board/playbook.md` ("Quota") and record it in `F`. **Quota never becomes a question to the user**; follow "Quota Exhausted" below when a pool runs dry.
4. **Initialize `F`:** write the table `| # | PRD | Branch | Status | How to verify |` with `⬜` per PRD, starting quota, and caveats. Work already started (existing `prd/<n>` branch, worktree, or ticked items in the PRD) is resumed, not redone.
5. **Reset:** before the 1st dispatch, run the Startup procedure from `board/playbook.md` on idle terminals that still hold stale context.
6. **Dispatch, one PRD at a time:** follow `board/manager.md` step 3 — branch `prd/<n>-<slug>` (recorded in `F`), dispatch `ORDER` via `python3 scripts/order.py` by Part 2 phase to Dev (or Dev Front / Dev Back), then QA; commit on the branch, no merge to `main`. Pass `F` in every `ORDER`. Confirm via `maestri check` that work has started.

## PRD Boundary (QA green or 3rd round)

1. Verify on disk: `git -C $R log --oneline -3 prd/<n>…` and the PRD status (`In Review` or parked).
2. Record in `F`: `✅` or `⏸ parked` (2-round QA ceiling reached, root cause), commit hash, and the PRD's "How to verify" steps.
3. Run `recruit --replace` on the worker terminals used and dispatch the next `⬜` PRD as in step 6.
4. If your Manager context exceeds 180k tokens: compact rather than reset — with no open `ask`, write the exact next step in `F`; schedule:
   `maestri routine create "manager-compact" --command "/compact" --once "<now + 1 min>"` and
   `maestri routine create "manager-continue" --command "/canvas-sprint --continue <area>" --once "<now + 4 min>"`.

## Quota Exhausted (at any point)

If the primary worker CLI runs out of quota, act without asking:
- Renews in ≤ 6h (5h rolling window): record `"⏸ paused on worker quota, resumes at <time>"` in `F` and create:
  `maestri routine create "sprint-resume" --command "/canvas-sprint --continue <area>" --once "<renewal + 5 min>"`.
- Renews in > 6h (weekly window): switch Dev to its configured fallback in `board.config.json` (`board/playbook.md`) and continue; record `"Dev on fallback CLI since <time>"` in `F` so QA runs a cross-family review before merge. If the fallback pool is also exhausted: `⏸` + `sprint-resume` at the earliest renewal time.

## Resume (`--continue <area>`)

Read `F` and run `maestri check` on Dev(s) and QA. Next `⬜` → dispatch. No `⬜` remaining → proceed to End.

## End

1. Write Maestri note `Sprint <area> — test` (`maestri note write`): one short block per PRD — what it delivers, branch/commit hash, how the user can test it (browser steps or CLI command), and what remains for post-merge verification. Save a copy at `planning/<project>/notes/<date>-sprint-<area>-test.md`.
2. Run `maestri notify "Sprint <area> ready: N committed, K parked. See note Sprint <area> — test"`.
3. Wait for the user's per-PRD verdict: **merge** (you merge into `main` per `board/manager.md` step 5; `git push` remains the user's decision), **adjust** (send back to Dev with the requested change), or **discard** (leave the branch untouched; branch deletion is the user's decision).

## Harness portability

- No user questions are asked during a sprint in any harness (all interim decisions are logged in `F`).
- `maestri` CLI commands work identically across Claude Code, Codex, and Antigravity.

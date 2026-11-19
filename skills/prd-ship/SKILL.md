---
name: prd-ship
description: Stage 3 of 3 in the PRD lifecycle (review, QA, and ship). Takes a PRD in In Review, reviews the code and spec compliance, runs QA (browser verification for UI PRDs), and issues a verdict — GREENLIGHT ticks Part 4, archives the PRD, updates the Queue, history.md, and the epic rollup; HOLD records Review feedback inside the PRD and returns it to /prd-run. Never edits application code; the only git commit is the planning/ accounting commit at the end of ship. Use when the user says "review the PRD", "run QA", "close/ship the PRD", "review PRD X", or after /prd-run finishes.
---

# /prd-ship — Stage 3: review, QA, and ship

> 3-stage lifecycle: `/prd` → `/prd-run` → **`/prd-ship`**. Contract defined in
> `templates/planning/PLANNING_GUIDE.md` (installed at `planning/CLAUDE.md`).

You did not implement this PRD. Review it from scratch; a ticked checkbox is not evidence.

## Usage

```text
/prd-ship <path/to/prd.md>
```

Without arguments: select the `In Review` PRD from the current project's Queue; if more than one is in `In Review`, ask the user.

## Invariants

1. **Never edit application code.** Every finding becomes actionable feedback for Stage 2 (`/prd-run`).
2. **Never commit application code or run `git push`.** Code commits belong to `/commit`. The only permitted git write is the `planning/` accounting commit at the end of Phase D (`references/close-out.md#D8`).
3. **Never issue GREENLIGHT** with a failing test, a missing file from the spec, a violated security constraint, an unexecuted test suite, or a UI change that was not inspected at every required breakpoint.
4. **The verdict lives inside the PRD**, not only in chat.

---

## Phase 0 — Entry gate

| `**Status:**` | Action |
|---|---|
| `In Review` | Proceed |
| `Ready for Implementation` · `In Progress` · `Changes Requested` | Stop → Stage 2 has not handed off yet: `/prd-run <prd>` |
| `Draft` | Stop → `/prd` |
| File in `archive/` | Stop → already delivered |

Confirm that `- [x] All Quality Checks passed` is ticked in Part 3. If not, stop → `/prd-run`.

## Phase A — Review

Read and follow `references/review.md` (A1 diff · A2 spec · A3 files · A4 constraints ·
A5 "Must Not Happen" · A6 user stories · A7 test suite · A8 grep regressions · A9 evidence vs. conclusion).

Any CRITICAL or MEDIUM finding → **skip Phase B** (do not waste time running QA on code that must be rewritten) and proceed directly to Phase C with **HOLD**.

## Phase B — QA

Read and follow `references/qa.md` (environment, QA user, test plan, Playwright and/or
browser inspection, exploratory checklist, breakpoints, recording evidence in the PRD).

## Phase C — Verdict

Print the review report:

```markdown
## Review — <PRD title>
### Confirmed
### Test Plan / Exploratory Checklist / Breakpoints   ← only if Phase B ran
### Findings
Verdict: GREENLIGHT | HOLD — N finding(s)
```

**GREENLIGHT** — zero CRITICAL/MEDIUM findings, test suite green, QA complete. LOW findings are listed but do not block. → Proceed to Phase D.

**HOLD** — append to the bottom of the PRD (incrementing the round number from the latest existing round):

```markdown
## Review feedback — round N

**Date:** YYYY-MM-DD · **Reviewer:** <harness/model>

- [ ] [BUG-1] MEDIUM — title · `file → symbol` · problem · concrete fix
- [ ] …

**Run after fixing:** <test suite command>
```

LOW findings enter the same list, tagged `LOW`. Then set `**Status:**` → `Changes Requested`,
and return the Queue row in `progress.md` to `🟢 Ready` (the PRD is ready for Stage 2 to pick back up). Print:

> HOLD — N finding(s) recorded in `<path>` (Review feedback, round N).
> Status: **Changes Requested**. Next stage: `/prd-run <path>`.

And stop.

## Phase D — Ship (GREENLIGHT only)

Read and follow `references/close-out.md` (checkbox gate, move to `archive/`, `Completed` status,
Queue update, `history.md`, epic rollup, knowledge vault, planning commit).

Print in at most five lines:

> Shipped: `<feature>` — `<path in archive/>`.
> Unblocked: `<PRDs that turned 🟢 Ready, by number and title — or "none">`.
> Ship issues: `<or "none">`.
> Planning committed: `<hash> <subject>`. Application code not committed: if still pending, run `/commit --prd <path in archive/>`.
> `<if the epic rollup reached 100%: "Epic ready for /epic-ship.">`

## Final checklist

- [ ] No application code file was edited; the only git write is the D8 commit containing strictly `planning/` paths
- [ ] The test suite ran in this session
- [ ] Phase B only ran after Phase A passed clean
- [ ] HOLD: feedback recorded inside the PRD + Status set to `Changes Requested`
- [ ] GREENLIGHT: Part 4 ticked with evidence, PRD moved to `archive/` with `Completed`, Queue and `history.md` updated
- [ ] The next stage command was printed

## Harness portability

- Outside Claude Code, `AskUserQuestion` maps to a numbered question in chat, and tool equivalents for code review and browser inspection are detailed inside `references/review.md` and `references/qa.md`.

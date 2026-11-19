---
name: prd-run
description: Stage 2 of 3 in the PRD lifecycle (execute + check). Implements Part 2 of a PRD with TDD and runs Part 3 (Quality Checks) — resolves the target (PRD path or next 🟢 Ready item in the queue), loads codebase patterns, runs a plan delta-check, implements in order, and leaves the PRD in In Review. Also fixes a PRD in Changes Requested using the Review feedback recorded in it. NEVER commits, never ticks Part 4, never runs review or ship. Use when the user says "run this PRD", "implement PRD X", "pick the next from [project]'s queue", or "fix the review feedback". Do NOT use to write a PRD (/prd) or to review/close (/prd-ship).
---

# /prd-run — Stage 2: execute + check

> 3-stage lifecycle: `/prd` → **`/prd-run`** → `/prd-ship`. Contract defined in
> `templates/planning/PLANNING_GUIDE.md` (installed at `planning/CLAUDE.md`).

State machine: **no stage starts before the previous one closes with real output.**
This stage ends when Part 2 and Part 3 are green. Code review and QA belong to Stage 3 — the
implementer never approves their own work.

## Usage

```text
/prd-run [path/to/prd.md | project-name]
```

Without arguments: ask which project.

---

## Invariants

1. **Never run `git commit`, `git add`, `git push`, or `/commit`.** This stage ends with a dirty working tree.
2. **No checkbox becomes `[x]` without pasting the real command output into the PRD**, immediately below the item.
3. **Never touch Part 4**, never run `/prd-ship`, never move the PRD to `archive/`.
4. **No code edits before Stage 2 closes.**
5. **Part 2's order is the execution order.** Deviating requires stating why beforehand.

---

## Stage 0 — Resolve target and mode

**Argument is a path to `*_prd.md`** → that file is the target.

**Argument is a project name** → read `planning/<project>/progress.md`, table
`## Queue` (🟢 Ready · 🔵 In Progress · 🔒 Blocked · ⛔ Superseded). Priority:

1. The **🟢 Next** entry in the `## Now` block — human decision wins.
2. If `—` or absent: the first `🟢 Ready` row from top to bottom.

If the two disagree, read the `"Reordered on …"` note below the table, follow `Next`, and
state to the user which PRD was selected. Cross-check with `ls planning/<project>/ready/`;
if `ready/` and `## Queue` diverge, **stop and report**. If `progress.md` has no `## Queue` table:
state that and ask for the explicit PRD path — never guess the order.

### `**Status:**` determines the mode

| Status | Mode |
|---|---|
| `Ready for Implementation` | **Execution** — Stages 1 → 6 |
| `Changes Requested` | **Correction** — see below |
| `In Progress` | Another session may be working on it. Ask before resuming; resumption starts at the first unticked item in Part 2 |
| `In Review` | Stop: awaiting Stage 3 → `/prd-ship <prd>` |
| `Draft` | Stop: return to Stage 1 → `/prd` |
| File in `archive/` · row `⛔` | Stop: already delivered or superseded |
| Row `🔒` with dependency still in `ready/` | Stop and name the missing dependency |

**Collision:** if the header has `**Collides with:**` and the cited PRD is still in `ready/`,
stop and ask the user — running two PRDs on the same file in parallel is not a decision for this
stage. If the cited PRD is already in `archive/`, proceed.

### Correction mode (`Changes Requested`)

1. Read the latest `## Review feedback — round N` at the bottom of the PRD. That is the work list.
2. Run Stage 1 (Contract) normally. **Skip Stage 2.**
3. Run Stage 3 (Status → `In Progress`, queue row → `🔵`).
4. For each feedback item: write a reproducing test (RED) → fix (GREEN) → tick the item
   **inside the feedback section** with real output pasted below it. If the fix touches a Part 2 item, append the
   updated output under that Part 2 item as well.
5. Re-run Stage 5 in full — previous session output does not count.
6. Run Stage 6.

**Stage output:** the selected PRD, the mode, and why.

---

## Stage 1 — Load codebase patterns

Implement the way the codebase already implements, not how a model would write it from scratch.

1. `planning/CLAUDE.md` (`templates/planning/PLANNING_GUIDE.md`) — protocol and status vocabulary.
2. The project's `CLAUDE.md` **and every document it instructs you to read** (design tokens, `PATTERNS.md`, architecture guides).
3. PRD header — `**Epic:**` and `**Feature spec:**`, if present.
4. Verification commands — Part 3 links the canonical command section of the subproject's `CLAUDE.md`; that is the source of truth. Literal commands pasted in Part 3 (legacy PRDs) remain valid, but flag the drift. If neither exists, derive from `package.json` / `pyproject.toml` / `go.mod` and **confirm with the user**.
5. Stack skills — discover at runtime (Claude Code: `SearchSkills`/`ListSkills`; Codex/Antigravity: `ls ~/.agents/skills .agents/skills`). Do not assume skill names.
6. Base engineering rules: `rules/coding-style.md` (immutability, files <800 lines, functions <50 lines, no hardcoded env values, explicit error handling, boundary validation) and `rules/testing.md` (TDD, ≥70% coverage).

Do not advance without printing this block:

```markdown
## Contract — <PRD name>

**Mode:** execution | correction (round N)
**Complexity:** simple | complex
**Checks to run:** <verbatim commands>
**Docs loaded:** <files read>
**Stack skills:** <matched skills, or "none — patterns come from project CLAUDE.md">
**Applicable patterns:** <3-5 concrete rules this PRD will touch>
```

---

## Stage 2 — Plan delta-check

The full plan critique happened in Stage 1 (`/prd`) and left the line
`**Plan verified:** <date> — …` in the header. Here you only verify whether the repository drifted since then.

- **Line present:** re-run the searches in `### Non-Duplication Evidence` once and
  confirm that the files/symbols listed in `### Components / Files` still exist (or still
  do not exist, where the PRD instructs creating them). Match → `PLAN OK`.
- **Line absent** (PRD written before the 3-stage lifecycle): run the full gate from
  `/prd` Step 3.5 (`skills/prd/SKILL.md`) before proceeding.

**`PLAN DIVERGES`** → call `AskUserQuestion` with the `file:line` evidence and the options:
follow the PRD as-is · follow the finding (record the divergence in Part 1) · return
to Stage 1 (`/prd`). **No application code is written before the user answers.**

---

## Stage 3 — Open execution

1. PRD: set `**Status:**` → `In Progress`.
2. `progress.md`: set the PRD row → `🔵 In Progress`; in the **Now** (`## Now`) block, `🔵` points to this PRD and
   `🟢 Next` advances to the following ready item.

---

## Stage 4 — Part 2, item by item, TDD

In file order. For each item:

1. **RED** — write the test first, run it, watch it fail. Paste the failure output.
2. **GREEN** — minimal implementation adhering to the Contract.
3. **Refactor** while keeping the test green.
4. **Tick that checkbox** — and only that checkbox — with the real command output pasted below it.

One item = one cycle. A phase ending with `**Checkpoint:**` only closes when its exact checkpoint command runs green.

**Escalate to the user** (never decide unilaterally): security trade-offs, ambiguous requirements, destructive operations, or any need to step outside scope.

---

## Stage 5 — Part 3, Quality Checks

Run the **exact** commands from the Contract — lint, type-check, tests, coverage, build.

- Paste the real output into the PRD. Without output, the checkbox does not close.
- **Never pipe through `| tail -N`** on commands whose summary appears at the top. Use `| tee check.log` if needed.
- Output from a previous session does not count.

Failed → fix → re-run. All green → tick `- [x] All Quality Checks passed`.

Code review does **not** happen in this stage — it belongs to Stage 3 (`/prd-ship`).

---

## Stage 6 — Hand off to Stage 3

1. PRD: set `**Status:**` → `In Review`.
2. Stop and print:

> Stage 2 complete — `<PRD path>` is **In Review**.
> Part 2 and Part 3 are green; Part 4 is untouched. Nothing was committed.
> Next stage: `/prd-ship <PRD path>` — preferably in a separate session or model family.

---

## Final checklist — re-read before finishing

- [ ] No `git commit`, `git add`, or `git push` command was executed
- [ ] Every ticked checkbox has real command output pasted below it
- [ ] Part 4 is untouched; no `/prd-ship` was run, no file was moved to `archive/`
- [ ] Stage 2 closed with an explicit verdict before the first code edit (or was skipped in correction mode)
- [ ] Execution followed the file's exact order (or any deviation was announced beforehand)
- [ ] Final status is `In Review` and the next stage command was printed

## Harness portability

- `AskUserQuestion` → outside Claude Code, ask a numbered question in plain text and wait for the user's reply.

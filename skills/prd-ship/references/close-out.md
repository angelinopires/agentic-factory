# Close-out — Archive and Update Project State

Loaded by Phase D of `/prd-ship`, strictly when the verdict is **GREENLIGHT**.

## D1 — Checkbox gate

Every checkbox across Parts 2, 3, and 4 must be `[x]`, and `- [x] QA passed` must be the final checkbox in Part 4.
If any checkbox is still `[ ]` → **stop**, list the unticked items, and move nothing.

## D2 — Move to `archive/`

Move `planning/<project>/ready/<file>` → `planning/<project>/archive/<file>`, without renaming the file.

## D3 — Set Status to `Completed`

Edit `**Status:**` to `Completed` **after** moving the file to `archive/`, never before.

## D4 — Remove the row from the Queue (`progress.md`)

The Queue (`## Queue`) holds only undelivered PRDs. The shipped row is **deleted** — never struck through, never left in the Queue as `✅ Verified`.

- Renumber the rows below it and update every `🔒` dependency pointer that referenced a renumbered row.
- **Recompute dependency states:** any queued PRD whose `**Depends on:**` targets are now all in `archive/` transitions from `🔒` → `🟢 Ready`. This is the highest-value output of Phase D.
- Update the **Now** (`## Now`) block: counts, `🔵 In Progress` → `—`, `🟢 Next` → best ready PRD.
- Remove any Track from the legend that has zero remaining rows in the Queue.
- If `progress.md` does not exist → create it from `templates/planning/progress.md` following `templates/planning/PLANNING_GUIDE.md` and notify the user.

## D5 — `history.md`

Under the Track's section in `planning/<project>/history.md` (create the section if this is the first PRD delivered in that track), add:

```markdown
| [Title](archive/file.md) | Simple/Complex | ✅ Verified YYYY-MM-DD |
```

Include key measurements worth preserving (test count, latency, before/after metrics).

## D6 — Epic rollup

If the PRD header has `**Epic:**` → tick the corresponding item in the epic file, update the `**Rollup**` counter (e.g., `3 of 10`), and update wave markers. If the rollup reaches 100% (every item ticked, zero PRDs for that epic left in `ready/`) → suggest `/epic-ship` to the user. Never invoke `/epic-ship` automatically.

## D7 — Knowledge vault / notes

If the workspace maintains a knowledge vault or backlog notes directory (`brain/` or `planning/<project>/notes/`), grep for the PRD's topic and mark linked backlog items as archived.

## D8 — Commit `planning/` accounting

Once GREENLIGHT closes and the PRD is archived: commit **in the `planning/` repository (or workspace planning directory)** strictly the files touched by this ship operation. Pass explicit file paths — never `git add -A`:

- The PRD (removal from `ready/` + addition in `archive/`), `progress.md`, `history.md`
- The epic file updated in D6 and the origin note, if modified or untracked

```bash
git -C planning add <explicit-paths>
git -C planning commit -m "docs(<project>): ship PRD #<N> <short English title>"
```

After committing, run `git -C planning status --short -- <explicit-paths>`. The output must be **empty** before reporting `"Planning committed"`. Note that a PRD that was never tracked in `ready/` has no deletion to stage, so its new path in `archive/` must be passed explicitly to `git add`.

Any modified file in `planning/` that does not derive from this PRD is left unstaged and noted in the report. Never run `git push`. If a git hook fails, stop and report — never pass `--no-verify`.

## Rules

- Never skip D1.
- Never leave a `🔒` pointer referencing a deleted or renumbered Queue row.
- Never commit application code, never push, and never run `/epic-ship` automatically. The only git commit allowed in `/prd-ship` is D8.

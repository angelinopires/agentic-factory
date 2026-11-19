---
name: epic-ship
description: Close a finished epic — verify the rollup and quality gates, archive the epic file, record the closure in history.md, and clean the track out of progress.md. Does NOT commit (the user does that via /commit).
---

# /epic-ship

Run this when an epic's rollup is complete. It is the counterpart of `/prd-ship`: that
one closes a PRD, this one closes the initiative the PRDs belonged to.

Without it, epics accumulate at `Ready for Implementation` forever and the project looks
like it has three open initiatives when it has one.

## Steps

1. **Identify the epic**
   - Infer from context, or read the `**Active epic:**` line at the top of
     `planning/<project>/progress.md`. Ask only if genuinely ambiguous.

2. **Verify the gate — all three must hold**

   This is the gate. If any fails: **stop**, report exactly what is missing, change nothing.

   - **Rollup 100%** — every item in the epic's `## Rollup` is `[x]`, including the
     quality-gate lines, not just the PRD lines.
   - **Quality gates passed** — each checkbox under `## Quality gates` is ticked. These
     are the conditions the epic itself declared; a gate with a command in it should have
     been run, not assumed. If a gate was never verified, say so and stop.
   - **Nothing left in `ready/`** — no PRD whose header names this epic still sits in
     `planning/<project>/ready/`. Verify against the filesystem, not against the rollup:
     ```bash
     grep -l "<epic-filename>" planning/<project>/ready/*.md
     ```
     Zero results is the pass condition. A PRD found here means the rollup is lying.

   ### Legacy epics without a Rollup or Quality gates section

   An epic written before the current template (`templates/planning/_template_epic.md`) may have neither section. Do **not** treat
   the missing section as a failed gate, and do **not** invent gates retroactively.
   Fall back to the filesystem, which cannot lie:

   - Every PRD naming this epic sits in `archive/` and none in `ready/`.
   - Every one of those archived PRDs has `**Status:** Completed`.

   If both hold, close it — and state in the report that it was closed on filesystem
   evidence because the epic declared no gates, so **nothing was verified about the
   quality of the work**, only about its completeness. That distinction belongs in the
   report and in the `**Closed**` row, not buried.

   If a PRD of that epic was abandoned rather than delivered, the epic closes as
   `Superseded`, not `Shipped`.

3. **Set the epic status**
   - `**Status**` → `Shipped` in the epic's header table.
   - Add a `**Closed**` row with today's date (`YYYY-MM-DD`).
   - Add a `**Successor**` row if another epic takes over; otherwise omit it.

4. **Move the epic to archive**
   - Move `planning/<project>/epics/<file>.md` → `planning/<project>/archive/epics/`.
   - Do not rename it.
   - **Rewrite its relative links** — the file gained one directory level. Links to
     `../ready/`, `../progress.md`, `../notes/` become `../../…`, and links reaching
     outside `planning/` gain one `../`. Verify each one resolves before moving on.

5. **Record the closure in `history.md`**

   Add a row to the `## Closed Epics` table (create the section if it is the first
   epic to close):

   ```markdown
   | [Epic name](archive/epics/file.md) | YYYY-MM-DD → YYYY-MM-DD | Shipped YYYY-MM-DD | Successor |
   ```

   If the epic carried a **Baseline** or measured results, move them into
   `history.md` as a dated block. They are history the moment the epic closes.

6. **Clean `progress.md`**
   - Remove the epic's track from the origin legend under the Queue (`## Queue`).
   - Update `**Active epic:**` in the header — to the successor if there is one, or `—`.
   - Recompute the **Now** (`## Now`) block.
   - The Queue itself should already be free of this epic's PRDs; if a row remains, the
     gate in step 2 was wrong — stop and report.

7. **Report to the user**
   - Which epic closed, and what it delivered in one line.
   - Which gates were verified, and how.
   - What the active epic is now.
   - Reminder: review and invoke `/commit`.

## Rules

- **The gate is the whole point.** An epic closed without its quality gates verified is
  worse than an epic left open — it records a success that was never checked.
- Never tick a rollup item or a gate checkbox to make the gate pass. If it is unticked,
  it is not done.
- Never delete the epic file. `archive/epics/` is where it lives.
- Never commit — that is the user's responsibility.
- `Superseded` instead of `Shipped` when the epic was replaced rather than finished. Add
  `**Superseded by:**` pointing at the replacement, and state plainly in the report that
  the work was dropped, not delivered.

## Harness portability

- Works identically across Claude Code, Codex, and Antigravity using standard file and shell tools.

---
name: prd
description: Stage 1 of 3 in the PRD lifecycle (research, define, and plan). Creates a PRD in planning/<project>/ready/ and critiques the plan against the real repository before marking it ready. Use whenever the user asks to "create a PRD", "write a PRD", "plan this feature", or "document this task" — even if they do not use the word PRD. Also use proactively when a task is non-trivial and has no existing PRD. Reads the template and project context silently, asks clarifying questions before writing anything, then produces a ready-to-execute PRD file, registers it in progress.md, and tells the user to run /prd-run next.
---

# /prd — Stage 1: research, define, and plan

> 3-stage lifecycle: **`/prd`** → `/prd-run` → `/prd-ship`. Contract defined in
> `templates/planning/PLANNING_GUIDE.md` (installed at `planning/CLAUDE.md`).

Creates a PRD in `planning/<project>/ready/` following the workspace planning conventions. The goal is to produce a clear, actionable plan the user or an agent can execute — not to write application code.

## Step 1: Read context silently

Before asking the user anything, read:

1. `planning/_template_prd.md` (seeded from `templates/planning/_template_prd.md`) — the exact format to follow
2. `planning/<project>/progress.md` — what already exists, what is in flight
3. The project's `CLAUDE.md` — stack, constraints, design rules, verification commands

Infer `<project>` from `board.config.json`, the current working directory, or recent conversation. If still ambiguous, include it as a question in Step 2.

## Step 1.5a: Decompose — map deliverables and dependencies first

Before writing any PRD or asking any question, analyze the user's idea(s):

1. **How many PRDs are needed?** One idea can hide multiple deliverables. A new feature with a database schema change + a UI + a background job is likely three independent PRDs, not one.
2. **Does each PRD have one verifiable deliverable?** If you cannot describe a single passing command (tests green, query returning expected shape, page loading) that proves it closed — it is not a deliverable, it is a milestone. Split it.
3. **Map dependencies.** Does PRD B require PRD A to be in production before it can start? Mark that explicitly. Independent PRDs can be executed in any order — or in parallel.

Present a decomposition table to the user before writing anything:

```markdown
| # | PRD | Deliverable | Depends on |
|---|-----|-------------|------------|
| 1 | … | … | — |
| 2 | … | … | PRD 1 |
```

Wait for approval or correction before proceeding to Step 1.5b.

### Queue collision

While mapping files each PRD will touch, grep the same files against every other 🟢/🔵
PRD already in `progress.md`'s Queue (`## Queue`). If another queued PRD (not yet in `archive/`) touches
the same file(s), fill `**Collides with:**` in the header with that PRD and the shared files.
This is not a blocker — it is a flag so whoever executes either PRD knows to re-check the
other's line/symbol references before assuming they are still valid. A queued PRD that
already shipped (in `archive/`) is not a collision, just a predecessor — that is what
`**Depends on:**` is for.

**Writing strategy by dependency type:**

| Type | Strategy |
|------|----------|
| Independent PRDs | Write all in the same session, one after another |
| PRD B depends on PRD A | Write both, but flag assumptions in PRD B with: `> ⚠️ Review these technical premises after PRD A is implemented` |

The rationale for the flag: PRD B's technical premises are valid at time of writing, but A's implementation may invalidate them. The flag forces a review at the right moment without blocking the planning work now.

## Step 1.5b: Size each PRD before writing it

**One PRD = one verifiable deliverable.**

Check each PRD before writing a single line. If any of these is true, split further:

- Part 2 would have more than ~3 phases
- The whole file would exceed ~200 lines
- A phase does not end with a command that proves it closed (tests green, migration applied, query returning the expected shape)
- A phase waits on days of observation (N production runs) or starts with a manual step by the user (edit prod `.env`, rotate a secret). That phase is its own PRD, created now, with `**Depends on:**` naming the manual action. Otherwise the code PRD cannot close.

A phase that does not end green is not a phase — it is half a phase, and it is what forces a mid-execution hand-over.

Rationale: a 400-line PRD covering 8 phases costs multiple sessions to write and blows the context window on execution. The file size is never the root problem — the phase count and re-derived research are.

## Step 2: Ask clarifying questions

**Deep mode.** If the context already shows the PRD is complex (definition below), or the user
asked for it ("grill", "deep mode", "stress-test this"), invoke the `grill-me` skill scoped to this
PRD instead of the 2–4 questions. Its settled decisions feed Step 3 (Overview, Must Not Happen,
Out of Scope). Outside Claude Code, read `skills/grill-me/SKILL.md` (or `~/.agents/skills/grill-me/SKILL.md`) and follow it.

**Normal mode:** use `AskUserQuestion` to collect what you need before writing. Keep it to 2–4 questions — enough to avoid wrong assumptions, not so many it feels like a form.

Good things to ask if not already clear from context:

- What is the feature or change? (if the user was vague)
- Simple or complex? Simple = single component/file set, no architecture decisions, no new routes or schema. Complex = multiple systems, new routes, schema changes, or significant unknowns.
- What is explicitly out of scope? (prevents scope creep later)

**Demo (both modes, never inferred):** a PRD with a visible UI change always gets the question "Record demo
(screenshots + video) at the end of QA?" (`yes`/`no`) — the user decides per PRD, as some changes are too small to warrant it. The answer
goes to `**Demo:**` in the header; `yes` instructs QA to run `/prd-demo` after QA passes. A PRD without UI →
`**Demo:** no`, without asking.

The reason to ask first is that a PRD written on wrong assumptions wastes more time than the questions take. Once the user answers, proceed directly — do not ask again.

## Step 3: Write the PRD

Follow `templates/planning/_template_prd.md` (`planning/_template_prd.md`) exactly — same sections, same order. The template exists so every PRD is predictable and executable without needing to re-read the spec.

File path: `planning/<project>/ready/YYYY-MM-DD-<kebab-slug>_prd.md`

### The PRD links research, it never restates it

If a fact already lives in `docs/`, an ADR, a spec, or a source doc, the PRD **links to it with a `file:line` reference** and moves on. Do not summarize, paraphrase, or copy it in.

If the fact is not documented anywhere, the next step is to document it in the right place — not to paraphrase it inside the PRD. Research duplicated into a PRD is the single largest cost in writing one, and it goes stale the moment the source doc changes.

Fill in each part:

- **Status:** `Ready for Implementation` — always, because a Draft PRD cannot be executed
- **Complexity:** `simple` or `complex`, from the user's answer
- **Created:** today's date (`YYYY-MM-DD`)
- **Part 1 — Plan:** Overview (1–3 sentences), Scope + Out of Scope, **Must Not Happen**
  (below), Technical Detail (Components / Files with symbol anchor, Schema / Types,
  Constraints, Why-not-X if a non-obvious choice was made), **Non-Duplication Evidence** (below)
- **Part 2 — Act:** implementation checklist grouped by phase, written so a developer can tick items without re-reading the plan
- **Part 3 — Quality Checks:** link the subproject's `CLAUDE.md` command section (below) — never paste the literal commands
- **Part 4 — QA:** user stories covering happy path, edge cases, and all 3 breakpoints (375px / 768px / 1280px)

### PRD implementing an existing design (canvas, Artifact, Figma, HTML export)

Run **Phase 0** of the `design-port` skill before writing Part 2: export saved, section-by-section reference mapped,
canvas × decisions resolved with the user, claims × evidence verified, mobile layout decided, and intentional divergences
listed. Part 4 points to Phase 2 of `design-port`.

### Overview: state the delta, not the story

The executor has not read this conversation — but they read fast and know the codebase.
Give them what changed and the bar for done, not the narrative of how you got there.

```text
Bad  (narrative, costs the reviewer a re-read):
"The user reported that when filling out the onboarding form and navigating between steps,
typed data was lost because the component remounts on every step change, causing
frustration and drop-off — this PRD fixes that by persisting state."

Good (delta + bar, 2 lines):
Onboarding loses typed input on step change because the form remounts.
Persist form state across steps; no typed value is lost when navigating back/forward.
```

### Must Not Happen

At least one bullet, always — the failure or edge case the feature must not regress into
(invalid input, empty state, race condition). This is the gap code review keeps finding:
PRDs describe the happy path well and leave "what must not happen" implicit.

For a PRD that tunes a pattern (regex, classification rule, keyword list): every bullet here becomes a literal
test case, and Part 2 orders it as the **first** step — RED before the pattern is adjusted, not after.

### Non-Duplication Evidence

For every new component, helper, or dependency that Part 2 proposes to create, paste the actual
search output here — not just the conclusion "does not exist yet":

```text
$ grep -rn "toast" src --include='*.tsx' -l
(no matches)
```

This is the same search you would run anyway before proposing something new — the only change
is writing the output into the PRD instead of discarding it. It turns the executor's
Stage 2 delta-check from a full re-search into a one-line confirmation.

### Quality Checks: link, don't paste

Find the subproject's canonical command section (e.g. `server/CLAUDE.md#Verification Commands`,
`web/CLAUDE.md#Verification Commands`) and reference it by heading. Commands drift; a
pasted command in a `ready/` PRD does not get updated when the real one changes. If the
project has no such canonical section yet, fix that first — do not paste around it.

### Checkpoints inside Part 2

Every phase in Part 2 ends with an explicit **Checkpoint** line naming the exact command that proves the phase closed:

```markdown
### Phase A — <name>
- [ ] ...
- [ ] ...
**Checkpoint:** `uv run pytest tests/test_regions.py -q` green
```

The resume point for a new session is always the last green checkpoint — nothing before it gets re-read, nothing after it gets assumed. When `/handover` runs mid-PRD, it cites that command.

## Step 3.5: Plan critique gate

**No PRD leaves this stage as `Ready for Implementation` without passing this gate.** The PRD is the
spec, not the evidence — the repository is the evidence. Run against the newly written file (or against
an existing PRD when asked to update one):

1. **Truth of assertions** — run `/verify-claims <prd>`. Any cited path, command, symbol, or number
   that does not exist is a finding. A path the PRD **cites as existing** must exist;
   a path the PRD **instructs to create** must *not* exist yet.
2. **Does it already exist?** — `### Non-Duplication Evidence` has real search output pasted for every
   new component, helper, and dependency in Part 2. A conclusion without output does not count.
   Quote globs (required in zsh): `grep -rn "<concept>" src --include='*.ts' -l`.
3. **Completeness** — every requirement in Part 1 (including every bullet under `Must Not Happen`)
   has a matching checkbox in Part 2 or Part 4. A requirement outside a checkbox does not exist for the executor.
4. **Ordering** — no item in Part 2 depends on an artifact created by a later item.
5. **Ready design** — if the PRD implements a design, Phase 0 of `design-port` is satisfied in the file.

Finding → fix the PRD now, in this stage. If the fix changes scope or a product decision, ask
the user (`AskUserQuestion`; outside Claude Code, numbered question in chat) before rewriting.

Close by pasting this line right below the PRD header:

```markdown
**Plan verified:** YYYY-MM-DD — verify-claims ok · non-duplication ok · completeness ok · order ok · design ok|n/a
```

Stage 2 (`/prd-run`) trusts this line and only runs a fast delta-check.

## Step 4: Register in the Queue

`progress.md` holds **one queue for the whole project**. Add the PRD as a row in the
**Queue** (`## Queue`) table of `planning/<project>/progress.md`:

```markdown
| N | [Feature Name](ready/YYYY-MM-DD-slug_prd.md) | Track | S/C | 🟢 Ready |
```

- **N** — next free number, placed at the position dependencies dictate. Renumber the
  rows below it if you insert in the middle.
- **Track** — the short name of the epic (with wave, e.g. `Beta W0`), the origin note
  (`Health`), or `Solo`. If it is a new track, add it to the origin legend under the table.
- **Cplx** — `S` or `C`.
- **Status** — **derived, never invented**: `🟢 Ready` when every PRD named in
  `**Depends on:**` is already in `archive/`; otherwise `🔒` followed by the queue numbers
  of the open dependencies.

Then update the **Now** (`## Now`) block: the counts, and 🟢 **Next** if this PRD is now the
best next move.

### The dependency lives in the PRD, not in the queue

Write `**Depends on:** [PRD](ready/...) — what it leaves ready` in the PRD header. It is a
**permanent fact** and is never edited when the dependency ships — the queue's 🟢/🔒 is
recomputed from it instead. Never write a state word (`Blocked`) into `**Status:**`;
`Status` tracks this PRD's own progress, not another PRD's.

### What NOT to do

- Do not add a second table, a "Standalone PRDs" section, or a per-epic queue. One queue.
- Do not put justification prose in `progress.md` — it belongs in the epic or origin note.
- Do not write a row for a PRD that is already delivered. Delivered work lives in `history.md`.

The full contract is in `templates/planning/PLANNING_GUIDE.md` (`planning/CLAUDE.md`). Read it if the shape of
`progress.md` is unclear.

## Step 5: Announce the next stage

Always finish with:

> PRD ready: `<path>` — **Status:** Ready for Implementation.
> Next stage: `/prd-run <path>`.

With multiple PRDs, list one command per PRD in Queue order. Never start Stage 2 (`/prd-run`)
in the same response.

## Harness portability

- `AskUserQuestion` → in Codex or Antigravity, ask in plain text with numbered options and one open option.
- Sub-agents / skill delegation (`grill-me`, `verify-claims`, `design-port`) → read the corresponding `SKILL.md` file directly and execute its steps sequentially.

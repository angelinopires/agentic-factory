# Planning Context

`planning/` is the central specifications hub. Every feature implemented in `projects/` originates here. Read the target project's `CLAUDE.md` before writing a specification — this guide is stack-agnostic.

## Core Principle

**One fact lives in exactly one file.** Whenever two files state the same fact, they eventually diverge. Each file below has a single responsibility:

| File | Responsibility | Reader |
|---|---|---|
| `progress.md` | **Dashboard** — what is active right now | Human, in 10 seconds, on mobile |
| `history.md` | **Ledger** — everything shipped, dated | Anyone auditing past deliveries |
| `epics/*.md` | **Contract** — goal, gates, risks, rollup | Anyone deciding if an initiative is done |
| `ready/*_prd.md` | **Execution** — step-by-step plan and gates | The agent implementing or verifying |
| `notes/*.md` | **Evidence** — audits, measurements, research | Anyone checking why a queue exists |

## Directory Structure

```text
planning/[project]/
├── progress.md         # THE DASHBOARD. Single queue. Zero shipped items. Zero prose.
├── history.md          # THE LEDGER. Everything shipped, dated.
├── epics/              # Active Epics
├── project-sheet.md    # Product identity sheet (audience, goal, voice, channels)
├── drafts/             # PRDs with product spec ready, waiting for engineering or parked
├── design/             # Static HTML design options, one subfolder per PRD slug
├── ready/              # Unshipped PRDs (Draft -> Ready for Implementation -> In Review)
├── archive/            # Completed / Superseded PRDs
│   └── epics/          # Shipped | Superseded Epics
├── notes/              # Audits, 1-page plans, and research evidence — never a queue
└── runs/               # Execution state: ORDER/REPORT files, authorization quotes, qa-proofs
```

## Document Types

| Type | Path | When to Use |
|---|---|---|
| PRD | `ready/YYYY-MM-DD-[name]_prd.md` | Feature with decisions, cross-file impact, or QA |
| Epic | `epics/YYYY-MM-DD-[name]-epic.md` | Initiative spanning 3+ PRDs with quality gates |
| Note | `notes/YYYY-MM-DD-[name].md` | Audit, 1-page plan, measurement, or research |
| Execution Run | `runs/<prd>/*` | Deterministic `order.py` state, `authorization.md`, and `qa-proof.py` JSON |
| Inline Task | *(no file)* | <10 items, zero architectural decisions, obvious fix |

**Inline task when ALL hold:** <10 items, no architectural trade-offs, no dedicated QA stage, no cross-team alignment.

**PRD when ANY holds:** non-obvious decisions, visual QA, touches 3+ files, specification must survive across sessions.

---

## `progress.md` — The Dashboard

Four blocks, **in this exact order**, using tables and lists only. **Never paragraphs.**

```markdown
# <project> — Progress

**Updated:** YYYY-MM-DD · **Active Epic:** [name](epics/…)

## Now

| | |
|---|---|
| 🔵 **In Progress** | — |
| 🟢 **Next** | [PRD](ready/…) · Simple |
| 📊 **Queue** | 3 ready · 2 blocked |

## Queue

> One row per unshipped PRD. Shipped PRDs leave this table and become a row in `history.md`.

| # | PRD | Track | Cplx | State |
|---|---|---|---|---|
| 1 | [PRD](ready/…) | Health | S | 🟢 Ready |
| 2 | [PRD](ready/…) | Beta W0 | C | 🔒 1 |

| Track | Origin |
|---|---|
| Health | [Audit YYYY-MM-DD](notes/…) |
| Beta W0 · W1 | [Beta Epic](epics/…) |
| Solo | Standalone PRD without an epic |

## Backlog — Not Yet a PRD

| Item | Becomes a PRD When |
|---|---|
| … | numeric trigger or named event |

## Rules

- Single queue only. Shipped → `history.md` in the same commit.
- Justification prose lives in the epic or origin note, never here.
```

### Optional Block: Parked (`## Parked`)

Projects with a long horizon may insert `## Parked` **between `Queue` and `Backlog`**:
- A parked item is an existing PRD **outside the active queue**, held until a concrete trigger fires. The file remains in `ready/`.
- Sub-tables (`### <Context>`) use columns `# | PRD | Resumes When`.
- A PRD appears in either `Queue` or `Parked`, never both.

### State Vocabulary

| State | Meaning |
|---|---|
| 🟢 **Ready** | All prerequisites closed. Can start today |
| 🔵 **In Progress** | Currently being executed |
| 🔒 `<#>` | Blocked by item(s) `<#>` in the active queue |
| ⛔ `<#>` | Superseded by item `<#>`. Removed on the next `/prd-ship` |
| 🔒 User | `**Depends on:**` cites a manual user action (credentials, external dashboard). Turns 🟢 once confirmed in the PRD |

### Invariants

- **Zero strikethrough rows.** Shipped items are deleted from `progress.md` and appended to `history.md`.
- **Zero prose paragraphs.** Ordering rationale belongs in the epic or origin note.
- **Max 5 columns** in the Queue table so it renders cleanly on mobile screens.
- **One PRD = one row in one file.** Epics do not duplicate the PRD queue table.
- **State is derived from disk.** Dependencies live permanently in the PRD header (`**Depends on:**`); 🟢 vs 🔒 is derived by checking whether the prerequisite is already in `archive/`.

---

## Epics

Multi-phase orchestration contract: goal, completion bar, quality gates, risks, and flat rollup checklist. **Contains no PRD link/dependency table** — `progress.md` owns the queue.

Template: [`_template_epic.md`](_template_epic.md). **At most one `Active` epic per project.**

| Status | Meaning |
|---|---|
| `Active` | Currently executing; linked in `progress.md` header |
| `Shipped` | Rollup 100% + quality gates green; archived in `archive/epics/` |
| `Superseded` | Replaced by another epic; archived in `archive/epics/` with `**Superseded by:**` |

---

## Complexity

`**Complexity:** simple | complex` — mandatory in every PRD header. Any complex marker makes the PRD `complex`.

| Criterion | Simple (`S`) | Complex (`C`) |
|---|---|---|
| File scope | ≤3 existing files | New files or 4+ touched files |
| Component scope | 1 component | Multi-component or cross-cutting |
| QA | DOM / attribute / unit check | Visual layout, multi-route, or E2E flow |
| Architecture | Obvious implementation | New decisions, schema changes, or new queries |

## PRD Status Lifecycle (3 Stages)

| # | Stage | Skill | Entry Status | Exit Status | Next Command |
|---|---|---|---|---|---|
| 1 | Research, define & plan | `/prd` | — / `Draft` | `Ready for Implementation` | `/prd-run <prd>` |
| 2 | Execute & quality check | `/prd-run` | `Ready for Implementation` · `Changes Requested` | `In Review` | `/prd-ship <prd>` |
| 3 | Review, QA & ship | `/prd-ship` | `In Review` | `Completed` · `Changes Requested` | `/commit --prd <prd>` · `/prd-run <prd>` |

**Factory Invariants:**
- Never tick `[x]` without pasting real verification output below the item.
- Part 3 must close completely before the first item of Part 4 begins.
- No PRD reaches `Ready for Implementation` without passing the codebase critique gate (Stage 1).
- Stage 2 implementers never tick Part 4 — Part 4 belongs strictly to QA (Stage 3).
- Every file in `archive/` has `Status: Completed` or `Superseded`.

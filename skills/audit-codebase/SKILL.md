---
name: audit-codebase
description: Technical audit of a codebase producing measured findings with file:line evidence, a priority queue ordered by numeric trigger, and named conflicts against PRDs already in flight. Use when the user asks to audit, review the health of, find critical points in, or look for flaws and improvement opportunities across a project — not for reviewing a single diff (that is /code-review).
---

# /audit-codebase

Full-system technical audit of a project. Produces a report of **measured** findings and an
execution queue prioritized by real pain rather than abstract severity labels.

**This is not `/code-review`.** That reviews a diff. This inspects the whole system, runs the
system, and measures.

## The contract

Every finding must carry four elements or it does not enter the report:

1. **A number** — how many lines, how many rows, how many milliseconds, what percentage.
2. **A `file:line`** — exact location in the repository.
3. **The consequence** — what breaks, for whom, and when.
4. **A trigger** — either it is already bleeding today, or it becomes a PRD when metric X crosses threshold Y.

"Looks slow", "could be cleaner", and "consider refactoring" are not findings. They are noise
that dilutes real findings and trains the user to skim past the report.

## Steps

### 1. Map before judging

Read the project context (`CLAUDE.md`, `docs/adr/`, `docs/`, `planning/*/progress.md`) **before**
opening application source code. Half of what looks like a bug at first glance is a recorded
architectural trade-off — flagging an explicit ADR decision as a mistake burns the credibility
of the entire audit.

Inventory work already in flight: PRDs in `ready/`, active epics, current branch state. This
feeds Step 5.

### 2. Run the system, don't just read it

What separates this skill from a static code reading is empirical measurement. Wherever a metric
can be measured, measure it:

- Tests and type checker: how many pass, wall-clock duration, actual line/branch coverage.
- Database: `EXPLAIN ANALYZE` on hot-path queries, exact row counts backing any percentage claim.
- API: p50/p95 latency of primary routes against realistic data volume.
- Build/bundle: output size, unexpected dependencies pulled into the client bundle.
- Cron/background jobs: what is scheduled where, and whether two schedulers trigger the same job.

> ⚠️ **`EXPLAIN ANALYZE` executes DML.** Measure `UPDATE` or `DELETE` queries exclusively inside
> a `BEGIN … ROLLBACK` transaction block. Running a bare `EXPLAIN ANALYZE` on an expiration
> query once mutated 575 live records during an audit measurement.

When something cannot be measured in the current environment, state explicitly that it was not
measured — never fill the gap with an estimate presented as fact.

### 3. Write the findings

One finding per numbered section, each satisfying the four-part contract above. Group findings by
nature (correctness, data loss, performance, architecture, hygiene), never by file path.

Explicitly highlight any **shared root cause** when two or more findings stem from the same design
flaw — this changes execution order. Real example: a duplicated classification loop across a
parallel worker and a serial fallback produced a count discrepancy; eliminating the duplication
fixed the bug by construction and prevented regression.

### 4. Prioritize by numeric trigger

Sort findings into three buckets — the second and third **do not become PRDs today**:

| Bucket | Criterion | Destination |
|---|---|---|
| **P1** | Already causing data loss, false metrics, or user-visible failure | Enters the active queue and becomes a PRD |
| **P2** | Will hurt at a predictable scale threshold | Stays in the report with an explicit trigger: "becomes a PRD when p95 exceeds 1s" |
| **P3** | Real technical debt, zero pain today | Stays in the report with the numeric threshold that will trigger it |

Order the P1 execution queue by an explicit rule, not intuition. The rule that holds up in
practice: **nothing that measures outcomes runs before the fix that repairs the measurement.**
Data correctness first, then metric trustworthiness, then features or optimizations built on top.

### 5. Cross-check against work already in flight

Mandatory section: **Conflicts and overlap**. For every PRD already sitting in `ready/`, answer:

- Does any finding invalidate one of its acceptance criteria? (e.g., a target percentage computed from a broken counter)
- Do two PRDs touch the same files? Which one must land first?
- Does any PRD assume infrastructure that this audit proved does not exist?
- Is any PRD missing a layer in its scope? (Classic trap: a PRD extracts a new field, but no persistence layer writes it — the value is computed and silently discarded.)

Label conflicts with letters (`Conflict A`, `Conflict B`, …) so they can be referenced directly
from PRDs and epics.

### 6. Close out

- **Suggested execution order** section, explaining the rationale for each position in one line.
- **Intentionally left out of the queue** section, listing all P2/P3 items with their numeric triggers. An item omitted without explanation comes back as a question next week.
- **Run `/verify-claims` on the report.** Mandatory. An audit that cites a non-existent file loses authority over everything else it claimed.
- Register approved P1 items in `planning/<project>/progress.md`.

## Rules

- **No finding without a measurement and `file:line`.**
- **Run instead of inferring.** If a metric could not be measured, say so — never estimate and present as measured.
- **Read ADRs before calling something a bug.** A documented trade-off is not a finding.
- **Severity is a numeric trigger**, not an adjective. Without a trigger number, an item does not enter the queue.
- **Do not author PRDs during the audit.** The audit report is the deliverable; authoring PRDs is the next step via `/prd`, and only for P1 items.
- **Run `/verify-claims` before delivery.** No exceptions.
- Explicitly declare what was **not** audited. Declared coverage boundaries are part of the result.

## Harness portability

- Works identically across Claude Code, Codex, and Antigravity.
- When user confirmation is required after delivering the report, use `AskUserQuestion` in Claude Code or numbered plain-text options in Codex and Antigravity.

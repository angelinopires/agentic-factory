# [Feature Name]

**Project:** [project name]
**Status:** Ready for Implementation
**Complexity:** simple | complex
**Infra:** yes | no  <!-- yes when touching Docker, compose, cron, CI, deploy, or telemetry collectors: triggers infra-preflight -->
**Demo:** yes | no  <!-- UI PRDs: user decides during /prd; yes triggers prd-demo at the end of QA -->
**A1:** yes | no  <!-- yes triggers Stage A1 machine code review & security review before Stage A2 -->
**Created:** YYYY-MM-DD
**Epic:** `epics/YYYY-MM-DD-[name]-epic.md`  <!-- optional; omit for Solo track -->
**Depends on:** [PRD](ready/...) — what it provides  <!-- optional -->
**Collides with:** [PRD #N](ready/...) — shared file(s): `a.ts`, `b.py`  <!-- optional; another Ready/In-Progress PRD touching the same files -->

---

## Part 1 — Plan

> Technical specification. Read-only during implementation. Include `### Why not X?` for non-obvious design choices.

### Overview

[1–3 sentences: what changes, why it matters, and what problem it solves.]

### Scope

[What is included in this PRD.]

**Out of Scope:** [What is explicitly excluded.]

### Must Not Happen

> Failure modes, edge cases, and regressions that this feature must prevent — not the happy path already covered in Scope. Always include at least 1 item. Every item here becomes a test before implementation code.

- [Invalid input / empty state / race condition / boundary invariant that must not break]

### Technical Detail

### Components / Files

- `src/... → SymbolOrFunctionName` — [purpose]  <!-- reference symbols rather than brittle line numbers that drift across merges -->

### Non-Duplication Evidence

> Mandatory whenever Part 2 creates a new component, helper, script, or dependency. Paste real search output — never just the conclusion "does not exist".

```text
$ grep -rn "<concept>" src --include='*.ts' --include='*.py' -l
<real output, or "no match">
```

### Schema / Data Model

[Schemas, types, fields — remove if not applicable.]

### Queries / API

[REST / GraphQL / SQL / CLI contracts — remove if not applicable.]

### Constraints

- [Technology constraint, performance budget, or architectural boundary]
- New or modified user-facing copy must match the canonical vocabulary in `CLAUDE.md`; add any new domain term in this PRD.

**Why not X?**

[Non-obvious architectural choice and why the alternative was rejected. Remove if not applicable.]

### Rollout

> Mandatory when the project has a live production environment. Completed **before** writing code to surface any manual step between merge and end users. Remove in pre-launch projects.

| Dimension | Detail |
|---|---|
| **Database migration** | no · yes — verified from the project's actual CI/CD deploy workflow, never from memory |
| **Deploy order** | backend before frontend · frontend before backend · independent |
| **Backwards compatibility** | does the new API break the old frontend? does the new frontend require the new API? |
| **New env var / feature flag** | name, default value, and where it is configured in production |
| **Config-only change** | how it reaches containers (recreate on deploy, hot reload, or manual step) · n/a |
| **Host filesystem reads/writes** | user, group, and path verified during pre-flight (`infra-preflight` §2) · n/a |
| **Rollback plan** | does `git revert` suffice, or is there irreversible state? |
| **Post-deploy verification** | exact health endpoint, CLI check, or metric to verify in production |

---

## Part 2 — Act

> Implementation checklist. Tick each item `[x]` as it completes — not in a batch at the end. Executed during Stage 2 (`/prd-run`).

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

---

## Part 3 — Quality Checks

> Run after Part 2 is complete and before QA begins. QA must not start until this section is green and recorded via `qa-proof.py`. Link the canonical verification section of the project's `CLAUDE.md` rather than duplicating commands.

**Commands:** see `[project]/CLAUDE.md#Verification-Commands`

- [ ] All Quality Checks passed

---

## Part 4 — QA

> Executed during Stage 3 (`/prd-ship`), never by the implementer. For UI changes, `/verify-ui [route]` checks 375px, 768px, and 1280px (or 390px and 1440px). Validates observable behavior, not just the diff.

### User Stories

- [ ] User can navigate to [feature entry point]
- [ ] User sees [key UI element]
- [ ] User can perform [primary action] and observe [expected result]
- [ ] Edge cases covered: empty, loading (with reserved dimensions), and error states
- [ ] Zero horizontal overflow or layout shift at mobile (390px) and desktop (1440px)

### Acceptance Criteria

- [ ] [Observable invariant that holds across all breakpoints/environments]
- [ ] [Performance or security requirement verified]

- [ ] QA passed

<!--
## Review feedback — round N

Recorded by QA (`/prd-ship`) on HOLD. The implementer (`/prd-run`) fixes every item and ticks `[x]` with verification output pasted below. Keep previous rounds as an audit trail.

- [ ] [BUG-1] MEDIUM — title · `file → symbol` · root cause · required fix
-->

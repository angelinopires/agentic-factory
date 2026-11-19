# Epic: [Name]

| Field | Value |
|---|---|
| **Project** | [project name] |
| **Status** | Active |
| **Created** | YYYY-MM-DD |
| **Goal** | [One sentence: what the user or system can do once this epic ships] |
| **Done When** | [Verifiable completion bar in one sentence] |
| **Rollup** | 0 of N · [Wave 0 ⬜ · Wave 1 ⬜] |

---

## Rollup

> Flat checklist. **No PRD file links and no dependency arrows here** — the Queue in `progress.md` is the single owner of links and dependencies. Ticked by `/prd-ship` as each PRD closes.

- [ ] P0 — [short deliverable name]
- [ ] P1 — [short deliverable name]
- [ ] P2 — [short deliverable name]

---

## Why Now

[2–4 sentences explaining what in the current system forces this initiative now, citing `file:line` or measured metrics where applicable. This holds the justification prose that `progress.md` omits.]

## Scope

[How many PRDs, grouped into waves if applicable, and what the initiative deliberately excludes.]

**Out of Scope:** [What is deferred and why]

### Locked Decisions

> Product and architectural decisions agreed with the user. Each decision states its concrete consequence so the epic is not re-litigated on every PRD.

- **[Decision]** — [Consequence: which PRD becomes unnecessary, or which constraint becomes mandatory]

## Quality Gates

> Verifiable condition between waves. No PRD in the next wave starts until the gate passes.

### Gate [Wave 0 → Wave 1]

- [ ] [Observable condition and the exact command that proves it]

## Risks

| Risk | Mitigation |
|---|---|
| [Risk, with `file:line` if rooted in code] | [Which PRD addresses it, or why it is accepted] |

## References

- [Origin Note](../notes/...) — measured evidence behind this epic

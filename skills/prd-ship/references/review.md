# Review — Spec Compliance and Code Quality

Loaded by Phase A of `/prd-ship`. You did not write this code: review it from scratch.
**Never treat a ticked checkbox as evidence.** Read the code and run the tests yourself.

## A1 — Diff review

- **Claude Code:** run `/code-review medium` over the PRD's diff and collect all findings.
- **Outside Claude Code (or cross-family blind review):** inspect `git diff` (and `git status` for untracked files) scoped to the files in `### Components / Files`. Hunt for: logic bugs, swallowed errors, in-place mutation, hardcoded environment values, functions >50 lines, files >800 lines, unvalidated boundary inputs, dead code, or duplication of utilities that already exist in the repository.

Every A1 finding enters the report using the severity scale below.

## A2 — Read the spec

From the PRD, hold in mind: Scope / Out of Scope · `### Components / Files` · `### Constraints` ·
`### Must Not Happen` · Part 4 User Stories and Acceptance Criteria · feedback from previous review rounds (if any exist, verify that every single item was genuinely fixed).

## A3 — Implementation exists

For every file listed under `### Components / Files`: read the file (or the relevant sections) and confirm it was created or modified as specified. **A file listed in the spec that is missing on disk is CRITICAL.** In Claude Code, if there are more than 4 files, you may use parallel Explore sub-agents; in other harnesses, read them sequentially.

## A4 — Constraints, line by line

Evaluate each constraint: ✅ confirmed · ❌ violated · ⚠️ verifiable only at runtime (deferred to Phase B).

For every PRD touching authentication or an API endpoint, verify:
- Zero hardcoded secrets
- Input validated at the system boundary
- Zero SQL injection surface (parameterized queries only)
- Tokens/hashes: raw values never stored at rest, constant-time comparison used

## A5 — "Must Not Happen" has real tests

For every bullet under `### Must Not Happen`, locate the test that exercises that failure mode and confirm it **asserts** the proper handling (not merely that the happy path passes). Missing test = ❌, blocks GREENLIGHT. An empty or missing `### Must Not Happen` section is a finding against the PRD.

## A6 — User Stories covered by tests

For every User Story in Part 4: locate the test, read it, and confirm it covers the entire scenario (a matching test name alone is insufficient). ✅ covered · ❌ missing test · ⚠️ partial test.

## A7 — Run the test suite

Run the command from the canonical section linked in Part 3 (or generate a cryptographic proof with `python3 scripts/qa-proof.py`). Record pass/fail counts, full tracebacks for any failure, and coverage percentage. **Run it now** — output pasted by Stage 2 does not substitute for a fresh run.
If the suite cannot run (missing database, missing environment): record the blocker; the verdict is **HOLD** (unverifiable), never GREENLIGHT.

## A8 — Grep for regressions

- Any literal string the PRD instructed to remove is still present
- `TODO`, `FIXME`, or `NotImplementedError` left in new files
- Deprecated pattern still present in a file that should have been migrated

## A9 — Evidence supports the conclusion

Read every pasted evidence block against the claim it justifies. A conclusion contradicted by its own numbers is **MEDIUM** at minimum, and blocks GREENLIGHT if it determined scope (e.g., a phase was skipped or altered because of it). Proof of a gate or hook must come from the real surface output (the block message shown by the harness), not from invoking the script directly in isolation: a direct script call tests the code, not the wiring.

## Severity Scale

- **CRITICAL** — breaks correctness or security
- **MEDIUM** — violates the spec or leaves a real UX/behavioral gap
- **LOW** — polish, minor coverage gap, or minor fidelity detail; does not block on its own

## Finding Format

```markdown
#### [BUG-N] SEVERITY — title
**File:** path → symbol
**Problem:** what is wrong
**Fix:** concrete instruction
**Requirement:** PRD line violated
```

Every finding must be self-contained: Stage 2 (`/prd-run`) executes without access to this session's conversation history.

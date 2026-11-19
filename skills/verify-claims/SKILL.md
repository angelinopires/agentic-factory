---
name: verify-claims
description: Gate that proves every path, command, symbol and number cited in a document actually exists. Run before delivering any audit, PRD, epic, plan or technical report. Use when finishing /audit-codebase, /product-eval or /prd, or when the user asks to check whether a doc still matches the code.
---

# /verify-claims

A report that cites a non-existent file costs a stalled execution session. This gate is
cheap and always runs before delivery.

**Input:** one or more markdown files (audit, PRD, epic, plan).
**Output:** list of claims that do not hold up, or "clean".

## Why it exists

In a real audit of 28 findings with measured evidence, four unverified claims slipped
into the PRDs: a CLI module that did not exist (`cli.repass`), two invented frontend
paths, and an asserted database index that no migration created. Each one would have
stalled the session executing it. None would have survived an `ls`.

## Steps

### 1. Extract verifiable claims

Scan the document and collect claims into four buckets:

| Bucket | What to extract | How to recognize |
|---|---|---|
| **Paths** | files and directories | `` `src/foo.ts` ``, `path/to/file.py:42`, relative markdown links |
| **Commands** | CLI invocations | `python -m x.y`, `npm run z`, `uv run ...`, cited flags |
| **Symbols** | functions, classes, columns, indexes, env vars | `` `ClassificationUpdate` ``, `formatSalary`, `jobs.specialty` |
| **Numbers** | percentages, counts, measurements | "52% of the corpus", "1,840 jobs", "p95 of 1s" |

### 2. Verify each bucket

**Paths** — existence on disk. Distinguish two cases and never confuse them:
- a path the document **cites as existing** → must exist right now;
- a path the document **instructs to create** → must *not* exist yet, and must appear in a
  scope/phases section rather than in "Components / Files" describing the current state.

```bash
grep -ohE '[a-zA-Z0-9_./-]+\.(ts|tsx|py|js|jsx|go|rs|sql|md|yml|yaml)' DOC.md \
  | sort -u | while read p; do [ -e "$p" ] || echo "MISSING: $p"; done
```

**Relative markdown links** — resolve from the document's own directory:

```bash
grep -ohE '\]\((\.\.?/)?[^)#]+\.md' DOC.md | sed 's/^](//' | sort -u \
  | while read p; do [ -f "$(dirname DOC.md)/$p" ] || echo "BROKEN LINK: $p"; done
```

**Commands** — the module/script exists and the cited flag exists. Having the module is
not enough: an invented flag stalls execution just the same. Read the argument parser;
do not guess.

**Symbols** — `grep` for the definition, not just any mention. A cited function requires
`def name`/`function name`/`class Name`. Database column and index: look in the migration
that creates them, not in the code that reads them.

**Numbers** — every number that becomes an acceptance criterion must carry a date and
source. Re-run the cheap ones. Mark the rest as `*(measured YYYY-MM-DD)*`.

### 3. Separate historical records from acceptance criteria

An old number is not always an error. A dated block ("baseline measured on 2026-08-24") is
a **historical record and must not be updated** — rewriting it falsifies a measurement.
Only update numbers that serve as future acceptance criteria.

When in doubt, ask. Never silently overwrite a dated number.

### 4. Report

Output a single table: `Claim | Location (file:line) | Verdict | Fix`. Verdict is
`✅ verified`, `❌ missing`, or `⚠️ exists with mismatch` (e.g., function exists, but with
a different signature — the most dangerous case, because it passes a naive grep).

Do not modify the document without showing the table first, unless the user has already
authorized fixes.

## Rules

- **Verifying means running, not inferring.** Use `ls`, `grep`, and read the parser. Memory
  from a previous session does not count as verification.
- **A symbol that exists with a different signature is a failure**, not a pass. `formatSalary`
  existing does not mean it accepts the parameter the document assumes.
- **"Path to create" and "existing path" are different buckets.** Confusing them produces
  mass false positives and trains the user to ignore the gate.
- **Never rewrite a dated number** without confirming with the user.
- The gate runs on the document **before** delivery, not after someone trips over it.

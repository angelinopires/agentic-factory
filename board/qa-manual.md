# QA Verification Manual

Read by QA before executing each verification stage (A1, A2, B).

## Stages

| Stage | Method | Output |
|---|---|---|
| **A1** Machine Review | Run only if PRD header has `**A1:** yes`; skip if `**A1:** no`. Standard execution: `/code-review high`; auth, security, or critical data mutations: `/code-review xhigh` + `security-review` skill. If Dev ran on a fallback Claude model, also run `codex review --base main` when quota permits. | Findings list |
| **A2** Spec & Proof | Check Constraints, "Must Not Happen", User Stories → tests, and cryptographic gates: verify `qa-proof.py` record (below), run only diff-touched tests and boundary mutations. | GREENLIGHT / HOLD |
| **B** Live Product | Live browser verification (`verify-ui`) across 375px → 768px → 1280px (or 390px and 1440px mobile-first targets). | PASS / FAIL |

- **Screens with Designer HTML:** verify user intent, hierarchy, interactive states, and mobile-first responsiveness against the approved HTML preview rather than brittle pixel matching. Documented improvements pass; any deviation that changes behavior or omits a state (empty, loading, error) is a finding.
- **100% Interaction in Stage B:** open every modal, drawer, and dropdown; test hover and keyboard focus. Hydration or console errors block PASS.
- **Unimplemented Scope items are never LOW.** Any finding contradicting an already-ticked `[x]` checkbox blocks PASS.
- **`**Infra:** yes`** without "CI-equivalent" container test output (`infra-preflight` §3) pasted in the PRD results in HOLD.

## Hard-Earned Lessons & Gates

- **A1 checks beyond static linters:** component naming conventions, zero arbitrary hardcoded Tailwind tokens when design tokens exist, new components registered in `/design-system`, user-facing copy aligned with project vocabulary, and zero duplicate dependencies when an equivalent exists in the repo. Log one summary line in the PRD for A1: tool, level, duration, and findings by severity (or `A1: no`).
- **Stage A2 Cryptographic Gates:** QA does not re-run the entire test suite, linter, or typechecker from scratch. Verify the Dev's cryptographic test proof and working-tree hash, then run only the tests touched by the diff plus mutation checks:

  ```bash
  P={{WORKSPACE_ROOT}}/scripts/qa-proof.py
  R={{PLANNING_DIR}}/runs/<PRD>
  mkdir -p $R
  # Dev (Part 3, after final commit) records the suite execution proof:
  python3 $P record --prd <PRD> --order <PRD>-<side> --base main --out $R/qa-proof-<side>.json -- <suite command>
  # QA (Stage A2, in the same worktree) verifies the cryptographic proof:
  python3 $P verify $R/qa-proof-<side>.json
  ```

  Working-tree dirty hash verification (returns empty-input SHA-256 on a clean tree):

  ```bash
  { git diff HEAD --binary; git ls-files -o --exclude-standard -z | xargs -0 shasum -a 256; } | shasum -a 256
  ```

- **Measurement tools:** before using any validation or reporting script to measure the product, prove with `file:line` from both sides that it uses the exact same predicate as production code.
- **Mutation testing:** run 1 boundary mutation per Constraint in a scratch copy during Round 1 and record the `mutation → test failure` table in the PRD. Any surviving mutation causes HOLD. Every test deleted in the diff must be justified (retired UI) or restored; unexplained test deletion causes HOLD.
- **Reuse the `QA` Portal** (`navigate`, never `create`) so the user can observe live verification. Use headless Playwright only for repetitive multi-step setups. Verify external links via DOM attributes (`href`, `target`, `rel`) without clicking them.
- **Never trigger full external syncs** against live third-party APIs during QA: run dry-runs with a frozen clock against recorded fixtures.
- **Root-cause every finding:** include `getComputedStyle` / `getBoundingClientRect` numbers plus `file:line` for visual bugs. From Round 2 onward, new findings ≤ MEDIUM outside the diff that do not contradict Scope go to the technical debt log; cheap bugs in the touched file are fixed inline.
- **Targeted reading:** use `grep -n` + `sed -n` rather than reading whole files; read `git diff` in full during A2.
- **Final verdict:** always send PASS in a fresh turn after ticking Part 3 and Part 4 `[x]` in the PRD. Never modify application code.

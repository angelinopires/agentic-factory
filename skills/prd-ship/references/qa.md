# QA — Observable Behavior

Loaded by Phase B of `/prd-ship`, **only after Phase A passes with zero CRITICAL/MEDIUM findings**.
QA validates what the user sees and does. It does not read diffs.

## B0 — PRD Type

- **UI** — `### Components / Files` includes `.tsx/.ts/.jsx/.js/.vue/.svelte/.css/.html` or files under `web/`, `app/`, `frontend/`. Follow B1–B6.
- **Non-UI** — run the observable verification named in the PRD itself (`curl` against an endpoint, CLI command, database query, row count), paste the real output under each User Story and Acceptance Criterion, and skip to B6.

## B1 — Environment

Start the local stack using the procedure documented in the project's `CLAUDE.md` (e.g., `docker compose up -d` + health check). If startup fails → environment blocker, verdict **HOLD**. Never tick QA items without a live runtime.

## B2 — QA User (idempotent)

Convention: `qa@<project>.test` (standard user) and `qa-admin@<project>.test` (admin), where `<project>` is the project name in `board.config.json`. Create only missing accounts using the command documented in the project's `CLAUDE.md`. Never invent credentials and never create test users in production. Reuse an already-authenticated session whenever available.

Authenticate using the first method that succeeds: Playwright storage state (`tests/e2e/.auth/<role>.json`) → project CLI login-link generator → magic link read from local logs.

An email provider error (401, 5xx, rotated API key) in local dev is an **environment** issue, not a PRD defect: fall back to the next authentication method in the list and never issue HOLD over an external email sandbox error. If no authentication path works, report an environment blocker to the Manager with the exact error output pasted.

## B3 — Test plan before opening the browser

From Part 4 and `### Must Not Happen`, write the test plan into the report **before** executing:

```text
T1 — <action> → <observable outcome>
T2 — …
```

Every bullet in `### Must Not Happen` becomes at least one `T` scenario.

## B4 — Execution

**Playwright** (if the project has `playwright.config.*`): create or extend `tests/e2e/<prd-slug>.spec.ts` with one `test()` per automatable `T`, using `data-testid` or accessible role selectors. Run the spec **twice**; both runs must agree — a flaky test is a finding.

**Browser** — Claude Code: `preview_start`/`preview_*` for a local dev server, or Chrome MCP tools (`mcp__Claude_Browser__*`). In Maestri / Codex / Antigravity: `maestri portal` (`create`, `resize`, `snapshot`, `screenshot`, `logs`) or the browser subagent. Outside browser-capable harnesses without Playwright: visual QA cannot run → record `"Visual QA pending — run /prd-ship in a browser-enabled harness"` and set verdict to **HOLD** (unverifiable). Never approve UI without seeing it rendered.

For every non-automated `T`, execute it in the browser and capture evidence (screenshot or accessibility snapshot). Then run the exploratory checklist:

| # | Check |
|---|---|
| E1 | Error path (invalid input, API offline) — is a clear error shown to the user? |
| E2 | Recovery without a full page reload |
| E3 | Empty state explained clearly, never a blank screen |
| E4 | Boundary values: long text, zero, maximum, special characters |
| E5 | Double action: does double-clicking / submitting twice create duplicate effects? |
| E6 | Zero console errors — **hydration errors block GREENLIGHT** |
| E7 | End-to-end flow, not just the isolated screen |

## B5 — Breakpoints

Run `/verify-ui <route>` for every affected route across `375` → `768` → `1280`. No breakpoint may be skipped; if a screenshot tool fails, fall back to DOM/layout inspection — never mark a breakpoint `"assumed OK"`. Restore the viewport to `1280` at the end.
Visual regression = MEDIUM; if it renders the feature unusable, CRITICAL.

## B6 — Record evidence

Passed: tick each User Story and Acceptance Criterion **inside the PRD**, one by one, with the observed evidence pasted immediately below it, and finally tick `- [x] QA passed`. If the PRD header has `**Demo:** yes`, run `/prd-demo` to record the visual evidence package.
Failed: every failure becomes a finding formatted per `references/review.md`, including reproduction steps, expected behavior, and actual behavior.

Report tables:

```markdown
### Test Plan
| ID | Scenario | Playwright (1 / 2) | Browser | Status |

### Exploratory Checklist
| # | Status | Evidence |

### Breakpoints
| Breakpoint | Method | Status | Notes |
```

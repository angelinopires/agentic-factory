---
name: design-port
description: Port a finished design (Claude Design canvas, Artifact, HTML export, Figma) into production code with measured fidelity. Three phases — pre-code check (canvas vs. decisions and copy claims vs. evidence), literal port, and side-by-side fidelity gate. Use when a PRD implements an already-designed screen, when /prd authors that PRD, when Frontend executes it, and when QA validates it. Do NOT use to invent a new screen from scratch or for backend/system features.
---

# design-port — finished design into code, measured

Porting a design is a different craft from implementing a feature: the specification is the artboard,
not the prose in the PRD. Origin: Case #147 (2026-10-14), 4 rounds. Round 1 reinterpreted the canvas;
once switched to a literal port, animations and fonts matched — the remaining 52 deviations came from
**the canvas contradicting prior product decisions** and **unverified copy claims**. That is why
Phase 0 exists.

| Phase | Owner | Output |
|---|---|---|
| 0. Before code | PRD author (`/prd`, Explorer) | PRD with saved reference export, resolved conflicts, verified claims |
| 1. Literal port | Frontend executor (`Dev` / `Dev Front`) | Production code + per-section screenshots |
| 2. Fidelity gate | Independent QA (never the author of the port) | Deviation table, PASS/FAIL verdict |

## Phase 0 — before code

1. **Saved design export** under `planning/<project>/runs/<n>-design/reference/` (self-contained HTML
   from the canvas, `.dc.html`, or exported Figma frames). CLI agents cannot read cloud Artifacts directly.
   If the export is missing: stop and ask the user; do not write the PRD without it.
2. **Per-section visual baseline**: screenshot each artboard section at 375, 390, and 1440 before any
   application code is written.
3. **Canvas × decisions**: list every previously settled product decision (grill session, discovery note,
   epic) regarding section order, content, and behavior, and check it against the artboard. Any conflict
   triggers an immediate question to the user **now**, naming both options, with the chosen answer
   recorded in the PRD. Never allow "follow the canvas" and "follow the decision" to coexist.
4. **Claims × evidence**: every claim in the copy (metrics, "only shows X", "guarantees Y", links, CTAs)
   must cite `file:line` or a verified data source, or be marked for removal/replacement in a
   `Claim | Evidence | Verdict` table.
5. **Mobile behavior settled**: either a mobile artboard exists in the export or the exact responsive
   rules are written in the PRD. Never leave mobile layout invention to the implementer.
6. **Intentional divergences** (design-system token replacing raw hex, live data replacing static mock,
   revised copy) are listed explicitly with their rationale. Everything not on that list must be a 1:1 copy.

## Phase 1 — literal port

- Copy the markup structure, CSS rules, typography, and animations (`@keyframes`, `transition`,
  `animation-delay`, timeline JS) directly from the reference export. Replace **only** what the
  intentional-divergences list specifies: raw color → design token, mock string → real data source,
  draft text → approved copy. Never "rebuild inspired by the reference".
- Existing design-system components only enter where the PRD explicitly mandates them (e.g., live product
  component replacing a static illustration).
- If both the mobile artboard and written mobile rules are missing: stop and ask the dispatcher.
- Deliver per-section screenshots at the exact same viewports as the Phase 0 baseline.

## Phase 2 — fidelity gate

The standard is equality with the artboard, not "doesn't look broken". Any deviation without a written
decision in the PRD is a **FAIL**.

1. **Side-by-side per section** at 375, 390, and 1440. Re-verification after fixes compares only the
   cropped section that changed; full-page capture happens only on final sign-off (full-page screenshots
   on every iteration blow up QA context).
2. **Measure on the artboard's own selector**: record the selector and computed value from the reference
   export next to the live page's value. Never measure an inner child in place of the container block
   (Case #147: inner `span` measured at 18×40 instead of `.big` at 34×50).
3. **Typography via computed style** (`getComputedStyle`): `font-family`, `font-weight`, `font-size`,
   `line-height`, and `letter-spacing` for every text hierarchy level, comparing identical selectors on
   both sides.
4. **Animation**: compare duration, easing, stagger order, and final resting state against the export's
   CSS/JS; capture frames at matching timestamps (start, midpoint, end) with motion enabled. Verify
   `prefers-reduced-motion` in a separate pass. A single-frame pixel diff checks one instant, not the
   timeline.
5. **Mobile against the mobile artboard**: block ordering, line wraps, and what collapses or hides.
6. **Interactive states**: compare every state present in the artboard (empty, submitted, error, waitlist
   confirmation), not just the default state.
7. **Output**: write `round-<N>-deviations.md` inside the run folder, one row per deviation —
   `Section | Axis | Artboard | Live Page | Selector` — appending after each section rather than holding
   the entire list in context memory.

Optional automation: Playwright `toHaveScreenshot` per locator if the project already has `@playwright/test`
configured. Visual diffs complement — never replace — items 3 and 4.

## Harness portability

- **Asking the user:** use `AskUserQuestion` in Claude Code; in Codex and Antigravity, ask a numbered
  question with lettered options in chat or via the dispatcher (on the Maestri canvas, report back to
  Manager/Explorer).
- **Screenshots and computed styles:** use `preview_*` or `maestri portal` in Claude Code/Maestri; use
  Playwright CLI or headless browser in Codex.

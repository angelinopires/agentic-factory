---
name: ui-ux-analysis
description: Comprehensive UI/UX audit specialist. Analyzes a live product (not code) against WCAG 2.2 AA (with 2.1 compatibility), design system tokens, mobile-first responsiveness, and Core Web Vitals. Includes modern accessibility tests (zoom, color-scheme, motion preferences, screen reader compatibility). Generates a markdown audit report, updates the metrics baseline, and automatically creates PRDs for any new issues not yet covered in planning/.
origin: custom
---

# UI/UX Analysis Skill

You are a UI/UX specialist conducting a comprehensive audit of a project's user interface and experience. You analyze the **live product** (not code), assess it against WCAG 2.2 AA accessibility standards (with backwards compatibility to WCAG 2.1), design system tokens, and modern UX patterns, and generate a structured markdown report with actionable, PRD-ready recommendations.

**Standards:** WCAG 2.2 AA primary (released 2023); WCAG 2.1 AA for legacy projects. Includes modern accessibility: zoom testing (200%), color-scheme preferences, motion preferences, screen reader compatibility, form error handling, and ARIA live regions.

**Tone:** Constructive and opportunity-focused. Frame every issue as an improvement, not a failure.
**Output:** Markdown audit report saved to `planning/[project]/ui-ux-audits/` (or `brain/projects/[project]/ui-ux-audits/` if configured) with baseline tracking.

---

## Input Parameters

When invoked, extract these from the user's message or context:

- **project** *(required)*: Project name or slug (e.g., `my-app`)
- **project-path** *(optional)*: Path to the project repository. Defaults to `projects/[project]`
- **scope** *(optional)*: `all` | `critical-path` | comma-separated routes. Defaults to `all`
- **focus** *(optional)*: `accessibility` | `design` | `performance` | `all`. Defaults to `all`

---

## Phase 1 — Context Discovery

Read the project's own docs to understand what it should look like and how it should behave. Do NOT assume — derive from the docs.

**Read in order:**

1. `[project-path]/CLAUDE.md` — Stack, routes, design system rules, component locations, do/don't constraints
2. `[project-path]/docs/*-product-spec.md` (or similar) — Business goals, target audience, MVP scope
3. `[project-path]/docs/design-tokens.md` — Colors, typography, spacing, borders, motion tokens
4. `[project-path]/docs/ui-patterns.md` — Component APIs, interaction patterns, layout rules
5. `[project-path]/docs/FEATURES.md` (or `brain/projects/[project]/features/FEATURES.md`) — Feature specs, page-by-page context

**Extract and note:**

- The project's design language (colors, fonts, spacing system)
- The target audience and primary user journeys
- Routes available in the current MVP
- Component names and their expected behavior
- Any explicit accessibility requirements documented
- Any "DO NOT" constraints that affect UI choices

---

## Phase 2 — Baseline Comparison (Deduplication)

**Before testing, check if a previous audit exists.**

Look for files in `planning/[project]/ui-ux-audits/`:

```text
planning/[project]/ui-ux-audits/
├── YYYY-MM-DD-[name]-audit.md   (previous audit files)
└── metrics-baseline.md          (aggregated issue tracker)
```

**If `metrics-baseline.md` exists:**

Read it and extract the issue registry — the list of all previously identified issues with their status and PRD references.

This allows you to classify each finding in the new audit as:

| Tag | Meaning | PRD action |
| --- | ------- | ---------- |
| `✓ Fixed` | Was in previous audit, now resolved | No PRD needed |
| `⚠️ Regression` | Was in previous audit with a PRD, still not fixed | Flag only — PRD already exists |
| `🆕 New` | Not seen before | Create a PRD entry |
| `→ No Change` | Still present, no PRD exists yet | Create a PRD entry |

**If no previous audit exists:**

Mark all findings as `🆕 New` and create the baseline from scratch.

---

## Phase 3 — Page Discovery

Identify all pages to audit from the project context docs:

1. **From `CLAUDE.md`**: Extract the Routes section — these are the authoritative page list
2. **From feature specs**: Check project feature docs for per-page descriptions
3. **Apply scope filter**: If `scope=critical-path`, only audit homepage + primary content pages

**Default priority order:**

1. Homepage `/`
2. Primary content page (article, product, dashboard, etc.)
3. Category/listing pages
4. Secondary pages (hubs, department landings, settings, etc.)
5. Edge states (empty states, error pages) — if accessible via preview

List the pages to test before starting the browser analysis.

---

## Phase 4 — Live Product Testing

For **each page**, test at three breakpoints. Use preview tools only — do not read source code.

### Breakpoints

| Name | Width | Height |
| ---- | ----- | ------ |
| Mobile | 375px | 812px |
| Tablet | 768px | 1024px |
| Desktop | 1280px | 800px |

### Zoom Testing

Additionally, test at **200% zoom** on desktop:

```text
1. Resize the viewport → desktop (1280px × 800px)
2. Set zoom to 200% in browser dev tools
3. Screenshot → capture zoomed state
4. Verify no horizontal scroll
5. Verify text readable without further zoom
6. Verify all interactive elements still accessible
7. Reset zoom to 100%
```

**Critical issues to check:**

- Horizontal scroll bar appears (layout breaks)
- Text becomes unreadable
- Overlapping content
- Buttons/form fields become inaccessible
- Navigation collapses incorrectly

### Workflow Per Page

```text
1. Start the preview (if not running)
2. Resize the viewport → set breakpoint
3. Navigate to the page URL
4. Screenshot → capture visual state
5. Read the accessibility tree
6. Read console messages → errors/warnings
7. Read network requests → load times and resource sizes
8. Click / fill → test interactions (nav, search, tabs, carousels)
9. JS eval `getComputedStyle` → verify CSS values on key elements
10. Repeat for next breakpoint
```

### What to Observe at Each Breakpoint

**Accessibility:**

- Semantic HTML landmarks (nav, main, section, article, header, footer)
- HTML lang attribute present and correct (e.g., `lang="en"` or `lang="pt-BR"`, matching content language)
- Heading hierarchy (H1 → H2 → H3, no skips)
- ARIA attributes (tablist/tab roles, aria-label, aria-selected, aria-hidden, aria-expanded)
- Skip-to-content link present and visible on focus (keyboard accessible with visible focus ring)
- Focus management (visible focus ring, tab order logical, focus not obscured by sticky headers/modals)
- Color contrast (text on backgrounds — especially muted text variants; ≥4.5:1 for AA, ≥7:1 for AAA)
- Touch target sizing (all interactive elements ≥44×44px minimum WCAG AA; 48×48px recommended WCAG AAA on mobile)
- Alt text on images (meaningful text for content images; alt="" for decorative)
- Form labels and input associations
- Error messages clear and associated with fields (aria-describedby)
- Required fields marked (required attribute or aria-required)
- Field format hints provided (placeholder, aria-label, or aria-describedby)

**Responsiveness:**

- No horizontal scroll (unless intentionally designed, e.g., carousels)
- Text remains readable (no overflow, no clipping, no overlapping)
- Images/video maintain aspect ratios
- Grid/flex layouts reflow correctly
- Typography scaling smooth (no jarring jumps at breakpoints)
- Carousel/scroll areas show visual overflow hints (fade gradients)
- Navigation collapses/expands correctly on mobile

**Color Scheme Preferences:**

- Dark mode rendering correct (prefers-color-scheme: dark)
- Light mode fallback functional when forced
- Contrast ratios maintained in both modes (≥4.5:1 for AA, ≥7:1 for AAA)
- Text readable without additional adjustments
- Images and illustrations legible in both modes
- Borders and separators visible in both modes
- Custom colors use CSS variables aligned to design tokens

**How to test:** Emulate `prefers-color-scheme` dark and light with the viewport tool's color-scheme option

**Design Compliance:**

- Color tokens used correctly (no arbitrary hex values or inline styles)
- Typography tokens applied (font family, size, weight, uppercase rules match docs)
- Layout tokens followed (container max-width, horizontal padding, section spacing)
- Component patterns consistent (same card style across pages, same button variants)
- Borders, separators, overlays match design token definitions
- Gradients and overlays use defined CSS vars

**Interactions:**

- Navigation opens/closes correctly on mobile
- Search overlay (if present) opens, accepts input, closes correctly
- Tab/filter components switch content and update active state visually
- Carousels scroll, show prev/next controls, respond to keyboard
- CTAs and buttons have visible hover/focus states
- Animations respect prefers-reduced-motion (animations disabled/simplified when detected)
- Auto-play videos pause when motion preference is active
- Carousel transitions are instant instead of animated when motion preference is active
- Parallax or scroll effects disabled when motion preference is active

**Dynamic Content & ARIA Live Regions:**

- Dynamic updates (notifications, search results, load more) marked with aria-live
- aria-live region announces updates to screen readers (aria-atomic for complex regions)
- Confirm step present for destructive actions (delete, submit)
- Error recovery guidance provided (not just "invalid input")

**Screen Reader Compatibility (via accessibility tree):**

Use the accessibility tree to verify:

- All text alternatives present (alt text, aria-label, aria-labelledby)
- Heading structure logical (H1 → H2, no jumps)
- Form labels associated with inputs (via `for` attribute or ARIA)
- Interactive role elements properly marked (button, link, tab, menuitem, etc.)
- Navigation landmarks semantic (nav, main, contentinfo, region)
- Live regions and dynamic content announced correctly
- Link text meaningful (not "click here" or "more")

---

## Phase 5 — WCAG 2.2 AA Accessibility Audit

After testing all pages, categorize findings against **WCAG 2.2 AA** (primary) with backwards compatibility to WCAG 2.1 AA.

### Critical (Block launch if present)

- Missing alt text on meaningful images (WCAG 1.1.1)
- Form inputs without labels (WCAG 1.3.1)
- Navigation inaccessible by keyboard (WCAG 2.1.1)
- Contrast ratio < 4.5:1 on body text or < 3:1 on large text (WCAG 1.4.3)
- Content only perceivable by color (no text alternative) (WCAG 1.4.1)
- Missing HTML lang attribute (WCAG 3.1.1)
- Layout breaks at 200% zoom (WCAG 1.4.4)

### High Priority (Fix before or shortly after launch)

- Missing ARIA roles on interactive components (e.g., tabs without role="tablist") (WCAG 1.3.1)
- Touch targets < 44×44px on mobile (WCAG 2.5.5)
- Touch targets < 48×48px recommended (WCAG 2.5.5 AAA)
- Heading hierarchy violations (H1 → H3 without H2) (WCAG 1.3.1)
- Focus not visible on interactive elements (WCAG 2.4.7, 2.4.12)
- Focus obscured by sticky headers, modals, or UI overlays (WCAG 2.4.12)
- Carousel/modal not keyboard accessible (WCAG 2.1.1)
- Form errors not associated with fields (WCAG 3.3.1)
- Error messages unclear or missing recovery guidance (WCAG 3.3.4)

### Medium Priority (Post-launch phases)

- Animations not respecting prefers-reduced-motion (WCAG 2.3.3, 2.3.5)
- Decorative images not marked with alt="" (WCAG 1.1.1)
- Missing dynamic content aria-live announcements (WCAG 4.1.3)
- aria-atomic not used for complex live regions (WCAG 4.1.3)
- Missing breadcrumb navigation structure (WCAG 1.3.1)
- Required fields not marked (required attribute or aria-required) (WCAG 3.3.2)
- Field format hints not provided (WCAG 3.3.2)
- No confirm step for destructive actions (WCAG 3.3.4)

For each issue, record:

- **WCAG criterion**: (e.g., 1.3.1 Info and Relationships)
- **Affected element/page**: Be specific
- **Impact**: Who is affected and how
- **Fix**: Concrete implementation guidance

### WCAG 2.2 New Criteria (Additional to 2.1)

**Verify these WCAG 2.2-specific criteria:**

- **2.4.12 Focus Not Obscured (Minimum)**: Focus indicator not completely hidden by UI elements (sticky headers, modal backdrops, absolutely positioned overlays)
- **2.4.13 Focus Not Obscured (Enhanced)**: Focus indicator at least partly visible (higher bar than Minimum)
- **3.3.7 Redundant Entry**: If password confirmation field present, original password visibility option allows skipping confirm field
- **2.5.7 Dragging Movements**: If drag actions present, alternative non-drag method available
- **2.4.11 Focus Visible**: Focus indicator visually apparent for all focusable elements

---

## Phase 6 — Design System Compliance Audit

Verify adherence to the project's own design tokens and patterns from Phase 1.

**Colors:** All values use design tokens (no raw hex). Opacity scale applied correctly.
**Typography:** Correct font families, sizes, weights, case per token docs.
**Layout:** Container max-width, horizontal padding, section spacing all match.
**Components:** Consistent use of defined components (Button, Card, Badge, etc.).
**Borders:** Using defined border opacity tokens for cards, separators, interactive states.
**Motion:** Animation keyframes match the defined system. `prefers-reduced-motion` respected.

---

## Phase 7 — Performance Observations

Gather Core Web Vitals observations from network requests and console messages.

**Metrics to estimate:**

| Metric | Target | Signal |
| ------ | ------ | ------ |
| LCP | < 2.5s | Largest element load time (hero image/video/headline) |
| FID | < 100ms | First interaction response time |
| CLS | < 0.1 | Layout shifts during load (visible jumps) |
| Page Load | < 3s | Total load time from preview network |

**Also note:**

- Console errors or warnings during load
- Slow network resources (images > 500KB, unoptimized fonts)
- Layout shifts during load (elements repainting or reflowing)
- Image optimization (`next/image` used? Correct formats?)
- Video load behavior (autoplay, muted, preload settings)

*Note: These are observational estimates from dev preview. Full Lighthouse audit should be run in production for definitive scores.*

---

## Phase 8 — Generate Audit Report

Write the report to: `planning/[project]/ui-ux-audits/YYYY-MM-DD-[description]-audit.md`

Use today's date. For description, use: `full-audit`, `accessibility-audit`, `mobile-audit`, etc. based on focus.

### Report Template

```markdown
# UI/UX Audit — [Project Name]

**Date:** YYYY-MM-DD
**Scope:** [Pages tested, e.g., "All MVP pages (/, /category, /category/[slug])"]
**Breakpoints tested:** Mobile (375px), Tablet (768px), Desktop (1280px)
**Methodology:** Live product testing via preview browser, accessibility tree inspection, network analysis
**Previous audit:** [path to previous audit file, or "None — first audit"]

---

## Summary of Changes Since Last Audit

> Skip this section if this is the first audit.

| Status | Count | Items |
| ------ | ----- | ----- |
| ✓ Fixed | X | [brief names] |
| ⚠️ Regression | X | [brief names] |
| 🆕 New | X | [brief names] |
| → No Change (ongoing) | X | [brief names] |

---

## Executive Summary

[1-2 paragraphs: overall product state, top findings, launch readiness]

**Overall Status:** `LAUNCH-READY` | `NEEDS REFINEMENT` | `BLOCKED`

| Priority | Count |
| -------- | ----- |
| Critical | X |
| High | X |
| Medium | X |

---

## Issues Requiring New PRDs

> Only `🆕 New` and `→ No Change` (no PRD yet) issues appear here.
> This section is consumed by the PRD-creation routine.

### [Issue Title] `[🆕 New | → No Change]`

**Priority:** Critical | High | Medium
**Impact:** [Users affected, pages affected]
**Effort:** [Time estimate]
**Why:** [Business or UX impact]
**How:** [Concrete implementation guidance]

---

## Issues Already Captured (No New PRD Needed)

### ✓ Fixed Since Last Audit

- [Issue name] — was in [previous audit date] — now resolved

### ⚠️ Regressions (PRD exists, still unfixed)

- [Issue name] — PRD: `[filename]` — Status: [In Progress/Draft] — Action: check progress

---

## Page Analysis

> Sub-headings within each page section MUST be prefixed with the page name to avoid duplicate heading violations.
> Pattern: `#### [Page Name] Accessibility`, `#### [Page Name] Responsiveness`, etc.
> Example: `#### Homepage Accessibility`, `#### Article Accessibility`, `#### Category Landing Accessibility`

### [Page Name] `[Route]`

#### [Page Name] Accessibility

- ✓ [What passes]
- ⚠ [WCAG issue with criterion reference]
- ✗ [Critical problem]

#### [Page Name] Responsiveness

- ✓ [Mobile/Tablet/Desktop: what works]
- ⚠ [Issue at specific breakpoint with details]

#### [Page Name] Design Compliance

- ✓ [Token usage correct]
- ⚠ [Deviation from design system]

#### [Page Name] Performance

[Load time, LCP element, CLS observations, errors]

#### [Page Name] Improvements

Priority: [Critical/High/Medium]

1. **[Improvement title]** `[🆕 New / → No Change / ⚠️ Regression]`
   - **Why:** [Impact on users or business]
   - **How:** [Implementation approach]

---

## Full Accessibility Audit (WCAG 2.2 AA)

### Critical Issues

[None | List with WCAG reference, affected element, impact, fix]

### High-Priority Issues

[List with WCAG reference, affected element, impact, fix]

### Medium-Priority Issues

[List with WCAG reference, affected element, impact, fix]

---

## Design System Compliance

### Token Audit

| Area | Status | Notes |
| ---- | ------ | ----- |
| Colors | ✓ Compliant / ⚠ Issues | [Details] |
| Typography | ✓ Compliant / ⚠ Issues | [Details] |
| Layout & Spacing | ✓ Compliant / ⚠ Issues | [Details] |
| Components | ✓ Compliant / ⚠ Issues | [Details] |
| Motion | ✓ Compliant / ⚠ Issues | [Details] |

### Deviations Found

[List any design system violations with affected pages and fix]

---

## Responsive Design Analysis

### Mobile (375px)

[Observations, issues, strengths]

### Tablet (768px)

[Observations, issues, strengths]

### Desktop (1280px)

[Observations, issues, strengths]

---

## Performance Analysis

### Core Web Vitals (Estimated)

| Metric | Observation | Target | Status |
| ------ | ----------- | ------ | ------ |
| LCP | [value or estimate] | < 2.5s | ✓ / ⚠ / ✗ |
| FID | [value or estimate] | < 100ms | ✓ / ⚠ / ✗ |
| CLS | [value or estimate] | < 0.1 | ✓ / ⚠ / ✗ |
| Page Load | [value] | < 3s | ✓ / ⚠ / ✗ |

### Observations

[Load behavior, console errors, image optimization, video handling]

### Performance Recommendations

[Performance improvements with priority and implementation guidance]

---

## Recommendations

### Quick Wins (High impact, low effort)

1. **[Title]** — Why: [reason] — How: [approach] — Effort: [estimate]

### Strategic Improvements

1. **[Title]** — Why: [reason] — How: [approach] — Effort: [estimate]

---

## Testing Methodology

**Tools used:** Preview browser, viewport emulation, accessibility tree inspection, network monitoring
**Limitations:** Dev server only (not production build); emulated viewports (not real devices); no automated a11y scanner; motion animations not fully testable in preview
**Follow-up recommended:** Lighthouse on production build; real device testing (iOS Safari, Android Chrome); automated axe-core scan; screen reader testing (VoiceOver, NVDA)

---

End of Audit
```

---

## Phase 9 — Update Baseline

After saving the audit report, update `planning/[project]/ui-ux-audits/metrics-baseline.md`.

**Create it if it doesn't exist. Append a new row if it does.**

### Baseline Template (create on first run)

```markdown
# UI/UX Metrics Baseline — [Project]

Tracks audit findings and Core Web Vitals across runs for trend analysis.
Updated automatically by `/ui-ux-analysis` after each audit.

---

## Issue Registry

| Issue | First Seen | Status | PRD | Last Seen |
| ----- | ---------- | ------ | --- | --------- |
| [Issue name] | YYYY-MM-DD | Identified / PRD Created / Fixed | [filename or —] | YYYY-MM-DD |

---

## Core Web Vitals Trend

| Date | LCP | FID | CLS | Load | Notes |
| ---- | --- | --- | --- | ---- | ----- |
| YYYY-MM-DD | [value] | [value] | [value] | [value] | [audit file link] |

---

## Audit History

| Date | File | Pages | Critical | High | Medium | Status |
| ---- | ---- | ----- | -------- | ---- | ------ | ------ |
| YYYY-MM-DD | [filename] | [count] | [count] | [count] | [count] | [LAUNCH-READY/etc] |
```

**Update rules:**

- Add new findings to Issue Registry with status `Identified`
- Update existing issues: change status to `Fixed` if resolved, keep `Identified` if still present
- Append new row to Core Web Vitals Trend
- Append new row to Audit History

---

## Success Criteria

Before finishing, verify:

- [ ] Audit report saved to `planning/[project]/ui-ux-audits/YYYY-MM-DD-[name]-audit.md`
- [ ] All pages tested at 3 breakpoints (mobile/tablet/desktop)
- [ ] WCAG issues categorized (Critical / High / Medium) with WCAG references
- [ ] Design system compliance verified against actual design tokens from docs
- [ ] Core Web Vitals estimates documented
- [ ] Each finding tagged: `✓ Fixed` / `⚠️ Regression` / `🆕 New` / `→ No Change`
- [ ] "Issues Requiring New PRDs" section present with only `🆕 New` / `→ No Change` items
- [ ] Recommendations include What + Why + How + Impact + Effort
- [ ] `metrics-baseline.md` updated with new row
- [ ] Tone is constructive throughout (opportunities, not failures)
- [ ] PRDs created for all `🆕 New` / `→ No Change` issues not already covered in `planning/[project]/`

---

## Usage Examples

```bash
# Full audit of a project
/ui-ux-analysis project=my-app

# Focused accessibility-only audit
/ui-ux-analysis project=my-app focus=accessibility

# Critical path only (homepage + main content page)
/ui-ux-analysis project=my-app scope=critical-path

# Audit a different project
/ui-ux-analysis project=admin-portal
```

---

## Phase 10 — PRD Creation

After saving the audit report and updating the baseline, automatically create PRDs for every issue listed in the **"Issues Requiring New PRDs"** section of the new audit report.

**This phase runs unconditionally after Phase 9** — no extra invocation needed.

### Step-by-step

1. **Parse** the "Issues Requiring New PRDs" section from the audit report just saved.
   - If the section is empty (no items), skip this phase entirely.

2. **For each issue listed**, search `planning/[project]/` (all subdirectories: `ready/`, `archive/`, `done/`) for an existing PRD whose filename or title closely matches the issue title.
   - Use `find` or `ls` to scan all three folders.
   - A "match" means the same root problem (not just the same words). Use judgment.

3. **If a matching PRD already exists** → skip. Do not create a duplicate.

4. **If no match is found** → create a new PRD at `planning/[project]/ready/YYYY-MM-DD-[kebab-title]_prd.md`.

### PRD format

Follow `templates/planning/_template_prd.md` (or `planning/_template_prd.md` in the workspace) exactly. Use the issue's **Priority**, **Impact**, **Effort**, **Why**, and **How** fields from the audit report to fill in the content.

Required fields:

- `Status: Ready for Implementation` — never Draft
- `Complexity: simple` for issues with Effort ≤ 30 min; `complex` otherwise
- Part 2 — Act: specific, actionable tasks derived from the **How** field
- Part 4 — QA: user stories that verify the fix is observable in the browser

### After creating PRDs

Update `metrics-baseline.md`: for each new issue whose PRD was just created, set its `Status` to `PRD Created` and its `PRD` column to the new filename.

## Harness portability

- **Browser inspection:** use `preview_*` tools in Claude Code, `maestri portal` (`create`, `resize`, `snapshot`, `screenshot`, `logs`) on the Maestri canvas, or Playwright / browser sub-agent in Codex and Antigravity.

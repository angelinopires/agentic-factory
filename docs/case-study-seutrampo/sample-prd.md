# Search Summary Bar (#230)

> **Context:** This is a sanitized English translation of a real production PRD (`planning/seu-trampo-ai/ready/2026-11-18-resumo-da-busca_prd.md`) executed by the Maestri board on November 18–19, 2026. Notice how `Overview` states only the code delta, `Technical Detail` cites exact `file:line` numbers and `grep` non-duplication proofs, `Part 2` builds in `/design-system` first (Phase A) before wiring the live feed (Phase B), and `Review feedback` logs exact DOM pixel measurements across 6 rounds.

**Project:** seu-trampo-ai
**Status:** Ready — Manager 2026-11-18 (`230-READY` verified; Open Items 2 and 3 decided by Human)
**Complexity:** simple
**Infra:** no — `web/` only; no DB migration, Docker, compose, cron, or CI workflow changes
**Demo:** no — evaluated directly in `/design-system` and live feed (2026-11-18)
**A1:** no — no new backend data; `by_tier` is already returned by `/api/stats`
**Created:** 2026-11-18
**Decisions:** `runs/card-summary/decisions.md` (PRD B) · reference `runs/card-summary/human-reference.md`, `13.jpg` (390px), `14.jpg` (desktop)
**Depends on:** `#229` (Job Card Redesign) — archived; Part 1 verified against `main` post-`#229` (`d7c6778`, 2026-11-18)
**Collides with:** nothing in flight. `#224b` and `#229` are already on `main`; `JobsWorkspace.tsx` (mounts `StatsBar`) and `JobFilterBar.tsx` only need revalidation if another PRD touches them before execution

---

## Part 1 — Plan

> Premises verified on `main` at `d7c6778` (2026-11-18, post-`#229`); delta-check in Technical Detail. No cited symbol moved.

### Overview

The current search summary (`web/src/components/header/StatsBar.tsx`) is a plain text block: icon, total count, sort dropdown, and a single string `"Profile match: 14 Top · 28 High..."`. Replace it with **one** unified component: total count + sort control, a ~5px proportional segmented bar colored by match tier, and a 4-position legend with counts. Done when: both bar and legend read from `by_tier`, always keep 4 fixed positions, and clicking opens the score explanation modal.

### Scope

1. **Single component (`StatsBar`):** total (`"N jobs"`) + sort (`SortMenu`, existing) · ~5px segmented bar, **proportional** to `by_tier`, tier tokens (`--color-tier-*` in `index.css`), small gap, **zero animation** · legend with colored dot, count, and label (`Top` / `High` / `Medium` / `Low`).
2. **Layout:** desktop matches `14.jpg` (3 rows: total + sort; segmented bar; single-line legend). `390px` matches `13.jpg` (4-column legend, ~12px padding, number stacked above label so 3-digit and 4-digit counts never collide). No `"Search summary"` heading; no invented metrics.
3. **Legend does not filter.** Clicking anywhere on the bar or legend opens the existing score explanation dialog (`openScoreLegend`, `HelpModalContext`; `ScoreLegend.tsx`), including the new copy line **"match score ≠ hiring probability"** (reviewed by `Writer`).
4. **Single source of tier labels** ("Information Standard" rule): `Top/High/Medium/Low` are currently duplicated in `StatsBar.tsx:53-56` and `TierFilterPills.tsx:25`; extract a single canonical table in `web/src/types/tier.ts` (or `lib/`) shared by both components without creating a third copy.
5. **Zero-count tier** renders as `"0 Low"`, muted (secondary/attenuated text color); always 4 positions in fixed order (`Top`, `High`, `Medium`, `Low`). When all tiers are zero (empty search): neutral track, no division by zero (`NaN`).
6. **Skeleton** reserves the exact same pixel height as the loaded state (`SKELETON_STATS`), with zero layout shift; error and `profileError` states reserve the exact same height and follow `#213` conventions.
7. **Accessibility:** the segmented track is decorative (`aria-hidden="true"`); the accessible button name lists all 4 tier counts (`"View match score criteria: ..."`).
8. **Design System First:** `/design-system` (`HeaderHelpSection.tsx`, `PREVIEW_STATS`; `ConnectionStatesSection.tsx`) renders the component at `390px` and `1440px` across normal, zero-tier, all-zero, skeleton, error, and `profileError` states **before** wiring the live page. Phase A must not alter the production feed: the new layout lands behind `variant="summary"` (default `legacy`), used only in `/design-system`; Phase B switches `JobsWorkspace` and removes `legacy`.
9. **Vocabulary:** add an entry to `CLAUDE.md` ("Information Standard") recording the rule *"legend does not filter"* and the score explanation sentence in the same PRD.

**Out of Scope:** filtering by tier when clicking the legend (the search filter bar already provides `"at least"` tier filtering from `#224b`; do not duplicate or create parallel filter state); changing `/api/stats`, matching, or scoring logic; breakdown by work mode or specialty; `My Jobs` tab (summary only appears in Explore, `activeTab === 'all'`).

### Must Not Happen

- **Misleading bar proportions:** segments that do not sum to 100% of track width, division by zero when total is 0, or invisible sub-pixel slivers (enforce a 2px minimum width when `count > 0` without distorting total width).
- **Legend mutating search filters** or creating state parallel to the search bar's compatibility filter.
- **Dropping a tier position** (hiding `"0 Low"`): currently `compatibilityTiers` runs `.filter(count > 0)` (`StatsBar.tsx:52-57`) and `stats-bar.test.tsx` (`"omits tiers whose counts are zero"`) locks that old behavior; all 4 positions are now fixed and that test assertion is inverted.
- **Layout shift** from skeleton to loaded, loaded to error, or when totals change; horizontal overflow at `375px`; narrow legend column wrapping labels mid-word.
- **Color as the sole signal:** numeric count and text label are always visible; keyboard focus ring is clearly visible on the clickable control.
- **Misrepresenting filtered tiers:** `/api/stats` respects `filters.tier` (`stats.py:81,99`, `filter_and_rank_jobs(tier=filters.tier)`); when `"Medium or better"` is active, lower tiers return `0` and the bar displays `"0 Low"`. This is expected (summary of the active search, not the unfiltered database) and covered by test.

### Technical Detail

**Components / Files** (verified at `d7c6778`):
- `web/src/components/header/StatsBar.tsx -> StatsBar` (145 lines) — segmented bar + 4-position legend; preserves `SortMenu`, `SKELETON_STATS` (line 22), `profileError`, `onOpenLegend`/`openScoreLegend`, `data-testid` values `stats-bar`, `stats-bar-skeleton`, and `stats-kpi-perfect` (consumed by 5 existing test suites).
- `web/src/pages/JobsWorkspace.tsx:453-463` — sole production caller; sits **outside** the list+detail split grid (`:474`), so summary width never depends on whether the detail drawer or sidebar is open.
- `web/src/components/help/ScoreLegend.tsx` (119 lines; title line 30, intro line 34) — adds `"Match score shows how well the job fits your profile. It is not your probability of being hired."`; callers of `openScoreLegend`: `StatsBar.tsx:39`, `ScoreSticker.tsx:71,84`, `TierFilterPills.tsx:67`; context in `HelpModalContext.tsx:10,36`.
- `web/src/components/controls/TierFilterPills.tsx:25` and `web/src/lib/search-filters.ts:11,26-28` — tier labels and `TIER_ORDER`; source for the single table in Scope 4.
- `web/src/pages/design-system/HeaderHelpSection.tsx`, `ConnectionStatesSection.tsx`, `ConnectionFeedDemo.tsx` — Design System demos and fixtures.
- Existing tests to update in Phase B: `stats-bar.test.tsx`, `controls-bar.test.tsx:165-176`, `keyboard.test.tsx:368-389`, `design-system.test.tsx:536-545`, `dashboard-searches.test.tsx:86-92`, `minhas-vagas.test.tsx:422-435`, `semantic-callers.test.tsx:30`, `design-system-coverage.test.ts:32`.

**Queries / API:** unchanged. `by_tier` (`StatsResponse`, `web/src/types/job.ts:128`, `Record<string, number>`, missing key = 0): `perfect_match | great_match | good_match | worth_a_look`. **Verified on server:** `by_tier` counts records in `user_records` and `total_unique = len(user_records)` (`server/api/routes/stats.py:121,130,147`), so the sum of the 4 tiers always equals `total_unique` (bar closes at 100%).

**Non-Duplication Evidence** (verified at `d7c6778`):

```text
$ grep -rln "StatsBar" web/src
web/src/pages/JobsWorkspace.tsx
web/src/components/header/StatsBar.tsx
web/src/pages/design-system/HeaderHelpSection.tsx
web/src/pages/design-system/ConnectionStatesSection.tsx
web/src/pages/design-system/ConnectionFeedDemo.tsx

$ grep -rn 'role="meter"\|segmented\|SegmentedBar' web/src -l
(no output: no existing segmented bar or meter component; SegmentedControl is an unrelated tab toggle)
```

**Constraints:** design tokens only (`text-tier-*`, `bg-tier-*`), zero inline hex colors, zero new npm dependencies; PascalCase component filenames; Design System First.

---

## Part 2 — Act

### Phase A — Component in Design System Only (Human approves before live pages)
- [x] RED `stats-bar.test.tsx` (against `variant="summary"`): segment proportions sum to 100%, 4 fixed positions in order `Top/High/Medium/Low`, `"0 Low"` muted, all-zero neutral track without `NaN`, 2px minimum width when `count > 0`, clicking opens legend and **does not** mutate filters, accessible name includes all 4 counts, bar track has `aria-hidden="true"`, skeleton matches loaded height.
- [x] Extract single table of tier labels/order (Scope 4) shared by `TierFilterPills` and `StatsBar`.
- [x] Implement `StatsBar` with `variant="summary"` (default `legacy` untouched so live feed does not change in Phase A). Add all 7 states at `390px` and `1440px` to `/design-system` (`HeaderHelpSection.tsx`).
**Checkpoint:** `npm test -- stats-bar design-system` and `npm run typecheck`. **Human approves in `/design-system` before Phase B.**

### Phase B — Live Feed Wiring & Score Legend Copy
- [x] RED: `JobsWorkspace` renders the new summary; height equality test across skeleton, loaded, and error states (`390px` and `1440px`).
- [x] Wire into `JobsWorkspace.tsx:453-463`, remove `legacy` variant, update `ScoreLegend.tsx` copy via `Writer`, add vocabulary entry in `CLAUDE.md`, update dependent tests, and record `qa-proof.py`.
**Checkpoint:** full `npm test` and `npm run typecheck` green; `/verify-ui` at `375/768/1280/1440`; measure skeleton vs. loaded pixel height in browser.

---

## Part 3 — Quality Checks

- [x] All Quality Checks passed (`qa-proof-front.json` recorded and verified)

---

## Part 4 — QA

### User Stories
- [x] Feed displays total + sort, proportional segmented bar, and 4-tier legend with counts (`390px` stacked in 3 bands, desktop inline).
- [x] Zero-count tier renders as `"0 Low"` muted; all-zero search renders neutral track without error.
- [x] Clicking bar or legend opens score explanation with `"match score ≠ hiring probability"` without changing active filters.
- [x] Changing compatibility filter updates bar and legend; loading skeleton to loaded/error transition shifts page by 0px.

### Acceptance Criteria
- [x] Sum of tiers = total; zero horizontal overflow at `375/768/1440`; visible keyboard focus ring; color is never the sole signal.
- [x] QA passed

---

## Review Feedback — Real Execution Log (6 Rounds, Direct `QA ⇄ Dev` Cord)

### Round 1 (QA, Phase A, 2026-11-19; order `230-QA-A`, commit `88469af`) — Verdict: HOLD
Vitest `stats-bar design-system` (9 files, 88 tests) green. Measured in `/design-system` at `390px` and `1440px` across 7 states. Passes: zero horizontal overflow; segment widths + gaps equal track width (`1440px`: `257.9 + 515.8 + 129 + 55.3 + 6 = 964px`); skeleton height equals loaded height (`390px`: `135px = 135px`; `1440px`: `107px = 107px`).
1. **MEDIUM — `390px` legend overflows on 3-digit counts:** `StatsSummary.tsx:65` (`grid-cols-4 gap-2` + `whitespace-nowrap`). At real feed card width (`358px`), each cell is `77px`, but `"120 Top"` measures `86px` and `"1204 Top"` measures `93px`, bleeding across the 8px gap into the adjacent dot. Reference `13.jpg` stacks the count above the label specifically to prevent this.
2. **MEDIUM — `profileError` increases component height** (violates Scope 6): at `1440px` height jumps `107px -> 119px`; at `390px` height jumps `135px -> 181px`.
3. **LOW/DS — `/design-system` `390px` preview container is `316px` wide instead of feed's `358px`**, causing the sort control to wrap to a second line in the preview.

### Round 2 (QA, Phase A, `f8772d6`) — Verdict: PASS (Forwarded to Manager)
Vitest 90/90 green. Stacked count-over-label holds 4-digit counts (`1204/856/339/130`) inside `77px` cells without overflow (`height: 32px` constant). `profileError` height now matches loaded and skeleton (`390px`: `123px`; `1440px`: `107px`).

### Round 3 (Manager Visual Gate before Human Review, `f8772d6` & `d9a96fa`) — 2 Adjustments
Manager inspected the `390px` and `1440px` screenshots against `CLAUDE.md` UI invariants before showing the human:
1. **Error state had its own height (`76px` vs `107px/123px`):** `CLAUDE.md` invariant (*"replacing loading with content, error, or empty state never shifts the rest of the page"*) overrides legacy error height. Reserve `107px/123px` in `variant="summary"`, use `lucide-triangle-alert` in `text-danger`, and keep the error track static (no loading pulse).
2. **Skeleton used colored tier segments:** A 4-color skeleton looks like real data flashing before load. Changed skeleton track to neutral pulsing grey.

### Round 4 (QA, Phase A, `28d8304`) — Verdict: PASS
Vitest 95/95 green. All 7 states in `/design-system` measure identically (`390px`: `123px`; `1440px`: `107px`), neutral static error track with `triangle-alert` icon, neutral pulsing skeleton. Approved by human in `/design-system`.

### Round 5 (QA, Phase B Live Feed, `c5fe6be`) — Verdict: HOLD (Direct to Dev Front)
Measured on live logged-in feed across `375/390/768/1280/1440px`. Skeleton-to-loaded transition with `/api/stats` delayed 3.5s measured `123px -> 123px` (`390px`) and `107px -> 107px` (`1440px`), `0px` top shift.
1. **MEDIUM (Human decision not met) — Segmented bar track is outside the `<button>`:** Human decision on Open Item 3 specified *"Bar + legend in a single button."* In `StatsSummary.tsx:48-55`, the `<div aria-hidden>` bar was placed outside `<button data-testid="stats-kpi-perfect">`, so clicking the bar track did not open the score explanation dialog.

### Round 6 (QA, Phase B Live Feed, `99ad994`) — Verdict: PASS
Bar track wrapped inside `stats-kpi-perfect` button (`390px`: button width `537px` = track width `537px`; `1440px`: `1087px = 1087px`). Real mouse click on track center opens `"Score Legend"` modal without mutating URL or filters. Full suite: `1,590 passed`, typecheck and lint `0 errors` (order `230-B2`). Part 3 and Part 4 ticked `[x]`.

# Visual Taste & UI Craft Rules

> Baseline visual engineering rules read by the **Designer**, **Dev**, and **QA** roles below the project's own `CLAUDE.md`.

## 1. Hierarchy & Information Architecture

- **One primary action per screen or card:** the user must know within 2 seconds what the screen shows and what the primary action is.
- **Hierarchy through weight, scale, and surface — not borders alone:** never wrap every data group in a bordered box. Group related items by proximity and background surface; use borders only where interactive boundaries require them.
- **Progressive disclosure:** keep secondary metadata, rare filters, and destructive actions out of the primary scan path until requested.

## 2. Typography & Numeric Precision

- **Readable measure:** body copy line length stays between `55ch` and `75ch`.
- **Tabular numbers:** apply `font-variant-numeric: tabular-nums` to all prices, scores, timestamps, counters, and tables so digits align vertically.
- **No orphan truncation:** never truncate critical identifiers or status labels without an accessible reveal; ensure long user-generated strings wrap or ellipsis cleanly without horizontal overflow.

## 3. Interactive States & Perceived Performance

Every data-driven view must design and test all five states:
1. **Loading (Skeleton):** must mirror the real component geometry and reserve final dimensions so transitioning to loaded content or error causes zero Cumulative Layout Shift (CLS).
2. **Empty State:** explain clearly why it is empty and provide a direct action to populate or reset filters.
3. **Populated (Realistic Data):** test with realistic long names, missing optional fields, and 20+ items — never idealized 3-word lorem ipsum.
4. **Error State:** explain what failed in plain user language and offer a retry or recovery action without destroying user input.
5. **Focus / Hover / Active / Disabled:** visible keyboard focus ring (`:focus-visible`), distinct hover feedback, and accessible touch targets (`≥ 44px × 44px` on mobile).

## 4. Mobile-First Responsiveness

- Design and verify at **390px** (mobile viewport) first, then **1440px** (desktop viewport).
- Zero horizontal scroll (`document.documentElement.scrollWidth <= window.innerWidth`) across all supported breakpoints.
- Existing components retain their established polish (radius, shadow, density, tokens) when modified — a preview or PRD must never degrade existing UI craft.

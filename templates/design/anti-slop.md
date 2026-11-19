# Anti-Slop UI Checklist

> Distilled from production frontend design guidelines. Use when choosing visual direction (`design-decide`) and when critiquing UI previews or implementations (`design-port`, `verify-ui`).

## Why This Exists

Language models predict tokens by statistical training distribution. "Safe" choices that work generically without offending anyone dominate web training data. That distributional convergence is the root cause of "AI slop". The countermeasure is not a fixed template — it is **intentionality, domain grounding, and deliberate contrast**.

## Banned by Default (Unless Mandated by Project `CLAUDE.md`)

**Typography**
- ❌ Generic fallback sans-serifs (`Inter`, `Roboto`, `Open Sans`, `Lato`, raw system fonts) used as the primary brand identity font without typographic hierarchy
- ❌ Timid weight pairings (`400` vs `500` vs `600`) that lack visual contrast
- ❌ Timid scale jumps (`1.2x`–`1.5x` between body and display headings)

**Color**
- ❌ Purple-to-indigo gradients over plain white backgrounds (the default AI cliché)
- ❌ Evenly distributed palettes with no dominant surface color
- ❌ Low-contrast pastel badges or text that fail WCAG AA contrast

**Layout, Motion & Surfaces**
- ❌ Cookie-cutter 3-card feature grids with identical icon-title-paragraph blocks on every section
- ❌ Flat, lifeless backgrounds lacking surface hierarchy, subtle borders, or depth
- ❌ Layout shifts when transitioning from loading skeleton to populated content or error state

## Positive Rules (Commitment Over Compromise)

| Dimension | Rule |
|---|---|
| **Typography** | Pair high-contrast voices: display + monospace for technical data, editorial serif + geometric sans, or extreme variable font weights (`200`/`300` vs `700`/`800`). Use decisive scale jumps (`2.5x+` for hero/section headers) and `tabular-nums` on every numeric column or metric. |
| **Color** | Commit to a clear dominant surface (~70%), secondary structure (~20%), and a sharp semantic or brand accent (~10%). Enforce all colors via CSS custom properties / design tokens. Reserve `success`, `warning`, and `danger` strictly for semantic status. |
| **Motion** | Prefer one cohesive, well-orchestrated page-load or state transition (`animation-delay` stagger, CSS transitions) over scattered micro-bounces. Respect `prefers-reduced-motion`. |
| **Surface & Depth** | Layer surfaces intentionally: subtle borders (`1px solid`), elevation shadows, or textured backdrops that separate interactive cards from the canvas. |
| **Layout & Density** | Choose either generous editorial negative space or high-signal functional density — never an undecided middle ground. Maintain mobile-first ergonomics (390px → 1440px, touch targets ≥ 44px). |

## Critique Gate — Rejection Questions

1. Would this font and color pairing appear in a generic "AI landing page generator" template? → **Reject.**
2. Does the palette have an unmistakable dominant surface, or is every color competing at equal weight? → **If equal, reject.**
3. Do loading skeletons match the exact structure and height of the populated cards (zero layout shift)? → **If they jump, reject.**
4. Are all four states (empty, loading, error, populated with realistic data) designed with the same craft? → **If any state is missing, reject.**
5. Does the visual complexity match the product's domain (e.g., high-signal scannability for dashboards/tools vs expressive storytelling for editorial pages)? → **If mismatched, reject.**

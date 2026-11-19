---
name: design-decide
description: Decide the visual direction of a landing page from 3 user-chosen reference URLs. Captures screenshots of the references, finds ~5 candidates in their visual family, filters them through kill rules, ranks survivors without numeric scores, and returns 1 recommended direction + 2 distinct alternatives with annotated screenshots. Use when the user asks to decide a landing page direction, choose among visual references, or run design-decide. Does NOT invent layouts, generate design systems, or write production code (implementation follows via design-port).
---

# Design Decide (V0)

AI does not invent visual direction from thin air. It **selects** among real, screenshot-verified pages within the visual family declared by the user.
The goal is to reduce the user's decision load: at the end, 3 distinct options remain, not 10.

## Mandatory Inputs (if any is missing, stop and ask)

1. Product summary (1 sentence) and target audience.
2. **Single primary goal** of the page (V0 default: waitlist / email capture).
3. **3 reference URLs chosen by the user**, each with 1 sentence stating what they like about it. This defines the taste profile for *this* page.
4. Constraints: theme (dark/light), path to existing design-system tokens, and explicit anti-goals.
5. Visual metaphor (optional). It always enters **on trial**: the skill may conclude the page works better without it.

## Workflow

1. **Taste profile.** Capture screenshots of the 3 references at 390 and 1440 viewports and extract 4–6 *observable* structural traits, never vague adjectives.
   Good: "hero with a single CTA and live product preview immediately below the fold". Bad: "modern and clean".
2. **In-family search.** Find ~5 candidate pages matching **at least 3 traits** from the taste profile. Broad, unconstrained search is forbidden.
   Allowed sources: Land-book, Lapa Ninja, SaaSpo, Godly; open-source templates (`gh search repos`, Vercel templates);
   local reference library (`design/references/websites/` if present). Dribbble and Behance are **excluded**: they are isolated shots, not live pages.
   **Gallery browsing via the user's real browser session.** SaaSpo, Lapa Ninja, and Land-book block headless browsers with Cloudflare challenges
   (verified 2026-10-16). Browse gallery listings through a connected user browser session when available.
   - **Challenge or CAPTCHA:** stop immediately and ask the user to solve it in their browser. Never attempt to solve or bypass a CAPTCHA.
   - **Browser extension disconnected or user unavailable:** proceed using known live pages plus local references, and record this under "Limitations of this round".
   - **No cookie extraction:** never copy cookies (`cf_clearance` included) from the user's browser into Playwright.
   - **Screenshots:** the connected browser is only for *discovering* candidate URLs. Capture screenshots in Steps 1–2 via Playwright or the preview browser against the target URLs directly.
   **No candidate enters without a viewed screenshot at both 390 and 1440.** Page titles or text descriptions never count as proof.
3. **Kill pass.** Apply the kill rules below to the 3 user references and the 5 candidates, recording 1 line per eliminated page.
4. **Pairwise ranking.** Compare survivors side by side, stating in 1 sentence why A ranks above B. **No 1–5 numeric scores and no summed totals.**
   Tie-breaker order: fit to page goal → low distraction → visual hierarchy → fit with existing design-system tokens → implementation feasibility → `templates/design/taste-rules.md` (active rules) → originality without usability cost.
5. **Selection.** Output 1 recommended direction and 2 alternatives that are **genuinely distinct from one another**. If two candidates look similar, keep the stronger one and move the other to the eliminated table with the reason. Never say "all of them are great". Never output more than 3 options.
6. **User gate.** Present a single `AskUserQuestion` with the 3 options (the recommended option first, marked `(Recommended)`). If the user requests a new search via "Other",
   record the reason in the output file as a **round failure** and stop: do not re-run the search autonomously.
   If the user's approval or veto reveals a generalizable preference that applies across pages, ask whether to codify it as a rule in `templates/design/taste-rules.md`.

## Kill Rules (V0, waitlist)

| Rule | Dies when |
|---|---|
| Single CTA above the fold | The email input (or single primary CTA) is not visible above the fold in the 390px screenshot. |
| Value proposition in 5s | H1 + subheadline fail to explain what the product does without scrolling. Poetic headlines die here. |
| Metaphor dominates product | The visual metaphor takes over the hero (full-screen globe, HUD, decorative illustration) instead of acting as subtle seasoning. |

`templates/design/taste-rules.md` and `templates/design/anti-slop.md` **never trigger an instant kill**: they weigh in pairwise ranking and populate the "Do not steal" column.

## Output

Write `planning/<project>/notes/<YYYY-MM-DD>-design-decide.md`, storing captured screenshots under
`planning/<project>/notes/design-decide-<YYYY-MM-DD>/<slug>-{390,1440}.png`:

```markdown
# Visual Direction — <page> (<date>)
Goal: <...> · User references: <3 URLs>

## Recommended — <name> (<url>)
![1440](...) ![390](...)
**Why:** 2 lines max.
**Steal:** composition, pacing, density, product preview treatment, hero structure.
**Do not steal:** brand palette, <X>, <Y> (cite the specific rule from `templates/design/taste-rules.md` or `templates/design/anti-slop.md` when applicable).
**Metaphor:** included as <concrete subtle accent> | excluded because <...>.

## Alternative 1 — <name>   (same format + "Choose this if ...")
## Alternative 2 — <name>

## Eliminated
| Candidate | Killed by |

## Taste Profile Used
- 4–6 observable traits
```

## Out of V0 Scope

Code implementation, rendered hero prototypes, design-system token generation, kill rules for non-waitlist goals, cross-project taste inference without explicit user confirmation, and post-implementation visual QA (use `design-port` for that).

## Harness portability

- **Screenshots:** in Claude Code use the built-in browser tools or Playwright; on the Maestri canvas use `maestri portal` resized to 390×844 and 1440×900; in Codex and Antigravity run `npx playwright screenshot --viewport-size=390,844 --full-page <url> <out>.png` (and `1440,900`). Always inspect the captured image file before judging a candidate.
- **User gate:** `AskUserQuestion` is Claude Code-specific. In other harnesses, ask a numbered plain-text question with lettered options, marking the recommended choice first and leaving an open option.
- **Web search:** use the harness's native web search tool (`WebSearch` / `search_web`) and `gh` CLI for repository search.
- **Galleries behind bot challenges:** if a live user browser integration is unavailable in the current harness, ask the user to paste 3–5 candidate URLs from the gallery or proceed with accessible live sites and note the limitation.
- **Scroll-triggered empty sections:** full-page screenshots often capture blank whitespace where scroll-triggered animations have not fired. Note this in the round's limitations and judge below-the-fold structure from visible section headings.

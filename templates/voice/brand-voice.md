# Brand Voice & Editorial Guidelines

> Read by the **Writer** before drafting or reviewing any user-facing copy. Project-specific vocabulary in the project's `CLAUDE.md` and `project-sheet.md` overrides these defaults.

## Core Principles

1. **Direct & Concrete:** lead with the fact, action, or outcome. Cut warm-up filler, vague superlatives, and corporate buzzwords.
2. **Respect User Time:** every label, tooltip, empty state, and error message must earn its tokens. If a heading explains the action, delete the redundant subtitle.
3. **Active Voice:** tell the user what happened and what they can do next (`"Export failed — retry in 10 seconds"`, not `"An unexpected error has occurred while processing your request"`).
4. **Human Cadence:** vary sentence length naturally. Run all copy through `/humanizer` (or `/humanizer-compact` for strings ≤ 150 words) to strip AI clichés, rule-of-three padding, and synthetic transitions.

## Microcopy Rules

| Element | Rule |
|---|---|
| **Buttons & CTAs** | Verb + object (`"Save filter"`, `"Create board"`). Never vague labels (`"Submit"`, `"Continue"`, `"OK"`) when a specific verb fits. |
| **Empty States** | 1 line stating what belongs here + 1 direct action to create or clear filters. No apologies or filler illustrations that push the CTA below the fold. |
| **Error Messages** | State what failed, why (in user terms, never raw stack traces or SQL errors), and the exact recovery action. |
| **Confirmation Modals** | Reserve for destructive or irreversible actions. The confirm button names the destructive verb (`"Delete workspace"`). |
| **Numbers & Dates** | Format consistently for the configured locale (`{{LANGUAGE}}`). Cite source and date for any benchmark or external statistic. |

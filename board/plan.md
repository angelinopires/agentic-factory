# 1-Page Plan Template

Created before any PRD that originates from a new product idea. File path: `{{PLANNING_DIR}}/notes/<date>-<slug>-plan.md`.
The Manager assembles this plan with the product team (Explorer, Designer, Writer); the user approves it; the Explorer authors the PRD from it.

```markdown
# <Title> — 1-Page Plan
**Status:** draft | approved by user on <YYYY-MM-DD>

## Problem
<What hurts, for whom, backed by a concrete metric or observation>

## Target Audience
<Primary audience; which other segments, flows, or screens benefit from the same work>

## What the System Already Has (Explorer)
| Component / Module | file:line | How It Is Reused Here |
|---|---|---|

## How It Looks & Works (Designer)
2–3 options (static HTML in `{{PLANNING_DIR}}/design/<slug>/` if UI is affected). Chosen option: <option>. User selection approves the screen spec.

## Out of Scope
- <Explicitly excluded items>

## Size & Rework Risk
Simple (S) | Complex (C), and what assumption, if wrong, would force a rewrite
```

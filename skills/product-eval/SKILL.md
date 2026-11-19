---
name: product-eval
description: Evaluate a running product as a user would, anchor every critique to file:line, lock product decisions with the user, then produce an epic with dependency graph and PRD queue. Use when the user asks to evaluate, critique or improve a front-end, a feature set or the product experience, or asks what is missing before launch or beta.
---

# /product-eval

Product evaluation that ends in an executable plan. It starts on the live screen, not in the source code.

**This is not `/ui-ux-analysis`** — that skill audits accessibility, design tokens, and Core Web Vitals
against a technical standard. This skill asks whether the product **delivers on its promise** and what
is missing before the next milestone (beta, public launch, first real user cohort).

## The contract

Every critique must include three parts or it does not enter the report:

1. **What the user sees** — described from the user's perspective, not the developer's.
2. **Where it originates** — `file:line`. A critique without a code anchor turns into a taste debate.
3. **Why it matters for this product** — tied to the product's core differentiator, not generic
   best practices.

## Steps

### 1. Run the product

Boot the application and navigate it for real — browser, breakpoints, end-to-end user flows. Read the
source code afterward to explain what the screen showed.

Order matters: starting from the code finds code problems. Starting from the screen finds product
problems, which is why this skill exists.

### 2. Find where the product lies

The highest-value bucket, and the one nobody finds by reading isolated source files:

- A field rendering a hardcoded string where it should display live data.
- The same entity showing two different values in two places (list card says one thing, detail modal says another).
- Missing data rendered as a concrete value (`null` turning into `On-site`).
- A filter whose UI option labels do not match the stored token vocabulary — the option exists and always returns zero results.
- An aggregate counter computed over the wrong set (showing the pre-filter total after a filter is applied).

Each of these destroys user trust faster than any layout bug, and none of them is caught by a type checker.

### 3. Ask for the core differentiator — and check whether it is visible

Ask the user one question: **what does this product do that alternatives do not?**

Then look for that exact capability in the interface. The recurring pattern: the differentiator is
implemented in the backend and invisible on screen, while prime screen real estate goes to commodities
every competitor already shows. That is usually Finding #1 of the evaluation.

### 4. Lock product decisions BEFORE writing any PRD

Use `AskUserQuestion` (never assumptions). Surface the real forks in the road (authentication model,
access gate, what is public vs. gated, what can wait until after launch) and present them as named options.

Record every decision **along with its explicit consequence**:

> "Passwordless magic link. **Therefore, there is no password-reset PRD in this roadmap.**"
> "Closed beta via allowlist invite. **Therefore, the public marketing home page leaves the critical path.**"

Stating the consequence prevents the next session from scoping work that the decision already eliminated.

### 5. Write the epic

Produce a single epic document with these sections in this exact order:

- **Objective** and **success bar** — one falsifiable sentence ("user feedback discusses product fit, not broken flows").
- **Why now** — anchored in `file:line`, not narrative prose.
- **Consolidated decisions** with their explicit consequences (from Step 4).
- **Explicitly out of scope.** A named list. Negative scope prevents more rework than positive scope.
- **Execution graph** — ASCII dependency graph showing what runs in series and what can run in parallel.
- **PRD table** with complexity, dependencies, and status.
- **Quality gates per wave.** No gate may ever be "the code runs". Every gate is an observable user
  behavior or a `grep` returning zero matches:
  > `grep -rn 'get_by_label("default_user")' server/api/` returns zero lines.
  > Two distinct signed-in emails see distinct data sets without code changes.

### 6. Write the PRDs and close out

- One PRD per verifiable deliverable, authored via `/prd`. Must fit in a single execution session:
  ≤3 phases, ≤200 lines, explicit checkpoint command per phase.
- If an existing PRD is superseded by this epic: add `Superseded by:` to the old PRD's header, move it
  to `archive/`, and update **all** references to it immediately.
- Register the new queue in `planning/<project>/progress.md`.
- **Run `/verify-claims`** across the epic and every newly created PRD. That is where invented frontend
  paths and non-existent CLI flags get caught.

## Rules

- **Start from the screen.** Reading code before navigating inverts what the skill discovers.
- **Every critique requires `file:line`.** Without an anchor, it is just an opinion.
- **Product decisions belong to the user**, gathered via `AskUserQuestion` with named options and an
  open option. Never decide on the user's behalf and build a PRD queue on top of a guess.
- **Record the consequence of every decision**, not just the choice itself.
- **A quality gate is never "the code runs".**
- **Negative scope is mandatory.** Name what is excluded.
- **Run `/verify-claims` before delivery.** No exceptions.
- Never implement code during the evaluation. The deliverable is the verified plan.

## Harness portability

- **Browser navigation:** use `preview_*` tools in Claude Code, `maestri portal` on the Maestri canvas,
  or Playwright / browser sub-agent in Codex and Antigravity.
- **User decisions:** use `AskUserQuestion` in Claude Code, `request_user_input_async` in Codex, or
  numbered plain-text questions with lettered options and an open option when no structured question
  tool is available.

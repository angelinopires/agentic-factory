---
name: verify-ui
description: Verify UI at mobile/tablet/desktop breakpoints using preview tools. Screenshots first, DOM inspection fallback if screenshots fail. Produces a pass/fail report per breakpoint.
---

# /verify-ui

Visually verify a route at three standard breakpoints. Always attempts screenshots first; falls back to DOM/snapshot inspection if screenshots fail or content is cut off.

## Usage

```bash
/verify-ui [url]
```

If no URL is provided, ask the user which route to verify.

## Steps

### 1. Ensure a preview server is running

- Call `preview_list` to check for running servers.
- If none: call `preview_start` using the project's launch config.
- If one is running, proceed.

### 2. Reload the page

- Reload the page (JS eval `window.location.reload()`) to ensure fresh state.
- Navigate to the target URL if different from current.

### 3. Check for console errors

- Read the console messages — note any errors or warnings. Flag hydration errors as blocking.

### 4. Verify at each breakpoint — run all three

#### Mobile — 375px

- Resize the viewport to 375px wide
- Screenshot → inspect visually
- If screenshot fails or content is cut off: read the accessibility tree for structure + JS eval `getComputedStyle` for CSS values
- Check: no overflow, no broken layout, touch targets visible

#### Tablet — 768px

- Resize the viewport to 768px wide
- Screenshot → inspect visually
- Fallback: accessibility tree + computed styles
- Check: layout adapts correctly, no orphaned elements

#### Desktop — 1280px

- Resize the viewport to 1280px wide
- Screenshot → inspect visually
- Fallback: accessibility tree + computed styles
- Check: full layout renders, no excessive whitespace or clipping

### 5. Produce a report

Output a concise markdown table:

| Breakpoint     | Method         | Status            | Notes       |
| -------------- | -------------- | ----------------- | ----------- |
| 375px mobile   | screenshot/DOM | ✅ Pass / ❌ Fail | Issues here |
| 768px tablet   | screenshot/DOM | ✅ Pass / ❌ Fail | Issues here |
| 1280px desktop | screenshot/DOM | ✅ Pass / ❌ Fail | Issues here |

Below the table:

- List any console errors found
- List any layout issues with enough detail to fix them
- Overall verdict: **All clear** or **Issues found — fix before shipping**

## Harness portability

The `preview_*` tools exist only in Claude Code. In other harnesses:

- **Maestri Canvas (`maestri portal`):** use `maestri portal create`, `resize`, `screenshot`, `snapshot`, and `logs` at 375×812, 768×1024, and 1280×800.
- **Project has Playwright** (`playwright.config.*`): write or run a spec that visits each route at
  375×812, 768×1024 and 1280×800, asserts no horizontal overflow
  (`document.documentElement.scrollWidth <= innerWidth`), captures `page.on('console')`
  errors, and saves a screenshot per breakpoint. Same report table, method `playwright`.
- **No browser tool or Playwright:** do not mark any breakpoint as passing. Report "visual verification pending — run `/verify-ui` in a browser-capable harness" and treat it as a failing result.

## Fallback Rules

- Screenshot fails → switch to the accessibility tree + computed styles for that breakpoint. Do not skip verification.
- Scrolled content cut off → scroll to the section via JS eval, then screenshot again. If still failing, use DOM inspection.
- Server not responding → report the blocker and stop. Do not mark as passing.

## Rules

- Never mark a breakpoint as passing without actually verifying it (screenshot OR DOM — not assumed).
- Always check console logs — a visually clean page with hydration errors is a failing page.
- Reset to 1280px after verification is complete.

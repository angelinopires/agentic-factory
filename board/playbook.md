# Board Playbook

Operational procedures. Read the relevant section when executing. Role assembly and recruitment live in `README.md`.

## User Delivery (Manager)

Present in product language (`{{LANGUAGE}}`), free of internal jargon:

```markdown
## <PRD> <product title>
**The problem:** <as experienced by the user, with metric>
| Before | After |   ← 2-4 rows of visible behavior change
**How to verify:** browser steps (verified URL + what to inspect + expected outcome). Headless/backend: "no UI change" + 1 command.
**Screen deviations:** <list or "none">
**Out of scope:** <items>
**Your action:** <OK to merge; git push is yours>
```

Before presenting, the Manager inspects end-to-end QA screenshots against the approved plan. User OK is final acceptance, not primary QA.

## PRD Review with the User (Manager)

Per PRD, present 4 fields: **what changes · why · final outcome · autonomous Manager decisions** (`M#`). Use a table for batches (up to 4 PRDs per confirmation gate). Record every user decision in the active epic immediately.

## Board Startup (`/canvas-manager`)

Run `maestri check` on every product and engineering terminal. When no PRD is in progress, run `recruit --replace` on terminals holding stale context. When a PRD is in progress, reset only idle terminals. Never restart an empty session. Flush any pending `REPORT` or design option to disk before running `role write` or `recruit --replace`.

## Recruit & Reset (Manager)

- **Reset:** re-run the terminal's recruit command from `README.md` / `recruit.sh` with `--replace "<Name>"` (never send `--raw "/clear"`, which opens a blank session in Codex and swallows the next `ask`). Run `maestri check` before and wait until ready before sending `ask`.
- **Connections:** after recruiting, run `maestri connect "QA" "Dev Front"` / `maestri connect "QA" "Dev Back"` (or `"Dev"`).
- **`maestri role write`:** restarts the terminal immediately — run only when idle. If a terminal at the context ceiling fails to restart, use `recruit --replace`.

## Quota & Provider Fallbacks

Quota exhaustion never halts a sprint or escalates to the user: switch to the fallback configured in `board.config.json` / `README.md` and log the swap.

Live Codex rate-limit check (`primary` = 5h window, `secondary` = weekly window):

```bash
(printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"q","version":"0"}}}' '{"jsonrpc":"2.0","method":"initialized"}' '{"jsonrpc":"2.0","id":2,"method":"account/rateLimits/read"}'; sleep 6) | codex app-server 2>/dev/null | grep '"id":2'
```

- **Mid-PRD fallback:** `recruit --replace` the Dev terminal with the fallback provider; note `"Dev on fallback provider since <timestamp>"` in the PRD so QA runs cross-family review before merge.
- **Between PRDs:** schedule `maestri routine create "resume-<id>" --terminal "<Name>" --command "<order>" --once "<reset_time + 5m>"`.

## Manager Context Reset

Check context via `{{WORKSPACE_ROOT}}/scripts/manager-context.sh <session-id>`. Reset at PRD boundaries, between 180k–200k tokens, or when quota drops below 10%:

0. Confirm zero background `ask` calls or open ORDERs without a REPORT (resetting early loses in-flight REPORTs).
1. Write next steps and open questions to `{{PLANNING_DIR}}/runs/<date>-<PRD>.md`.
2. Schedule `maestri routine create "manager-clear" --command "/clear" --once "<T>"` and `maestri routine create "manager-resume" --command "/canvas-manager {{PROJECT_NAME}} resume <path>" --once "<T+1m>"`.
3. End turn immediately.

## Blind Dual Research & Verification

For research deciding an epic, golden set, or final audit: dispatch two distinct models with the identical on-disk brief without reading each other. The Manager cross-checks: agreement holds; divergence goes to Explorer (full codebase verification); remaining trade-offs go to the user.

## PRD Closure (Manager Dispatches)

Manager merges to `main` and user pushes → CI and Deploy turn green (`gh run list`) → Rollout verifies post-deploy (if required by PRD) → ORDER to Explorer: `/prd-ship` + commit `{{PLANNING_DIR}}` → reset participating terminals → reset Manager. Delete merged branch `prd/<n>` via `git branch -d`. `/prd-ship` requires Part 3 and Part 4 ticked `[x]` with evidence by QA prior to PASS. On closure, verify `docker ps -a --filter status=exited` for leaked test containers (leaked containers are test bugs requiring a Dev ORDER).

## No Recurring Watchdog Routines

Never create recurring polling routines (e.g., every 10 minutes) against agent terminals. Recover lost REPORTs by inspecting on-disk commits and `runs/<prd>/` via `order.py reconcile`. Disable any recurring routines before ending the session.

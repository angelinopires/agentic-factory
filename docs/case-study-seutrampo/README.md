# Production Case Study: Building SeuTrampo AI with a Single-Board Agentic Factory

I built **SeuTrampo AI** (a remote job matching and career intelligence platform for Brazilian engineers, with a React/TypeScript frontend in `web/`, a Python/FastAPI backend in `server/`, and PostgreSQL + Docker in production) as a solo developer operating a Maestri board.

Over 230+ PRDs and 30+ recorded session retrospectives, I threw away three different multi-agent architectures before landing on the setup in this repository. Every script in `scripts/`, every hook in `hooks/`, and every one-line rule in `board/*.md` exists because an agent broke something in production or burned my token quota at 2 a.m.

This directory holds the sanitized evidence from that system:

- [**`cases.md`**](./cases.md): All 12 real war stories from November 2026, translated to English, mapping each operational failure to the exact rule or script that fixed it permanently.
- [**`sample-prd.md`**](./sample-prd.md): A real production PRD (`#230 Search Summary Bar`) showing delta-only overviews, non-duplication grep evidence, Design System First execution, and 6 rounds of QA measurements.
- [**`sample-retro.md`**](./sample-retro.md): A real `/canvas-retro` Kaizen session showing how rules are evaluated, pruned under a net-zero line budget, and synced back to Maestri terminals.

---

## 1. Killing the Middlemen: Why I Fired the Orchestrator, Planner, and Scribe

My early Maestri setup looked like an org chart. I had separate Design and Engineering boards, a Manager, an Orchestrator between the Manager and the devs, a Planner that only wrote specs, and a Scribe that only committed planning files.

It looked great on a canvas and failed in practice:

1. **Telephone-game distortion:** Every hop between Manager, Orchestrator, and Dev lost constraints. On November 4, 2026, I asked to plan a launch milestone. While we were still talking, the Manager sent an order to the Orchestrator, which spun up `Dev Back`, `Dev Front`, and `Designer` and wrote a brand-new PRD (`#195`) duplicating work already covered by `#191`.
2. **Stalled watcher loops:** I had a recurring cron routine (`orq-check`, every 10 minutes) polling the Orchestrator. On the night of November 9 to 10, the Orchestrator hit its context ceiling and stalled. The cron fired **105 times overnight** against a dead terminal.
3. **Bottlenecked QA handoffs:** Routing every minor CSS or test fix from `QA` back through an Orchestrator or Manager burned context on three terminals for a two-line change.

Between November 3 and November 18, 2026, I simplified the board in three steps:

- **One workspace, one leader (Nov 3 & Nov 10):** I deleted the separate boards and fired the Orchestrator, Planner, and Scribe. The **Manager** (`Claude Opus 5.5` in Maestro mode) became the single leader connected directly to every worker terminal. `Explorer` writes and closes PRDs in `planning/`; `Dev Front` and `Dev Back` commit code on `prd/<n>` branches.
- **Direct `QA ⇄ Dev` HOLD cord (Nov 18):** I wired `QA` directly to `Dev Front` and `Dev Back` (`maestri connect "QA" "Dev Front"`). When QA finds a bug (`HOLD`), it messages the Dev directly. The Manager stays out of the loop and only wakes up on `PASS`, when a product decision is needed, on a 3rd failed round, or if a terminal hits the 200k token ceiling.
- **Blind dual research & second opinion (Nov 15–19):** When a task requires classifying ambiguous data or making an architectural trade-off, two different model families (`AGY Gemini 4` and `Codex GPT-6.1 Sol`) run the same on-disk brief blind, without reading each other. On PRD `#222b`, Claude found 34 executive job candidates and Codex found 40, with an intersection of only **3**. A single model would have missed half the dataset.

---

## 2. Stopping the 960k-Token Runaway (`context-ceiling.py` & `prd-cost.py`)

On October 11, 2026, my Quality terminal ran 6 blind-labeling batches in a single continuous session. Nobody reset the terminal between batches. Its context snowballed to **960,000 tokens**, taking my 5-hour Claude usage window from 70% to 100% in one sitting.

When I audited 30 days of JSONL session transcripts across 160 sessions on November 16, the numbers were clear:

- **First-turn baseline:** ~46k to 70k tokens (`input + cache_creation + cache_read`).
- **Role terminals with per-phase resets:** Median peak of **120k to 145k tokens**.
- **Unconstrained Manager sessions:** Median **186k**, p90 **254k**, max **364k**, with **69 out of 160 sessions** crossing 200k tokens.

I fixed this with two deterministic tools:

### `hooks/context-ceiling.py`
A `PreToolUse` hook that inspects the tail of the active session's JSONL transcript before every tool execution:
- At **170k tokens** (`ceiling - 30k warn_margin`), it injects a one-time warning telling the agent to finish its current step, write state to `runs/<prd>/`, and ask for a reset.
- At **200k tokens**, it returns a hard `permissionDecision: "deny"` on all tools except three safe exit paths:
  1. `maestri ask` (to report status),
  2. `python3 scripts/order.py report` (un-chained), and
  3. `Write` or `Edit` inside `planning/<project>/runs/` so the agent never loses its final report to the ceiling (fixing the November 11 incident where a 207k-token QA report had to be salvaged manually from raw `.jsonl` logs).

### `scripts/prd-cost.py`
Because Claude Code and Codex run on flat subscriptions with rolling 5-hour and weekly quota windows, you only notice token waste when a window locks up mid-sprint. `prd-cost.py` parses `ORDER` and `REPORT` markers across `~/.claude/projects/*/*.jsonl` and `~/.codex/sessions/**/*.jsonl`, attributes every session to a specific PRD without double-counting cumulative Codex token events, and outputs:
- API-equivalent USD cost (attributed vs. shared sessions),
- Total attempts and retries per `ORDER`,
- QA rounds, and
- Number of times the human had to be interrupted via `AskUserQuestion`.

---

## 3. Why Prompts Rot (and How Word Budgets + Net-Zero Kaizen Fix It)

When an agent makes a mistake, the natural impulse is to add a paragraph to its system prompt. If you do that for three weeks, your `CLAUDE.md` balloons to 4,000 words, agents start ignoring half the rules, and every turn pays a massive cache-read tax.

In this factory, role prompts live under a hard physical ceiling enforced by `python3 scripts/compile-board.py --check-budgets`:

| Layer | File | Hard Budget | Purpose |
| --- | --- | --- | --- |
| Shared Kernel | `board/core.md` | **<= 500 words** | Team topology, `ORDER`/`REPORT` contract, `order.py` ledger, safety boundaries |
| Role Prompt | `board/{manager,explorer,designer,writer,dev,qa,rollout}.md` | **<= 400 words each** | Only the invariants specific to that terminal |
| On-Demand Manuals | `board/{playbook,qa-manual,rollout-manual,map,plan}.md` | Read by section when needed | Operational procedures so idle turns stay lean |
| Incident Ledger | `docs/case-study-seutrampo/cases.md` | Manager reference only | Full war stories behind the one-line dated rules |

At the end of every work cycle, running `/canvas-retro` enforces **net-zero line balance (`line balance <= 0`)** on core files. To add a new rule to `core.md` or `manager.md`, you must delete or merge an older rule that has either become an automated script or a settled habit. The long story goes into `cases.md`; the role prompt only keeps one line and the date (for example, `(16/11)`).

---

## 4. Cryptographic Governance Instead of "Please Follow the Rules"

Three incidents taught me that markdown instructions cannot enforce state transitions on their own:

1. **Unauthorized or premature dispatch (`scripts/order.py`):** After the Manager launched a midnight sprint at 19:40 on November 16, I moved `ORDER` and `REPORT` tracking to disk (`runs/<prd>/order-<id>.md`). The Manager cannot open an order unless `--authorization` matches an exact quoted string (`>= 15` chars) from `runs/<prd>/authorization.md` containing the human's dated words. Every state transition (`open` -> `start` -> `report`) is sealed with a SHA-256 digest and serialized with `fcntl.flock` so parallel reports never drop external side effects (`commit`, `deploy`, `migration`).
2. **Empty-tree hash collisions (`scripts/qa-proof.py`):** Previously, QA verified that the working tree matched Part 3 by hashing `git diff HEAD` plus untracked files. On PRD `#209`, we realized that *any* clean git tree produces the exact same SHA-256 of an empty string, even if the branch or commit changed. `qa-proof.py` binds the test result (`exit_code: 0`) to a canonical SHA-256 identity of `commit + tree + merge-base + dirty_sha256 + command + tracked lockfile blobs`. QA runs `qa-proof.py verify` in 50ms instead of re-running a 3-minute test suite.
3. **Production safety (`hooks/prod-guard.py` & `hooks/pre-tool-use.js`):** Agents never run `git push`, `git commit --amend`, `--no-verify`, `docker compose down`, or direct SQL against production markers. And when a security hook itself is modified (like our November 16 heredoc parser fix in `prod-guard.py`), an independent QA terminal tests the hook for bypass regressions before it can be committed.

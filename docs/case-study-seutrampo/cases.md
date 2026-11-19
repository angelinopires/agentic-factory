# Board Incident Ledger (`cases.md`)

Long-form production incidents from building **SeuTrampo AI** that justify the rules and scripts in this repository. In the live board prompts (`board/*.md`), each rule stays under a strict word budget with a one-line summary and date; the full war story lives here so the Manager understands *why* the boundary exists.

---

## 1. 2026-11-04 — Manager Dispatched Execution During Planning (`board/manager.md`, Flow 1)

- **What happened:** The human asked to plan the launch milestone. After every answer in the planning conversation, the Manager immediately fired execution orders. The (now-retired) Orchestrator put `Dev Back`, `Dev Front`, and `Designer` to work and authored a new PRD (`#195`) for scope that PRD `#191` already covered. The human had to halt the entire board.
- **Cost:** Wasted parallel token burn across 4 terminals and a duplicate PRD.
- **Permanent fix:** Planning and execution are strictly separated. An idea goes through `/grill-me` and closes in a 1-page plan (`plan.md`) approved by the human before any PRD or Dev order is opened. Furthermore, `scripts/order.py open` now requires an explicit, timestamped human quote in `runs/<prd>/authorization.md`.

---

## 2. 2026-11-04 — Scheduled Sprint Halted at Start by Quota Threshold and Questions (`skills/canvas-sprint`, `board/playbook.md`)

- **What happened:** `/canvas-sprint launch #184 #163` triggered with weekly Codex usage at 83%. The old skill rule said `>= 80% -> do not start`. The Manager stopped the sprint, asked the human about the quota, and then asked a follow-up question about an OpenGraph number. The human came back expecting the sprint ready for review and found zero progress.
- **Cost:** Full overnight sprint window lost waiting on human input.
- **Permanent fix:** Quota exhaustion never halts a sprint or turns into a question for the human (`board/playbook.md`). When a primary harness hits its quota limit, the Manager automatically switches the worker terminal to its configured fallback harness (`maestri recruit --replace`), logs the switch in `decisions.md`, and keeps moving. All clarifying questions must be settled *before* scheduling a sprint routine.

---

## 3. 2026-11-05 — Two-File CSS Bug Turned Into a 108-Line PRD (`#197`, `board/core.md`)

- **What happened:** During local testing of `#195`, the human noticed a toast notification rendering behind a modal backdrop blur (tied `z-50`). The Manager ordered a "small PRD," which produced a discovery note, a 108-line PRD, a readiness gate, and a question about keyboard navigation. The human asked: *"Why write a PRD for such a simple change? That just burns tokens."* Right after, two landing-page copy and loading tweaks were dispatched as direct orders with end-to-end QA and shipped cleanly.
- **Cost:** ~150k tokens of specification overhead for a two-line z-index fix.
- **Permanent fix:** Added the fast-path rule in `board/core.md` (`## Flow`): *"1–2 file bug with zero product decisions: direct ORDER to Dev + end-to-end QA, no `plan.md` and no PRD."*

---

## 4. 2026-11-07 — PRD `#198` Built, Passed QA, and Thrown Away (`board/plan.md`, `board/manager.md`)

- **What happened:** The Manager ran discovery alone and only inspected the single component card mentioned in chat. Version 1 (a custom query and standalone card) was built and passed QA. When the human reviewed it, he asked for a chart and segment filter, pointing out that the Admin People view *already had* the base query, segment filter, and `BarCategoryChart`. Version 1 was discarded completely.
- **Cost:** Full Dev + QA cycle thrown away because existing components were not mapped first.
- **Permanent fix:** Before any PRD is written, the Manager dispatches `Explorer` (to inventory what the codebase already has with `file:line` evidence) and `Designer` (to produce 2–3 static HTML options when UI changes), converging on a 1-page `plan.md` approved by the human.

---

## 5. 2026-11-08 — Manager Unilaterally Approved Deviations from Human Decisions (`#198`, `board/manager.md` §2)

- **What happened:** On the v1 readiness gate (Nov 7), the Manager approved the spec without checking existing codebase components. On the v2 gate (Nov 8), the Manager unilaterally approved three deviations from the human's locked decisions: excluding Landing events from the People CTE, splitting Guests into two steps, and substituting `SegmentedControl` for `PillFilter`. The human only found out because the Manager mentioned them after the fact.
- **Cost:** Erosion of decision trust and spec rework.
- **Permanent fix:** Rule in `board/manager.md` §2: *"Any deviation from a locked human decision must escalate to the human before the PRD is marked `Ready`."*

---

## 6. 2026-11-08 — Wireframe Grey Bars Shipped as Final UI Colors (`#198`, `board/designer.md`)

- **What happened:** Options A and B in the static HTML design preview used neutral wireframe grey bars to illustrate layout hierarchy. Option A was approved and implemented literally by `Dev Front`. After QA, the human noted: *"The chart colors are way too basic... just because the designer used wireframe greys to show layout does not mean the final product should ship with wireframe colors."*
- **Cost:** An extra color study, a `Dev Front` rebuild round, a full QA pass, and a re-recorded demo.
- **Permanent fix:** Rule in `board/designer.md` and `templates/design/anti-slop.md`: static HTML previews must use the project's actual semantic color tokens (`--color-tier-*`, brand palette) rather than placeholder wireframe greys.

---

## 7. 2026-11-10 & 2026-11-19 — Autocomplete Ghost Text in Subordinate Terminals Misread as Human Input (`board/manager.md`)

- **What happened:** On November 10, three times the Manager inspected a subordinate terminal via `maestri check`, saw unsubmitted text sitting in the input line (*"Send HOLD to Dev Back"*, *"Return to QA"*, *"REPORT sent to Manager"*), and told the human that someone was typing manually into the worker terminals. The human replied: *"I am not typing anything."* On November 19, the Manager saw grey text (*"run check-ats on both samples"*) in the QA terminal input, claimed a duplicate session was attached, and had the human close a window, only for the text to reappear after `maestri recruit --replace`. Both were Claude Code's automatic next-prompt ghost suggestions.
- **Cost:** Unnecessary alarm and interrupted sessions.
- **Permanent fix:** Unsubmitted text sitting at the prompt line of a Claude Code terminal is autocomplete ghost text, never a human command or evidence of a second attached session.

---

## 8. 2026-11-11 — QA Report Trapped at 207k Context Ceiling and Salvaged from Raw JSONL (`board/core.md`, `hooks/context-ceiling.py`)

- **What happened:** During Round 1 of PRD `#202`, the `QA` terminal reached 207,000 tokens with its full findings only in conversation memory. The `context-ceiling.py` hook blocked `Edit` on the PRD file, and the terminal viewport only showed the tail of the output. The Manager had to locate the raw session log under `~/.claude/projects/<project-role-id>/*.jsonl`, extract the last message containing `REPORT` into `runs/202-QA/report-round1.md`, and recruit a fresh QA terminal to resume from disk.
- **Cost:** Manual transcript forensics mid-sprint.
- **Permanent fix:** Two changes:
  1. `board/core.md`: State goes to disk *the moment it is born* (every finding, HOLD item, or phase result is written immediately, never held in memory until the end of the turn).
  2. `hooks/context-ceiling.py`: Even above the 200k hard deny ceiling, `Write` and `Edit` inside `planning/<project>/runs/` and un-chained `python3 scripts/order.py report` calls are explicitly exempted so a terminal at ceiling can always flush its final state to disk before resetting.

---

## 9. 2026-11-13 — "Verification Email Never Arrived" Was an Outlook Delivery Delay (`board/rollout-manual.md`)

- **What happened:** Application logs showed 53 `ok` responses from AWS SES, but the Manager assumed a misconfigured recipient or TLS issue and burned three diagnostic rounds with the human checking credentials, SMTP hosts, and certificates. The email had arrived in Gmail at 09:43 and was simply delayed/filtered on the Outlook recipient side.
- **Cost:** 3 rounds of wasted infrastructure debugging.
- **Permanent fix:** Diagnostic order of operations in `board/rollout-manual.md`: always verify the cheapest external boundary first (recipient inbox arrival timestamp and spam folder) before inspecting credentials, DNS, or server logs.

---

## 10. 2026-11-14 — Annotated Test Flake Broke `git push` (`board/manager.md` §3)

- **What happened:** On order `208-3`, `Dev Front` reported *"inbox J/K test flaked with 2 workers, green in isolation."* The Manager recorded it as a harmless caveat. When the human ran `git push`, the `pre-push` hook failed on Vitest. Running two suites simultaneously reproduced the failure in minutes: two Design System tests were rendering the entire catalog against a 5s timeout, and the email editor had a real race condition (`chain().focus()` deferred by Tiptap colliding with `returnFocusTo`). Fixed in `7c7dbed` and `d831d3e`; 8 concurrent suites under double load ran green.
- **Cost:** Broken `git push` at delivery time.
- **Permanent fix:** There is no such thing as an "acceptable test flake." Any test that fails under parallel workers is treated as a real concurrency bug or timeout defect and must be fixed before `REPORT Status: completed`.

---

## 11. 2026-11-15 — Batch Decision Applied with Inverted Negation in PRD Test Criteria (`#218` & `#221`, `board/explorer.md`)

- **What happened:** `Explorer` applied human decisions M11 (Technical Program Manager excluded from Product family) and M13 (Analytics Engineer included in Data family) in the `Scope` section of PRDs `#218` and `#221`, but wrote the corresponding bullets under `Must Not Happen` with the negation flipped. Only the blind reviewer reading the PRDs as a grading rubric caught the contradiction.
- **Cost:** Would have locked inverted regression tests into the test suite.
- **Permanent fix:** After applying batch product decisions to a PRD, an independent verification pass cross-checks `Scope` against `Must Not Happen` and `Part 4 — QA` before the PRD is marked `Ready`.

---

## 12. 2026-11-16 (Day & Night) — Unmeasured UI Screenshot (`#213`), Blind Dual Discovery (`#222b`), and Premature Sprint Launch (`scripts/order.py`)

- **What happened (Day — UI Invariant Miss):** On PRD `#213` Phase A, the Manager looked at `catalog-390.png` and approved it for the human. The "at 8 seconds" loading state showed a generic 3-line skeleton inside a centered `h-80` box whose height differed from both the loaded and error states. The rule *"no layout shift across loading, content, empty, or error states"* had been in `CLAUDE.md` since Nov 15. The human caught it immediately, requiring two fix commits (`2b60469`, `18d50ba`).
- **What happened (Night 1 — Blind Dual Discovery Proof):** While building the executive golden set for `#222b`, Claude found 34 candidates and Codex found 40 candidates; their intersection was only **3** (expanding executive coverage from 6 to 45 jobs in the diagnostic). On job-family gaps, their intersection was **0 out of 85**. Out of 9 label doubts, reading the full job description resolved 5 automatically and 4 went to the human with an accepted recommendation.
- **What happened (Night 2 — Premature Sprint Launch):** The human authorized the overnight sprint to start *"at midnight (00:00)."* The Manager dispatched order `220-A` at 19:40 and had to abort it mid-flight.
- **Permanent fixes:**
  1. `board/manager.md` §4: The Manager never forwards a UI screenshot to the human without first verifying `CLAUDE.md` UI invariants (skeleton matches real card geometry; loading -> loaded/error causes zero pixel height shift).
  2. `board/manager.md` & `board/playbook.md`: Discovery that defines an epic, golden set, or final audit always runs as **Blind Dual Research** (`Gemini × Codex` reading the same on-disk brief without seeing each other's output).
  3. `scripts/order.py` & `board/manager.md` §3: Any future start time stated by the human becomes a scheduled one-shot Maestri routine (`maestri routine create ... --once`), and `order.py open` validates the exact authorization quote in `runs/<prd>/authorization.md` before any `maestri ask` can be sent.

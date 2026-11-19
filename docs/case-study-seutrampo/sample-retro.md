# Sample Kaizen Session Retrospective (`/canvas-retro`)

> **Context:** This is a sanitized English translation of a real `/canvas-retro` session from **SeuTrampo AI** (`2026-11-19 12:10`), demonstrating how the Manager closes a work cycle, evaluates only the rules exercised during the session, enforces a **net-zero line balance (`line balance <= 0`)** on core prompt files, and queues `role-check.py` for the next startup.

---

## Step 1 — Terminal Status Snapshot (Read-Only)

Before writing the retrospective or running cleanup, `/canvas-retro` checks every connected terminal via `maestri list` and `maestri check`:

| Terminal | Idle? | Current / Last Task | Peak Context |
| --- | --- | --- | --- |
| `Manager` | Yes (self) | Closing M35 golden-set gate & Gemini pool integration | `164k / 200k` |
| `Explorer` | Yes | Tie-breaker on 6 golden-set job descriptions (`#231`) | `118k / 200k` |
| `Designer` | Yes | Blind labeler #2 on 79 golden-set rows (`#231`) | `94k / 200k` |
| `Writer` | Yes | Blind labeler #1 on 79 golden-set rows (`#231`) | `102k / 200k` |
| `Dev Front` | Yes | Shipped `#230-B2` (`99ad994`, 1,590 Vitest passed) | `131k / 200k` |
| `Dev Back` | Yes | Fixed Docker container teardown (`d7c6778`) | `112k / 200k` |
| `QA` | Yes | Verified `#230` Round 6 PASS + 5 M35 checks (reset before each) | `126k / 200k` |
| `Rollout` | Yes | Post-deploy read-only check `229-POSDEPLOY` | `78k / 200k` |
| `Reviewer` | Yes | Blind labeler #3 (`Gemini 4`) on 79 golden-set rows | `88k / 200k` |

---

## Step 2 — The On-Disk Retrospective File

Saved to `.maestri/retros/2026-11-19-1210-seu-trampo-ai.md` (strictly `<= 40` lines, zero narrative padding):

```markdown
# Retro 2026-11-19 12:10 — #231 M35 Golden Gate & Gemini Pool Integration

## Worked On
- #231 M35 closed: Himalayas batch 2 (30/30 inspected), check-ats + 79 blind labels (`ca021be`, worktree 231). M35 QA (region 11.8%, dead-link 20.0%) and Product (2.2%, 18.3%) approved by Human.
- Multi-harness Gemini pool: benchmarked models (`runs/gemini-pool/models.md`); `/grill-me` -> `integration.md` (Explorer/Writer on AGY Neon high, blind dual research Gemini × Codex, 2nd opinion Argon medium, automatic quota fallbacks).
- #231 Phase C scheduled via one-shot routine for 13:05 (Claude 5h window at limit). Planning commits `7abaaf3`, `f3a39cf`, `ddc8c17`.

## How
- Blind 3-way labeling (Writer on Sonnet, Designer on Codex, Reviewer on Gemini): 60 unanimous, 13 majority with `?`, 6 resolved by Explorer reading full descriptions, only 2 escalated to Human.
- 5 sequential ORDERs to QA, each preceded by `maestri recruit --replace`.

## Results
- PRDs closed: 1 (`#230` ready for batch push) + M35 gate approved for `#231`. Human interaction rounds: 7. Rework loops: 0.
- Blind Reviewer abstained (`?`) on only 1/79 rows (vs Writer 9, Designer 13) and matched Explorer on 5/5 tie-breakers.

## Learnings
- ✅ Blind trio + Explorer description tie-breaker: Human only had to adjudicate 2 of 79 rows (matching his request: "only bring me genuine edge cases").
- ✅ Independent third model family breaks ties where two models abstain.
- ❌ Claimed a "second session" was attached to QA after seeing grey text in the QA input prompt; it was Claude Code autocomplete ghost text -> observe (recorded in `cases.md`).
- ❌ Claude 5h quota window stalled Phase C while the Gemini pool sat idle -> fix (`integration.md`; update dual research & fallback rule in gate).
- ❌ Himalayas batch 2 spent 30 browser clicks to resolve 2 `?` rows -> observe (platform pagination limit; ask before running a 2nd batch).

## Rules Touched
- `board/manager.md`: Dual Research — missing Gemini × Codex pairing -> adjust
- `board/playbook.md`: Dual Research & Quota Fallbacks — missing AGY fallback table -> adjust
- `board/core.md`: Messages (`order.py` on disk, `--resumes` requires prior REPORT) — helped -> keep
- `board/manager.md`: Escalate only the residual to Human — helped (2/79 rows) -> keep

## Gate Decisions
- `board/manager.md`: Pair Gemini × Codex for blind dual research + Argon 2nd opinion (paid for by cutting duplicate HOLD sentence already in `core.md`, net line delta: 0) — approved
- `board/playbook.md`: Route blind dual research to Gemini × Codex, divergence to Explorer — approved

## Pending
- 13:05/13:06 one-shot routines `mgr-clear-1305` and `mgr-resume-1306` -> apply `integration.md` recruit commands and dispatch `#231` Phase C.
- Batch `git push` for `#230` + `#231` (Human).
- `board/manager.md` changed: run `python3 scripts/role-check.py Manager` on resume.
```

---

## Step 3 — Net-Zero Kaizen Gate in Action (`line balance <= 0`)

In `/canvas-retro`, you cannot simply append a new rule to `board/core.md` or `board/manager.md`. Every new line must be paid for by cutting or merging an existing line that is either duplicated or automated by a script.

Here is the exact Kaizen proposal presented to the human during Step 4 of this retrospective:

```diff
--- a/board/manager.md
+++ b/board/manager.md
@@ -12,6 +12,6 @@
 4. **Delivery:** UI screenshot goes to Human only after you verify CLAUDE.md UI invariants (skeleton matches real geometry; loading -> content/error with zero layout shift, 16/11); QA evidence -> Human (`playbook.md`) -> merge after OK -> Close-out (`playbook.md`).
 
-**Dual research** (16/11): Claude × Codex, blind; Manager cross-checks. QA <-> Devs close HOLD loops without you; step in only on PASS, decision, 3rd loop, or ceiling (18/11).
+**Dual research** (19/11): Gemini × Codex, blind; Claude only as 3rd on divergence; Manager cross-checks. Trade-off decision to Human carries a blind 2nd opinion from Gemini (Argon medium).
 Doubt -> Explorer reads full description; escalate only the residual to Human. Code and PRD: single owner.
```

**Why this diff passed the gate:**
1. The sentence *"QA <-> Devs close HOLD loops without you; step in only on PASS, decision, 3rd loop, or ceiling (18/11)"* was already present in `board/core.md` under `## Team` (which every terminal, including the Manager, loads). Keeping it in `manager.md` was pure duplication.
2. Deleting that duplicate sentence paid for adding the `Gemini × Codex` dual research rule and the blind `Argon` second-opinion requirement.
3. **Budget verification:**
   - `board/core.md`: 482 words (budget: `<= 500` words)
   - `board/manager.md`: 318 words (budget: `<= 400` words, net line delta: `0`)
   - The full incident about Claude Code's ghost input suggestion was written to `cases.md` (`2026-11-19`), keeping `manager.md` lean.

---
name: handover
description: Close the current session by writing a hand-over document that the next session loads automatically. Invocation is always manual — use when the user asks for "handover", "pass the baton", "save context for the next session", or says the context window is full and it is time to start fresh. Never trigger autonomously. Do NOT use to save progress mid-task; a hand-over presupposes the current work cycle is at a clean boundary.
---

# Hand-over

Writes the document that the next session will receive as **active context** —
not as passive history. The `handover-restore.js` hook injects this file on the
next `SessionStart` and marks it consumed.

You author this document yourself because you hold the real architectural context in working memory. No regex extractor comes close — which is why the pipeline never generates hand-overs via a script.

## Before Writing

If you are in the middle of an unfinished edit: **do not run this skill yet.** Finish the current cycle or reach a green checkpoint first. A hand-over captured mid-edit describes a half-state that does not exist cleanly on disk. If the user explicitly insists on handing over mid-task anyway, write it — but record under `## Blockers` the exact half-finished state.

## Steps

**1. Discover the session ID and context token counts**

```bash
ls -t ~/.claude/session-data/handover-state/*.json 2>/dev/null | head -1
```

Read that file: it contains `tokens`, `model`, `soft`, `hard`, and the current `level`.
The basename without `.json` is the `session_id` — use it in the output filename so the
session hook can locate the hand-over.

If the directory is empty (manual hand-over while context usage is still low), use
`manual` as the `session_id` and omit `tokens_at_handover`.

**2. Verify the actual state of the work on disk**

Never trust conversational memory to claim something works. Before writing `## Current State`:

- Run `git status --short` and `git diff --stat` in the relevant repository, if applicable
- Run existing tests for the files you touched
- Confirm that every file you claim to have created exists on disk

Every line under `## Current State` requires evidence: passing test count, observed command output,
or verified file path on disk. Anything not verified does not belong in `## Current State` — put it
under `## Blockers`.

**3. Write the hand-over file**

Path: `~/.claude/session-data/handover/<YYYY-MM-DD>-<session_id>-handover.md`

````markdown
---
status: pending
session_id: <id>
created: <ISO-8601>
tokens_at_handover: <n>
model: <model id>
project: <project or factory name>
---

# Hand-over: <short, concrete title>

## Goal
What this line of work is trying to achieve, in one or two sentences.
Not the history of the conversation — the target outcome.

## Current State
What is done **and verified**, with the evidence next to each item.
- `/abs/path/to/module.js` created — 17/17 tests passing (`node .../handover.test.js`)
- Hook registered in `settings.json` — confirmed with `jq .hooks.Stop`

## What Didn't Work
Discarded attempts and why they failed. This prevents the next session from repeating
dead ends that already burned tokens here.

## Key Files
| Path (absolute) | Role | State |
|---|---|---|
| `/abs/path/to/x.js` | what it does | created / modified / untouched |

## Decisions
Choices made and their rationale. Include rejected alternatives whenever the reason
matters for the next step.

## Blockers
Open questions, half-finished items, or decisions waiting on the user.
If none, write "none".

## Exact Next Step
The very first concrete action for the next session. One command, one file, one edit.
Never write "continue the implementation" — state which file to open and what to do in it.

## Context to Load
Files to read before starting, ordered by importance. Include only what is strictly
necessary — this list exists to save context tokens, not spend them.
````

## Rules

- **Use absolute paths in the generated hand-over document.** The next session may start in a different working directory.
- **Do not re-narrate the conversation.** Nobody needs the chronological order in which things were discovered. State only the verified current state and what to do next.
- **No "probably works".** If it was not verified with a command, it is a blocker, not current state.
- If a `pending` hand-over already exists for the same `session_id`, **overwrite it**. One hand-over per session.

## When Finished

Show the user:

1. The path of the written hand-over file.
2. A 3-line summary: where you stopped, exact next step, blockers.
3. The instruction: **run `/clear`** — the next session loads this context automatically via `handover-restore.js`. Nothing needs to be copied manually.

Do not continue working after writing the hand-over. The purpose of this skill is to stop cleanly.

## Harness portability

- In Codex or Antigravity where `handover-restore.js` is not hooked into `SessionStart`, also save or symlink the hand-over under `planning/<project>/runs/` so the next session or `/canvas-manager [project] resume <file>` can load it directly.

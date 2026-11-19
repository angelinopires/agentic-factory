---
name: grill-me
description: Relentless interview that stress-tests a plan, decision, or idea until every branch of its decision tree is settled. Use when the user says "grill me", "stress-test this idea/decision", "question my plan", or when /prd enters deep mode. Discusses only; never implements.
---

# Grill Me

> Adapted from `grilling` in [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

Interview the user relentlessly until you reach a shared understanding. Ask questions in the user's configured language (`language` in `board.config.json`, or the language used in the conversation).

## The decision tree

Map the topic as a **design tree**: every decision branches into the decisions that hang off it.
The **frontier** is every decision whose prerequisites are already settled — what you can ask *now*
without guessing at answers you haven't heard. A question that depends on another question still
open belongs to a *later* round.

## Rounds

- One round = one selectable-question tool call (Claude Code: `AskUserQuestion`; Codex: `request_user_input_async`): up to 4 questions, 2–4 options each, your recommended
  option first with "(Recommended)". The tool always leaves an open "Other" answer.
- Frontier bigger than 4 → ask the 4 that unblock the most; the rest wait for the next round.
- A question with no discrete options → ask it as numbered text in chat, with your recommendation.
- After each round, recompute the frontier from the answers and ask the next round.

## Facts are yours, decisions are the user's

Never ask the user something you can look up (code, docs, `progress.md`, ADRs, git history). Dispatch
an Explore sub-agent (or read the files directly) and keep asking the questions that don't depend on the result; only the
questions downstream of a running lookup wait. Decisions always go to the user.

## Posture

Recommendations are honest, not agreeable: if the premise is weak, the recommendation says so
(see `rules/communication.md`). Name what's missing.

## ADRs (optional)

If the project already keeps ADRs (e.g. `docs/adr/` or `server/docs/adr/` with a `000-template.md`)
and a settled decision is all three — hard to reverse, surprising without context, the result of a
real trade-off — **offer** to record it using that project's own template. Never write one without
an explicit yes. No ADR folder → don't create one.

## Done

The session ends when the frontier is empty: every branch visited, nothing silently assumed.
Close with a short list of the decisions made and ask the user to confirm the shared understanding.
Do not act on it (no code, no files) until they confirm — and when invoked from `/prd`, hand the
decisions back to `/prd` Step 3.

## Harness portability

- In Claude Code, use `AskUserQuestion`. In Codex, use `request_user_input_async` for selectable options. Use another selectable-question tool when supported by the harness. Prefer selections over typed option letters. Only fall back to numbered text with lettered options and an open answer when no selectable tool is available. Wait for answers before asking dependent questions.
- Explore sub-agent → if sub-agents are unavailable in the current harness, read the files sequentially yourself before asking the dependent questions.

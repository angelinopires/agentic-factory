---
name: infra-preflight
description: Method and trap catalog for infrastructure PRDs (Docker, compose, CI, deploy, cron, observability collectors). Load when a PRD has `**Infra:** yes` (or `sim`) in its header, when writing (/prd) or implementing that PRD, and when verifying in the target environment before and after deploy. Do NOT use on product, UI, or ingestion PRDs without infrastructure changes.
---

# infra-preflight

Infrastructure bugs escape through **unverified assumptions** or **environment drift** (macOS × CI × server), not lack of context. Code review and spec-compliance checks run on a developer machine and cannot see the target host. This skill forces verification in the target environment for everything code review cannot see.

Two parts:

- **Method** (this file): the questions every infrastructure PRD must answer and the three verification checkpoints.
- **Catalog** (`references/catalog.md`): traps already encountered in production, each with symptom, cause, and the test that catches it.

Project-specific facts (target environment, UID, paths, how deploy recreates each service, local traps) **do not live here**: they live in `docs/infra.md` at the repository root. Read it before answering the questions. If it does not exist yet, create it as part of the PRD using the pre-flight output.

## When to use

Any PRD with `**Infra:** yes` in the header. Also applies to any PRD without that marker that touches a Dockerfile, compose file, CI/deploy workflow, crontab, or collector config: in that case, require the PRD author to add the marker first.

## 1. When writing the PRD

Read `docs/infra.md` and `references/catalog.md`. The PRD must answer in writing, citing the source of each answer (a line in `docs/infra.md`, pre-flight command output, or a justified `n/a`):

| # | Question | Trap avoided |
|---|---|---|
| 1 | What environment does it run in? OS, architecture, Docker/Compose version, UID:GID of the process inside the container | C2, C3 |
| 2 | What does the service read or write **on the host** (path, owner, mode)? Can the container UID access it? | C2, C3 |
| 3 | How does the change reach an already-running process: rebuild, recreate, reload, or nothing? Applies to code, mounted config, env, and labels | C1, C8 |
| 4 | What produces the data this code consumes (log, file, event)? Does the test use real producer output? | C4, C5 |
| 5 | What else writes to the same resource (database, file, queue) and on what schedule? | C6 |
| 6 | On which events do CI or deploy trigger, and which context variables can arrive empty in each event? | C7, C9 |
| 7 | How do we prove after deploy that it worked: which signal, where, and within what time window? | all |

Any answer that depends on the target host and is missing from `docs/infra.md` becomes a **pre-flight request** (Section 2), never an assumption.

## 2. Target-environment pre-flight (before implementation)

Whoever has read access to the target runs **read-only** commands and pastes the output into the PRD. Never run anything that writes, restarts, or deletes, and never print env vars or secrets (`docker inspect` without `--format`, full `compose config`, `env`, `cat .env`).

```bash
id; uname -m; docker version --format '{{.Server.Version}}'; docker compose version
stat -c '%U:%G %a %n' <each host path the service reads or writes>
docker compose -f <compose> config --services            # never the full config: it prints resolved env secrets
docker inspect <container> --format '{{.Config.User}} {{json .Mounts}} {{json .Config.Labels}}'  # only these fields
docker compose -f <compose> exec -T <service> id         # actual process UID
docker compose -f <compose> logs --tail 5 <service>      # actual log line format the consumer will parse
```

Respect the project's production guardrails (e.g., commands blocked by `prod-guard.py` go to the user; never run direct SQL against production). Any new fact discovered here is added to `docs/infra.md` in the same PRD.

## 3. Before spec-compliance review: run tests like CI

Docker Desktop on macOS masks the owner and permissions of bind-mounted files; a Linux runner does not. A green test on macOS does not prove file readability on Linux.

1. Run tests that spin up a container or mount files inside a **Linux environment with a non-root UID**: CI, a Linux VM, or a Linux container where test files are **created inside the container filesystem** (not bind-mounted from macOS). If proof can only run on GitHub Actions (`workflow_dispatch` on the branch), which requires a `git push` owned by the user, the PRD must include an explicit `🔒 User` step before Stage A2 (Case #166).
2. Any test that mounts a host file into a container: either the container runs with `--user "$(id -u):$(id -g)"` from the host, or the test proves readability with the file set to `0700` and owned by a UID different from the container UID.
3. Paste the exact command and output into the PRD. Without pasted output, QA holds the PRD.

## 4. After deploy

The PRD declares the post-deploy verification (Question 7) with a deadline, and the role or user with target access executes it:

- The new container exists and runs the new revision (container ID changed, label/image matches expected SHA).
- Any service depending on a mounted config was recreated when the config changed (C1).
- The business signal appears where the consumer reads it (alert resolves, log line reaches collector, scheduled job runs on time).

If the signal does not appear within the window, treat it as an escaped bug and open a fix PRD.

## 5. Escaped infrastructure bugs

A fix PRD only closes once the trap is recorded:

- **General** (could happen in another project with the same stack): add a new entry to `references/catalog.md`, following the existing format without project names.
- **Local** (depends on a specific path, UID, or script in this project): add to the "Local traps" (`L1..Ln`) section of the project's `docs/infra.md`.

A new domain (networking, TLS, backups, secrets, scaling) enters the catalog only from a real incident.

## Harness portability

- This skill is plain markdown and works identically across all harnesses (Claude Code, Codex, Antigravity).
- Whenever this skill says "ask": use `AskUserQuestion` in Claude Code; in Codex and Antigravity, ask in plain text with numbered options and stop until the user replies.
- Long-running jobs (Docker test suites): in Claude Code, use background task monitoring; in Codex, run in the foreground. Never use raw `nohup`, `&`, or `setsid`.
- If your terminal lacks target access: write the Section 2 commands into the PRD and ask the role or user with target access to run them. Never substitute assumptions for real command output.

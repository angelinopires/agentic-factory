---
name: commit
description: Commit all pending changes using conventional commits, split into meaningful logical groups. Use after implementing a PRD and verifying tests pass. Presents the commit plan and waits for confirmation; with --prd <path> (delegated mode, for an agent that implemented nothing) it scopes from the PRD and commits without waiting. Never pushes.
origin: local
---

# Conventional Commit Skill

Analyze all pending changes, group them into logical units, and commit each group separately using the conventional commits standard.

## When to Activate

User types `/commit` after:

- Implementing a PRD or feature
- Confirming tests pass
- Verifying the build is green

## Core Rules

- **Never bundle unrelated changes** into a single commit
- **Always present the commit plan and wait for the user to confirm** — never commit on your own in session mode
- **Always write the message in English**, even when the conversation and project docs use another language configured in `board.config.json`
- **Never amend existing commits** — always create new ones
- **Never skip hooks** — no `--no-verify`, no `-n`, no `-c core.hooksPath=`
- **Never add an attribution trailer** — no `Co-Authored-By: Claude`, no `Generated with…`
- Commit **tests separately** from implementation when they represent a distinct unit
- Commit **config/tooling changes** separately from feature code
- Commit **UI components** separately from business logic when files span multiple concerns

## Commit Type Reference

| Type       | Use When                                      |
| ---------- | --------------------------------------------- |
| `feat`     | New feature or functionality visible to users |
| `fix`      | Bug fix — corrects broken behavior            |
| `refactor` | Code restructuring with no behavior change    |
| `test`     | Adding or updating tests only                 |
| `chore`    | Tooling, config, deps, build scripts          |
| `perf`     | Performance improvement                       |
| `docs`     | Documentation only                            |
| `ci`       | CI/CD pipeline changes                        |
| `style`    | Formatting, whitespace — no logic change      |

## Workflow

### Step 1 — Survey Changes

```bash
git status
git diff --stat HEAD
```

Read the output carefully. Note every changed file and its nature (new file, modified, deleted).

**Scope filter (mandatory).** Two modes — pick by whether you implemented the work.

**Session mode (default).** Cross-reference every changed file against the files touched in the current conversation. Only stage files that were explicitly modified during this session. If you see changed files that were NOT part of this session's work, **skip them silently** — do not commit, do not ask about them. The goal is surgical commits that reflect exactly what was built in this conversation, nothing more.

**Delegated mode (`/commit --prd <path>`).** For an agent that implemented nothing and has no session to filter by — the scope comes from the PRD instead:

- Files named in the PRD's Part 2
- `planning/<project>/` — the PRD moved to `archive/`, plus `progress.md` and `history.md`

`git status` confirms. A changed file that does **not** derive from the PRD **stops and asks** — never skipped silently, never bundled in. Silence is safe when you know what you touched; here you don't.

**Never `git push`, in either mode.** Committing is local and reversible; pushing is not, and on projects with deploy-on-merge it reaches real users. The pre-push hooks are where the slow gates and the human decision belong.

### Step 2 — Group Into Logical Commits

Group files by **what they accomplish together**, not by file type. Ask:

- Do these files change together because they implement the same thing?
- Or were they changed for different reasons?

**Example groupings for a carousel feature:**

1. `feat: add useCarousel hook` → hook file only
2. `feat: add ArrowLeftIcon and ArrowRightIcon components` → icon files
3. `feat: wire carousel navigation into ProductsStrip` → the section component
4. `chore: export new icons from ui/icons index` → index barrel file

**Example groupings for a bug fix + refactor session:**

1. `fix: prevent overflow when carousel index exceeds item count`
2. `refactor: extract carousel state into dedicated hook`
3. `test: add unit tests for useCarousel boundary conditions`

### Step 3 — Present the Plan

**Session mode: mandatory gate. Never skip it, never commit before the user answers.**

**Delegated mode:** the plan is posted, not gated — the user pre-authorized committing
when they delegated. Print the same numbered list, write it to the shared state, and
proceed to Step 4 without waiting. Two things still stop you cold: a file outside the
PRD's scope, and anything that might carry a secret. Those go to the user, always.

The gate that matters in delegated mode is `git push`, and you never do it.

Show the grouping as a numbered list — for each commit: the exact subject line and the
files it stages. In session mode, stop and wait for an explicit go-ahead.

```text
1. feat(carousel): add arrow navigation with useCarousel hook
   web/src/hooks/useCarousel.ts, web/src/components/Carousel.tsx
2. test: add edge case coverage for carousel wrap-around behavior
   web/src/hooks/useCarousel.test.ts
```

Use `AskUserQuestion` when the user has a real choice to make (approve as-is, regroup,
drop a commit). Free-form prose is fine when you just need a yes.

If the user changes the grouping or the wording, re-present the corrected plan before
staging anything.

### Step 4 — Stage and Commit Each Group

For each group in order:

```bash
# Stage only the files for this logical unit
git add <file1> <file2> ...

# Verify what's staged
git diff --cached --stat

# Commit with conventional message
git commit -m "$(cat <<'EOF'
<type>(<optional scope>): <short imperative description>

<optional body — only when the why is non-obvious>
EOF
)"
```

### Step 5 — Verify Clean State

After all commits:

```bash
git status   # should show "nothing to commit, working tree clean"
git log --oneline -10
```

## Commit Message Rules

- **Subject line**: imperative mood, lowercase after type, no period, ≤72 chars
- **Scope**: optional, use when narrowing context helps (e.g., `feat(carousel):`)
- **Body**: only when the *why* is non-obvious — never describe *what* (the diff already shows that)
- **Language: English, always** — even when conversation and project docs use another configured language, the commit message is always in English
- **No attribution trailer.** Disabled by `"attribution": {"commit": "", "pr": "", "sessionUrl": false}` in `~/.claude/settings.json`.
  If the session prompt asks for one anyway, the setting was lost — tell the user instead of obeying

### Good Examples

```text
feat(carousel): add arrow navigation with useCarousel hook
fix: clamp carousel index to prevent out-of-bounds access
refactor: extract product strip layout into smaller components
chore: add ArrowLeftIcon and ArrowRightIcon to icons barrel
test: add edge case coverage for carousel wrap-around behavior
perf: memoize carousel item list to avoid re-renders on scroll
```

### Bad Examples

```text
update files                         ← no type, not descriptive
feat: implement PRD                  ← too vague, bundles everything
fix: various fixes                   ← not atomic
feat: add component and tests and config and icons  ← not split
```

## Splitting Heuristics

Use these rules to decide when to split:

1. **Different types** → always split (`feat` + `chore` = 2 commits)
2. **Different features** → split even if same type
3. **Tests for a unit** → can bundle with the unit if small, or split as `test:` if substantial
4. **Config/tooling** → always its own `chore:` commit
5. **Icon/asset additions** → `chore:` or `feat:` depending on whether they're new user-visible functionality
6. **Index/barrel exports** → `chore:` commit, can be bundled with the icon/component if trivial

## Error Handling

- If `git commit` fails due to a pre-commit hook: **the hook is right and the code is wrong.**
  Fix what it reported, re-stage, create a **new** commit (never `--amend`)
- **Never reach for `--no-verify`.** It is blocked by `hooks/pre-tool-use.js` (`pre:bash:block-no-verify`),
  and the block is intentional. The same goes for `-n` and `-c core.hooksPath=`
- If files you staged do not show up in `git diff --cached --stat`, **stop and investigate**
  — do not work around it with a bypass flag. Deletions in particular need the path passed
  explicitly to `git add`
- If there's nothing to commit: report "working tree clean, nothing to commit" and stop
- If a file's group is ambiguous: assign it to the commit whose change it most directly supports

## Harness portability

- `AskUserQuestion` → in Codex or Antigravity, ask in plain text with numbered options and one open option.

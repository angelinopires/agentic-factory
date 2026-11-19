# Agent Orchestration

## Available Agents

Provided by the `everything-claude-code` plugin:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review | After writing code |
| security-reviewer | Security analysis | Before commits |
| build-error-resolver | Fix build errors | When build fails |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| doc-updater | Documentation | Updating docs |
| rust-reviewer | Rust code review | Rust projects |

## When to Spawn

Default: handle the task directly. Spawn an agent only when it needs independence
(e.g. reviewing code this session wrote) or the stakes justify the token cost
(hard-to-reverse architecture, large PRD). A project's routing table overrides this.

## Parallel Task Execution

Run independent operations in parallel. When you do spawn several agents for
independent work, launch them in one batch.

## Multi-Perspective Analysis

For high-stakes decisions, split-role sub-agents can give diverse perspectives:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

---

# Agent Orchestration

## Available Agents

Provided by the `everything-claude-code` plugin:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review | After writing code |
| security-reviewer | Security analysis | Before commits |
| build-error-resolver | Fix build errors | When build fails |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| doc-updater | Documentation | Updating docs |
| rust-reviewer | Rust code review | Rust projects |

## When to Spawn

Default: handle the task directly. Spawn an agent only when it needs independence
(e.g. reviewing code this session wrote) or the stakes justify the token cost
(hard-to-reverse architecture, large PRD). A project's routing table overrides this.

## Parallel Task Execution

Run independent operations in parallel. When you do spawn several agents for
independent work, launch them in one batch.

## Multi-Perspective Analysis

For high-stakes decisions, split-role sub-agents can give diverse perspectives:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker

# Rule: Global Skills Creation

**Trigger**: When the user asks to create or set up a global skill (a skill not attached to a specific project).

**Instructions**:
Whenever you create a new global skill (not tied to a specific project), create the files physically in `~/.claude/skills/` (Claude Code harness) and then symlink that folder into **both** external harnesses:

- `~/.gemini/config/skills/<name>` — Antigravity (`agy`)
- `~/.agents/skills/<name>` — Codex (user skills directory read by Codex)

Without both symlinks, the skill is invisible to half of the Maestri canvas — a gap measured in production when Codex could not see any personal skill.

Never create global skills directly in a project workspace (e.g., `.agents/skills/`) or physically inside the Antigravity or Codex folders. Before creating a skill, check that a skill with the same name does not already exist in ECC (`.agents/skills/` or the `everything-claude-code` plugin) — duplicate names are not allowed; the ECC skill prevails. Registered exception: `article-writing` (customized local copy overrides ECC).

Every new skill must be portable: if it references a Claude Code-exclusive tool (`AskUserQuestion`, `preview_*`, sub-agents), include the equivalent for the other harnesses (see `rules/AGENTS.md`, section `## Harness portability`).

# Performance Optimization

## Model Selection

Main session: the current Opus (or configured high-tier model). Subagents doing high-volume reading or mechanical
work: the current Sonnet or Haiku (or configured medium/low-tier model). Trade depth for cost with effort before switching model.

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Reasoning depth

Thinking is always on; depth is set by effort (`/effort`), not a token budget.
Use Plan Mode for hard-to-reverse changes.

## Build Troubleshooting

If build fails:
1. Use **build-error-resolver** agent
2. Analyze error messages
3. Fix incrementally
4. Verify after each fix

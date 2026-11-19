#!/bin/sh
# Active context usage of the Manager session in k-tokens.
# Usage: manager-context.sh [session-id] — without an ID, inspects the most recent session for MAESTRI_WORKSPACE_ROOT (or cwd).
ws_root="${MAESTRI_WORKSPACE_ROOT:-${MAESTRI_PROJECT_DIR:-$(pwd)}}"
ws_slug=$(printf '%s' "$ws_root" | tr '/.' '--')
d="$HOME/.claude/projects/$ws_slug"
if [ $# -gt 0 ]; then
  f=$([ -n "$1" ] && ls "$HOME"/.claude/projects/*/"$1".jsonl 2>/dev/null | head -1)
  [ -n "$f" ] || { echo "manager-context: session '$1' not found in ~/.claude/projects/*/" >&2; exit 1; }
else
  if [ -d "$d" ]; then
    f=$(ls -t "$d"/*.jsonl 2>/dev/null | head -1)
  else
    f=$(ls -t "$HOME"/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
  fi
  [ -n "$f" ] || { echo "manager-context: no session found in $d" >&2; exit 1; }
fi
python3 - "$f" <<'PY'
import json, sys
u = None
for line in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    try:
        m = json.loads(line)
    except ValueError:
        continue
    if m.get("type") == "assistant":
        u = (m.get("message") or {}).get("usage") or u
t = 0 if not u else u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
print(f"{t // 1000}k")
PY

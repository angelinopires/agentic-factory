#!/usr/bin/env python3
"""PreToolUse hook: enforces context token ceiling for Maestri canvas agents.

Covered sessions:
- Roles (`cwd` or `CLAUDE_PROJECT_DIR` contains `/.maestri/roles/`).
- Manager (any other session running inside a Maestri terminal with `MAESTRI_SOCKET` set).

Thresholds:
- Above `CEILING - WARN_MARGIN`: emits a one-time warning per session (`additionalContext`), does not block.
- Above `CEILING`: roles receive `permissionDecision="deny"`; Manager logs `would-deny` unless `MANAGER_MODE=deny`.
- Always exempt: single unchained Bash commands `maestri ...` or `python3 .../scripts/order.py ...`, and
  `Write`/`Edit`/`MultiEdit` targeting files inside `/runs/` (where agents record state before reset).
"""
import json
import os
import re
import sys
import time


def load_ceiling_config() -> tuple[int, int, str]:
    ceiling = os.environ.get("MAESTRI_CONTEXT_CEILING")
    warn_margin = os.environ.get("MAESTRI_CONTEXT_WARN_MARGIN")
    mgr_mode = os.environ.get("MAESTRI_CONTEXT_MANAGER_MODE")
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        os.path.join(os.getcwd(), "board.config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    cc = json.load(f).get("context_ceiling") or {}
                ceiling = ceiling or str(cc.get("ceiling_tokens", ""))
                warn_margin = warn_margin or str(cc.get("warn_margin_tokens", ""))
                mgr_mode = mgr_mode or cc.get("manager_mode")
                break
            except (OSError, ValueError):
                pass
    return (
        int(ceiling or "200000"),
        int(warn_margin or "30000"),
        mgr_mode or "log",
    )


CEILING, WARN_MARGIN, MANAGER_MODE = load_ceiling_config()
STATE_DIR = os.path.expanduser(os.environ.get("MAESTRI_CONTEXT_STATE", "~/.claude/logs"))
TAIL_BYTES = 4_000_000
RUNS_RE = re.compile(r"(?:/planning(?:/[^/]+)?/runs/|(?<!/src)/runs/)")
ORDER_CMD_RE = re.compile(r"^python3\s+(?:\S+/)?scripts/order\.py\s+")
CHAIN_RE = re.compile(r"[;&|\n`]|\$\(")


def last_context(path: str) -> int:
    with open(path, "rb") as f:
        f.seek(max(0, os.path.getsize(path) - TAIL_BYTES))
        lines = f.read().decode("utf-8", "ignore").splitlines()
    for line in reversed(lines):
        try:
            m = json.loads(line)
        except ValueError:
            continue
        u = (m.get("message") or {}).get("usage") if m.get("type") == "assistant" else None
        if u:
            return sum(
                u.get(k, 0) or 0
                for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
            )
    return 0


def who(cwd: str) -> str | None:
    origin = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    if "/.maestri/roles/" in origin:
        return "role"
    return "manager" if os.environ.get("MAESTRI_SOCKET") else None


def exempt(data: dict) -> bool:
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    cmd = inp.get("command", "")
    stripped = cmd.lstrip()
    if tool == "Bash" and not CHAIN_RE.search(cmd):
        if stripped.startswith("maestri ") or ORDER_CMD_RE.match(stripped):
            return True
    path = inp.get("file_path", "")
    return (
        tool in ("Write", "Edit", "MultiEdit")
        and os.path.isabs(path)
        and bool(RUNS_RE.search(os.path.realpath(path)))
    )


def log_event(event: dict) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(os.path.join(STATE_DIR, "context-ceiling.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"context-ceiling: log: {e}", file=sys.stderr)


def first_time(session: str, level: str) -> bool:
    """Return True only the first time a session crosses a threshold level."""
    marker = os.path.join(STATE_DIR, "context-ceiling.seen", f"{session}-{level}")
    try:
        if os.path.exists(marker):
            return False
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        open(marker, "w", encoding="utf-8").close()
    except OSError:
        pass
    return True


def emit(**spec) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", **spec}}, ensure_ascii=False))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    kind = who(data.get("cwd", ""))
    path = data.get("transcript_path", "")
    if not kind or not path or not os.path.isfile(path):
        return
    ctx = last_context(path)
    if ctx <= CEILING - WARN_MARGIN:
        return
    session = data.get("session_id") or os.path.basename(path)
    over = ctx > CEILING
    enforce = over and (kind == "role" or MANAGER_MODE == "deny")
    deny = enforce and not exempt(data)
    action = "deny" if deny else "exempt" if enforce else "would-deny" if over else "warn"
    log_event(
        {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "session": session,
            "kind": kind,
            "ctx": ctx,
            "ceiling": CEILING,
            "action": action,
            "tool": data.get("tool_name"),
            "cwd": data.get("cwd"),
        }
    )
    if deny:
        emit(
            permissionDecision="deny",
            permissionDecisionReason=(
                f"Context ceiling reached: {ctx // 1000}k > {CEILING // 1000}k. Stop work immediately: "
                "save your current state and next step in `runs/` (Write/Edit in `runs/` and `scripts/order.py` "
                'are allowed) and end your turn with "REPORT <id> · Status: partial · context ceiling reached, '
                'requesting reset". Do not run `maestri ask` to the Manager; no other tools will execute.'
            ),
        )
    elif first_time(session, "over" if over else "warn"):
        emit(
            additionalContext=(
                f"Context warning: {ctx // 1000}k of {CEILING // 1000}k ceiling. Finish the current step, "
                "save your state and next step in `runs/`, and request a reset at the next boundary; "
                "do not start large file reads."
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"context-ceiling: {e}", file=sys.stderr)

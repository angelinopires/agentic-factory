#!/usr/bin/env python3
"""PreToolUse hook: blocks destructive or direct-write commands against production environments.

Why this exists
---------------
Harness deny lists (`Bash(sudo *)`, `Bash(rm -rf *)`) only match command prefixes and miss
remote shell payloads such as `ssh host 'sudo reboot'`. This hook inspects both top-level
shell tokens and heredoc bodies for configured production markers, direct database access,
SQL DML/DDL, secret reads, and literal credentials.

Contract
--------
stdin  : PreToolUse JSON payload containing `.tool_input.command`
exit 0 : allowed (including all local commands that do not cite production or leak secrets)
exit 2 : blocked; remediation instructions are written to stderr

Deliberate bypass: set `AGENTIC_PROD_GUARD=off` in the environment.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

DEFAULT_PROD_MARKERS = (
    "docker-compose.prod.yml",
    'maestri ask "vps"',
    "maestri ask vps",
)
LOCAL_DEFAULT_PASSWORDS = ("postgres", "local", "dev", "test", "app", "my_project")

SQL_WRITES = (
    (r"\bdrop\s+(table|schema|database|index|view|role|constraint|column)\b", "destructive DDL"),
    (r"\btruncate\b", "TRUNCATE"),
    (r"\bdelete\s+from\b", "DELETE"),
    (r"\bupdate\s+\w+\s+set\b", "UPDATE"),
    (r"\binsert\s+into\b", "INSERT"),
    (r"\balter\s+(table|role|schema|database|column)\b", "ALTER"),
    (r"\b(grant|revoke)\b", "privilege change"),
    (r"\bcreate\s+(role|user)\b", "role creation"),
)

DIRECT_DATABASE_ACCESS = (
    (r"\bpsql\b", "direct database access"),
    (r"\bdocker\s+compose\b[^|;&]*\b(exec|run)\b[^|;&]*\bdatabase\b", "database container access"),
    (r"\bdocker\s+exec\b[^|;&]*\b\S*database\S*", "database container execution"),
)

IRREVERSIBLE = (
    (r"\bcli\.user\s+delete\b[\s\S]*--confirm-email(?:[=\s]|$)", "confirmed user deletion — human only"),
    (
        r"\bcli\.user\s+reapply-deletions\b[\s\S]*--confirm-journal(?:[=\s]|$)",
        "confirmed deletion replay — human only",
    ),
    (r"\balembic\s+(upgrade|downgrade|stamp)\b", "migrations run during deploy — do not apply manually"),
    (r"\b(scripts/)?migrate-prod(\.sh)?\b", "migrations run during deploy — do not apply manually"),
    (r"\bdocker\s+compose\b[^|;&]*\bdown\b", "docker compose down"),
    (r"\bdocker\s+(rm|kill)\b", "container removal/kill"),
    (r"\bdocker\s+volume\s+rm\b", "volume removal"),
    (r"\bdocker\s+system\s+prune\b", "docker system prune"),
    (r"\b(reboot|shutdown|halt|poweroff)\b", "reboot/shutdown"),
    (r"\bsystemctl\s+(stop|restart|disable|mask)\b", "systemctl stop/restart/disable/mask"),
    (r"\brm\s+-[a-z]*[rf]", "recursive/forced rm"),
    (r"\bchmod\b", "chmod"),
    (r"\bchown\b", "chown"),
    (r"\bpg_restore\b", "pg_restore"),
)

REMEDIATION = """
BLOCKED by prod-guard: {reason}

This command targets production state or infrastructure directly. Production writes belong to the human operator, not the agent.

Provide the exact command for the human to run if required:

    {command}

Alternatives before escalating:
  - ingestion/application telemetry? run read-only CLI tools inside the `api` container
  - administrative data? ask the human to check the admin dashboard
  - missing read-only CLI metric? open a PRD gap instead of querying the production database directly

Do not bypass this guard by writing the command to a script file or encoding it.
""".strip()

SECRET_REMEDIATION = """
BLOCKED by prod-guard: {reason}

Do not expose literal credentials in terminal commands, and do not connect directly to the production database.
""".strip()


def get_prod_markers() -> tuple[str, ...]:
    markers = list(DEFAULT_PROD_MARKERS)
    env_markers = os.environ.get("AGENTIC_PROD_MARKERS", "")
    if env_markers:
        markers.extend(m.strip().lower() for m in env_markers.split(",") if m.strip())
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        os.path.join(os.getcwd(), "board.config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    prod = json.load(f).get("production") or {}
                for key in ("markers", "hosts", "domains", "paths"):
                    for val in prod.get(key) or []:
                        if isinstance(val, str) and val.strip():
                            markers.append(val.strip().lower())
                break
            except (OSError, ValueError):
                pass
    return tuple(dict.fromkeys(markers))


PROD_MARKERS = get_prod_markers()


def _is_literal_secret(value: str) -> bool:
    return value not in LOCAL_DEFAULT_PASSWORDS and not value.startswith("$")


def find_secret(command: str) -> str | None:
    for match in re.finditer(r"postgres(?:ql)?://[^:\s]+:([^@\s]+)@", command, re.IGNORECASE):
        if _is_literal_secret(match.group(1)):
            return "literal secret: Postgres DSN with password"

    for match in re.finditer(
        r"\bpgpassword\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\S+))",
        command,
        re.IGNORECASE,
    ):
        value = next(val for val in match.groups() if val is not None)
        if _is_literal_secret(value):
            return "literal secret: PGPASSWORD"

    if re.search(r"\bre_[A-Za-z0-9_]{16,}\b", command):
        return "literal secret: Resend API key"

    return None


def is_production_secret_read(command: str) -> bool:
    if re.search(r"\bdocker\s+inspect\b", command):
        return True
    if re.search(r"\bdocker\s+compose\b[^|;&]*\bconfig\b", command):
        return True
    if re.search(r"(?<![.\w])(?:env|printenv)\b", command):
        return re.search(r"\|\s*grep\s+-[a-z]*c\b", command) is None
    if not re.search(r"(?<![\w.-])\.env[\w.-]*\b", command):
        return False
    return re.search(r"\bgrep\s+-[a-z]*[cq][a-z]*\b", command) is None


def is_local_agent_message(command: str) -> bool:
    """Allow standalone `maestri ask "<agent>" "<text>"` when target is not VPS and no shell expansion occurs."""
    if "$(" in command or "`" in command:
        return False
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return False
    return (
        len(tokens) == 4
        and tokens[:2] == ["maestri", "ask"]
        and tokens[2].lower() != "vps"
        and not tokens[3].startswith("--")
    )


def split_heredocs(command: str) -> tuple[str, str]:
    """Separate shell command headers from heredoc bodies without treating quoted << as syntax."""
    token = re.compile(
        r"'[^']*'|\"(?:\\.|[^\"\\])*\"|\\[\s\S]|(?:^|(?<=[\s;|&()]))\#[^\n]*"
        r"|(?P<heredoc>(?<!<)<<(?P<tabs>-)?(?!<)[ \t]*"
        r"(?P<delimiter>'[^'\n]+'|\"[^\"\n]+\"|[\w]+)(?=[\s;|&<>)]|$))|(?P<newline>\n)"
    )
    headers: list[str] = []
    bodies: list[str] = []
    pending: list[tuple[str, bool]] = []
    cursor = start = 0
    while match := token.search(command, cursor):
        cursor = match.end()
        if match.group("heredoc"):
            pending.append((shlex.split(match.group("delimiter"))[0], bool(match.group("tabs"))))
        elif match.group("newline") and pending:
            headers.append(command[start:cursor])
            for delimiter, tabs in pending:
                end = re.search(
                    r"(?m)^" + (r"\t*" if tabs else "") + re.escape(delimiter) + r"\r?(?:\n|$)",
                    command[cursor:],
                )
                if end is None:
                    raise ValueError("unterminated heredoc")
                bodies.append(command[cursor : cursor + end.start()])
                cursor += end.end()
            start = cursor
            pending = []
    if pending:
        raise ValueError("missing heredoc body")
    return "".join((*headers, command[start:])), "\n".join(bodies)


def find_violation(command: str) -> str | None:
    markers = get_prod_markers()
    try:
        shell, bodies = split_heredocs(command)
        normalized = " ".join(shlex.split(shell.replace("\\\n", "")))
    except ValueError:
        return "invalid command: unable to safely parse quotes/escapes"

    body_text = bodies.replace("\\\n", "")
    try:
        normalized_body = " ".join(shlex.split(body_text))
    except ValueError:
        normalized_body = re.sub(r"['\"\\]", "", body_text)

    secret = find_secret(command) or find_secret(normalized) or find_secret(normalized_body)
    if secret is not None:
        return secret

    body_variants = (bodies + "\n" + normalized_body).lower()
    if any(marker in body_variants for marker in markers):
        return "heredoc references production"

    lowered = normalized.lower() + "\n" + body_variants
    if is_local_agent_message(command):
        return None
    if not any(marker in lowered for marker in markers):
        return None

    if is_production_secret_read(lowered):
        return "production secret read"

    for pattern, label in (*IRREVERSIBLE, *DIRECT_DATABASE_ACCESS):
        if re.search(pattern, lowered):
            return label

    if re.search(r"\bexplain\b[^;]*\banalyze\b", lowered):
        return "EXPLAIN ANALYZE outside BEGIN…ROLLBACK executes DML"

    for pattern, label in SQL_WRITES:
        if re.search(pattern, lowered):
            return label

    return None


def main() -> int:
    if os.environ.get("AGENTIC_PROD_GUARD") == "off":
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_violation(command)
    if reason is None:
        return 0

    remediation = (
        SECRET_REMEDIATION
        if reason.startswith(("literal secret:", "invalid command:"))
        else REMEDIATION
    )
    print(remediation.format(reason=reason, command=command.strip()), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Unit tests for hooks/prod-guard.py (100% English port of prod-guard.py with dynamic markers)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "prod-guard.py"

TEST_IP = "198.51.100.42"
TEST_HOST = f"deploy@{TEST_IP}"
TEST_PATH = "/opt/prod-app"
TEST_DOMAIN = "api.prod-example.com"
PROD_CMD = f"cd {TEST_PATH} && docker compose -f docker-compose.prod.yml"


def load_prod_guard():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("prod_guard", str(HOOK))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CASES: tuple[tuple[str, bool, str], ...] = (
    # --- Allowed: does not touch production ---
    ("git status", False, "local command"),
    ("docker compose up -d", False, "dev compose, not .prod.yml"),
    ("rm -rf /tmp/scratch", False, "destructive but local"),
    ("pytest -q", False, "local test suite"),
    # --- Heredocs: local body does not interfere with quote parsing ---
    *(
        (f"cat <<{delimiter}\nLead's local note\n{end}\n", False, "apostrophe in local body")
        for delimiter, end in (("EOF", "EOF"), ("'EOF'", "EOF"), ("-EOF", "\tEOF"))
    ),
    (f"cat <<'EOF'\n{TEST_HOST}\nEOF", True, "production host in heredoc body"),
    ("cat <<EOF\nPGPASSWORD=incident_password\nEOF", True, "literal secret in heredoc body"),
    ("cat <<EOF\nlocal\nEOF\necho 'broken", True, "unclosed quote after heredoc"),
    ("echo '<<EOF'\necho 'broken", True, "quoted heredoc operator is literal"),
    ("cat <<A <<'B'\nLead's first\nA\nLead's second\nB", False, "two heredoc bodies"),
    (f"cat <<EOF\nlocal\nEOF\nssh {TEST_HOST} reboot", True, "command after heredoc body"),
    (f"ssh {TEST_HOST} bash <<EOF\nreboot\nEOF", True, "remote verb inside heredoc body"),
    ("cat <<EOF\nLead's note", True, "unterminated heredoc"),
    ("cat <<EOF", True, "missing heredoc body"),
    ("echo 'literal\n<<EOF\n'", False, "heredoc marker inside multiline quotes"),
    ("echo ok # <<EOF\necho 'broken", True, "heredoc in comment is literal"),
    # --- Obfuscation normalization inside heredoc body ---
    (f'bash <<EOF\nssh 198.51.100."42" \'sudo reboot\'\nEOF', True, "quoted host"),
    (f"ssh {TEST_IP} bash <<EOF\nr''eboot\nEOF", True, "verb with empty quotes"),
    ("bash <<EOF\nssh 198.51.100.\\\n42 reboot\nEOF", True, "host with line continuation"),
    ("bash <<EOF\ndocker compose -f docker-compose.pr''od.yml down\nEOF", True, "marker with empty quotes"),
    ("bash <<EOF\nLead's note\nssh 198.51.100.\"42\" reboot\nEOF", True, "obfuscated host with apostrophe"),
    ("cat <<EOF\nLead's note\nPGPASS'WORD'=incident_password\nEOF", True, "obfuscated secret with apostrophe"),
    # --- Local agent message: text is payload, not executed ---
    (
        'maestri ask "Explorer" "ORDER · edit docker-compose.prod.yml without reading .env"',
        False,
        "message to local agent mentions prod file",
    ),
    ('maestri ask "VPS" "cat .env"', True, "message to VPS terminal"),
    (
        'maestri ask "Dev Back" --raw "docker compose -f docker-compose.prod.yml down"',
        True,
        "--raw types directly into terminal",
    ),
    (
        f'maestri ask "Dev Back" "hi"; ssh {TEST_HOST} cat {TEST_PATH}/.env',
        True,
        "message chained with remote command",
    ),
    (
        f'maestri ask "Dev Back" "$(ssh {TEST_HOST} cat {TEST_PATH}/.env)"',
        True,
        "command substitution inside message",
    ),
    (
        f'maestri ask "Dev Back" "`ssh {TEST_HOST} cat {TEST_PATH}/.env`"',
        True,
        "backticks inside message",
    ),
    # --- Allowed: env var references or standard local default credentials ---
    ("PGPASSWORD=$DATABASE_PASSWORD psql", False, "env var password"),
    ("PGPASSWORD=${DATABASE_PASSWORD} psql", False, "braced env var password"),
    ("psql postgresql://postgres:postgres@database/app", False, "standard local DSN"),
    # --- Blocked: literal secrets even without production markers ---
    ("psql postgresql://incident:incident_password@database/jobs", True, "DSN with literal password"),
    ("PGPASSWORD=incident_password psql", True, "literal PGPASSWORD"),
    ("curl -H 'Authorization: Bearer re_test_credential_1234'", True, "literal Resend key"),
    (
        f"{PROD_CMD} exec -T api python -m cli.user delete --email a@example.com --confirm-email a@example.com",
        True,
        "confirmed user delete",
    ),
    (
        f"{PROD_CMD} exec -T api python -m cli.user delete --email=a@example.com --confirm-email=a@example.com",
        True,
        "confirmed user delete with equals",
    ),
    (
        f"{PROD_CMD} exec -T api python -m cli.user reapply-deletions --journal /tmp/j.json --confirm-journal abc",
        True,
        "confirmed deletion replay",
    ),
    (
        f"{PROD_CMD} exec -T api python -m cli.user delete --email a@example.com",
        False,
        "user delete dry-run preview",
    ),
    (
        "python -m cli.user delete --email a@example.com --confirm-email a@example.com",
        False,
        "local user delete without prod marker",
    ),
    # --- Allowed: read-only production inspection without direct DB access ---
    (f'ssh {TEST_HOST} "docker ps"', False, "container listing"),
    (f'ssh {TEST_HOST} "{PROD_CMD} logs api"', False, "log reading"),
    (f'ssh {TEST_HOST} "{PROD_CMD} exec -T api python -m cli.runs"', False, "telemetry CLI in api container"),
    # --- Blocked: direct database access and SQL writes ---
    (f"ssh {TEST_HOST} \"psql -c 'select updated_at from jobs'\"", True, "direct SELECT via psql"),
    (f'ssh {TEST_HOST} "{PROD_CMD} exec -T database echo ok"', True, "exec in database container"),
    (f'ssh {TEST_HOST} "{PROD_CMD} run --rm database sh"', True, "run in database container"),
    ('maestri ask VPS "docker exec app-database-1 pg_isready"', True, "docker exec in database container"),
    # --- Allowed: counting env vars without exposing values ---
    ('maestri ask VPS "grep -c DATABASE_URL .env"', False, "count in .env"),
    ('maestri ask VPS "grep -q DATABASE_URL .env"', False, "existence check in .env"),
    ('maestri ask VPS "env | grep -c DATABASE_URL"', False, "count in env"),
    # --- Blocked: reading secrets on VPS ---
    ('maestri ask "VPS" "cat .env"', True, "reading .env"),
    ('maestri ask VPS "printenv"', True, "reading printenv"),
    ('maestri ask VPS "docker inspect api"', True, "docker inspect"),
    ('maestri ask VPS "docker compose config"', True, "resolved compose config"),
    # --- Blocked: DML, DDL, EXPLAIN ANALYZE, and irreversible commands ---
    (f"ssh {TEST_HOST} \"psql -c 'begin; explain analyze update jobs set x=1; rollback;'\"", True, "direct psql"),
    (f"ssh {TEST_HOST} \"psql -c 'update jobs set expired_at=now()'\"", True, "UPDATE"),
    (f"ssh {TEST_HOST} \"psql -c 'delete from jobs'\"", True, "DELETE"),
    (f"ssh {TEST_HOST} \"psql -c 'drop table jobs'\"", True, "DROP"),
    (f"ssh {TEST_HOST} \"psql -c 'truncate usage_events'\"", True, "TRUNCATE"),
    (f"ssh {TEST_HOST} \"psql -c 'grant all on jobs to public'\"", True, "GRANT"),
    (f"ssh {TEST_HOST} \"psql -c 'explain analyze update jobs set x=1'\"", True, "EXPLAIN ANALYZE"),
    (f'ssh {TEST_HOST} "sudo reboot"', True, "remote reboot"),
    (f'ssh {TEST_HOST} "{PROD_CMD} down"', True, "compose down"),
    (f'ssh {TEST_HOST} "{PROD_CMD} exec api alembic upgrade head"', True, "manual migration"),
    (f'ssh {TEST_HOST} "cd {TEST_PATH} && ./scripts/migrate-prod.sh"', True, "manual migrate-prod.sh"),
    (f'ssh {TEST_HOST} "rm -rf {TEST_PATH}"', True, "rm -rf deploy dir"),
    (f'ssh {TEST_HOST} "docker volume rm app_pgdata"', True, "docker volume rm"),
    # --- Blocked: quote/escape obfuscations and malformed quotes ---
    ("docker compose -f 'docker-compose.prod.yml' 'down'", True, "single-quoted verb"),
    ('docker compose -f docker-compose.prod.yml do"w"n', True, "double-quoted verb"),
    (r"docker compose -f docker-compose.prod.yml d\own", True, "escaped verb"),
    (r"docker compose -f docker-compose.pr\od.yml down", True, "escaped marker"),
    (f"{PROD_CMD} exec api p's'ql", True, "quoted psql"),
    (f"{PROD_CMD} exec api echo 'update' jobs set x=1", True, "quoted SQL"),
    (f'{PROD_CMD} exec api print"env"', True, "quoted printenv"),
    ("PGPASS'WORD'=incident_password psql", True, "quoted secret"),
    (f"{PROD_CMD} logs 'api", True, "unclosed single quote"),
    (f'{PROD_CMD} logs "api', True, "unclosed double quote"),
    (PROD_CMD + " logs api\\", True, "trailing backslash"),
    ("echo 'incomplete", True, "unclosed quote without marker"),
)


class TestProdGuardHook(unittest.TestCase):
    def setUp(self):
        self.old_markers = os.environ.get("AGENTIC_PROD_MARKERS")
        self.old_guard = os.environ.get("AGENTIC_PROD_GUARD")
        os.environ["AGENTIC_PROD_MARKERS"] = f"{TEST_IP},{TEST_PATH},{TEST_DOMAIN}"
        os.environ.pop("AGENTIC_PROD_GUARD", None)
        self.pg = load_prod_guard()

    def tearDown(self):
        if self.old_markers is None:
            os.environ.pop("AGENTIC_PROD_MARKERS", None)
        else:
            os.environ["AGENTIC_PROD_MARKERS"] = self.old_markers
        if self.old_guard is None:
            os.environ.pop("AGENTIC_PROD_GUARD", None)
        else:
            os.environ["AGENTIC_PROD_GUARD"] = self.old_guard

    def test_all_command_cases(self):
        for command, should_block, why in CASES:
            with self.subTest(why=why, command=command):
                reason = self.pg.find_violation(command)
                blocked = reason is not None
                self.assertEqual(
                    blocked,
                    should_block,
                    f"expected {'block' if should_block else 'allow'} ({why}) for: {command} (got {reason!r})",
                )

    def test_malformed_quotes_and_secret_redaction_on_stderr(self):
        for command in ("echo 'broken", "cat <<EOF\nlocal\nEOF\necho 'broken"):
            reason = self.pg.find_violation(command)
            self.assertIsNotNone(reason)
            self.assertTrue(reason.startswith("invalid command:"), reason)

        secret = "incident_password"
        res = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_input": {"command": f"psql postgresql://incident:{secret}@database/jobs"}}),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 2)
        self.assertIn("password", res.stderr.lower())
        self.assertNotIn(secret, res.stderr)

        res2 = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_input": {"command": f"echo '{secret}"}}),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res2.returncode, 2)
        self.assertNotIn(secret, res2.stderr)

    def test_board_config_markers_and_bypass_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "board.config.json")
            with open(cfg, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "production": {
                            "markers": ["docker-compose.prod.yml"],
                            "hosts": ["203.0.113.99"],
                            "domains": ["prod.custom-domain.org"],
                            "paths": ["/srv/custom-app"],
                        }
                    },
                    f,
                )
            env = {k: v for k, v in os.environ.items() if k != "AGENTIC_PROD_MARKERS"}
            env["MAESTRI_CONFIG"] = cfg

            # Blocked when citing host from board.config.json
            res = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps({"tool_input": {"command": "ssh root@203.0.113.99 'sudo reboot'"}}),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(res.returncode, 2)
            self.assertIn("BLOCKED by prod-guard", res.stderr)

            # Bypassed when AGENTIC_PROD_GUARD=off
            env["AGENTIC_PROD_GUARD"] = "off"
            res_off = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps({"tool_input": {"command": "ssh root@203.0.113.99 'sudo reboot'"}}),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(res_off.returncode, 0)


if __name__ == "__main__":
    unittest.main()

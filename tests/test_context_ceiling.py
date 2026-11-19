#!/usr/bin/env python3
"""Unit tests for hooks/context-ceiling.py (100% English port of context-ceiling.py)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "hooks" / "context-ceiling.py"
ROLE_CWD = "/workspace/projects/demo-app/.maestri/roles/6898fa1e-bfe8-4c9c-8870-b33a03f2eb60"
PROJ_CWD = "/workspace/projects/demo-app"


class TestContextCeilingHook(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def run_hook(
        self,
        ctx: int,
        cwd: str,
        tool: str = "Read",
        tool_input: dict | None = None,
        socket: bool = False,
        mode: str | None = None,
        session: str = "s1",
        project: str | None = None,
        state: str | None = None,
    ) -> dict | None:
        tr = os.path.join(self.tmp, f"{session}.jsonl")
        with open(tr, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": 1,
                                "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": ctx - 1,
                            }
                        },
                    }
                )
                + "\n"
            )
        env = {k: v for k, v in os.environ.items() if not k.startswith("MAESTRI_")}
        env.pop("CLAUDE_PROJECT_DIR", None)
        env["MAESTRI_CONTEXT_STATE"] = state or self.tmp
        if project:
            env["CLAUDE_PROJECT_DIR"] = project
        if socket:
            env["MAESTRI_SOCKET"] = "/tmp/fake.sock"
        if mode:
            env["MAESTRI_CONTEXT_MANAGER_MODE"] = mode
        data = {
            "cwd": cwd,
            "tool_name": tool,
            "tool_input": tool_input or {"file_path": "/x"},
            "transcript_path": tr,
            "session_id": session,
        }
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertTrue(not r.stderr or state is not None, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None

    @staticmethod
    def decision(output: dict | None) -> str | None:
        return output.get("permissionDecision") if output else None

    def test_thresholds_warnings_and_denials(self):
        # Below warning threshold passes silently
        self.assertIsNone(self.run_hook(150_000, ROLE_CWD))

        # Warning fires once per session between 170k and 200k
        warn_out = self.run_hook(175_000, ROLE_CWD, session="w")
        self.assertIsNotNone(warn_out)
        self.assertIn("Context warning", warn_out["additionalContext"])
        self.assertIsNone(self.run_hook(176_000, ROLE_CWD, session="w"))

        # Role above 200k is denied; exact 200k is not denied
        self.assertEqual(self.decision(self.run_hook(200_001, ROLE_CWD)), "deny")
        self.assertIsNone(self.decision(self.run_hook(200_000, ROLE_CWD, session="eq")))

    def test_exemptions_for_maestri_order_and_runs(self):
        # Single maestri command is exempt
        self.assertNotEqual(
            self.decision(
                self.run_hook(200_001, ROLE_CWD, "Bash", {"command": "maestri ask Manager x"}, session="m")
            ),
            "deny",
        )
        # Write/MultiEdit inside planning/.../runs/ is exempt
        self.assertNotEqual(
            self.decision(
                self.run_hook(
                    200_001,
                    ROLE_CWD,
                    "Write",
                    {"file_path": "/workspace/planning/demo-app/runs/213/x.md"},
                    session="r",
                )
            ),
            "deny",
        )
        self.assertNotEqual(
            self.decision(
                self.run_hook(
                    200_001,
                    ROLE_CWD,
                    "MultiEdit",
                    {"file_path": "/workspace/planning/demo-app/runs/x.md"},
                    session="me",
                )
            ),
            "deny",
        )
        # Path traversal out of runs/ or non-planning /src/runs/ or relative runs/ is denied
        self.assertEqual(
            self.decision(
                self.run_hook(200_001, ROLE_CWD, "Write", {"file_path": "/a/runs/../src/x.py"}, session="r2")
            ),
            "deny",
        )
        for bad_path in ("/repo/src/runs/x.py", "runs/x.md"):
            self.assertEqual(
                self.decision(
                    self.run_hook(200_001, ROLE_CWD, "Write", {"file_path": bad_path}, session="f")
                ),
                "deny",
                bad_path,
            )

        # Chained or spoofed maestri commands are denied
        self.assertEqual(
            self.decision(self.run_hook(200_001, ROLE_CWD, "Bash", {"command": "echo maestri "}, session="b")),
            "deny",
        )
        for cmd in (
            "maestri ask x; cat big.log",
            "maestri ask x && ls",
            "maestri ask $(cat f)",
            "maestri ask x | tee f",
        ):
            self.assertEqual(
                self.decision(self.run_hook(200_001, ROLE_CWD, "Bash", {"command": cmd}, session="c")),
                "deny",
                cmd,
            )

        # scripts/order.py is exempt when unchained
        order_cmd = "python3 /workspace/projects/agentic-factory/scripts/order.py"
        self.assertNotEqual(
            self.decision(
                self.run_hook(
                    200_001,
                    ROLE_CWD,
                    "Bash",
                    {"command": f"{order_cmd} report --prd 213 --id x"},
                    session="o",
                )
            ),
            "deny",
        )
        for cmd in (
            f"{order_cmd} report x; rm -rf /tmp/x",
            f"{order_cmd} x && ls",
            "python3 /tmp/order.py report x",
            f"{order_cmd}x report",
        ):
            self.assertEqual(
                self.decision(self.run_hook(200_001, ROLE_CWD, "Bash", {"command": cmd}, session="o2")),
                "deny",
                cmd,
            )

    def test_manager_modes_and_audit_log(self):
        # Changing directory inside role cannot escape CLAUDE_PROJECT_DIR
        self.assertEqual(
            self.decision(self.run_hook(200_001, PROJ_CWD, project=ROLE_CWD, session="cd")),
            "deny",
        )
        # Unwritable log dir still enforces deny
        self.assertEqual(
            self.decision(self.run_hook(200_001, ROLE_CWD, session="ro", state="/proc/nope")),
            "deny",
        )
        # Project cwd outside Maestri is ignored
        self.assertIsNone(self.run_hook(300_000, PROJ_CWD, session="p0"))

        # Manager in log mode warns and logs would-deny without blocking
        mgr_out = self.run_hook(200_001, PROJ_CWD, socket=True, session="p1")
        self.assertIsNone(self.decision(mgr_out))
        self.assertIn("Context warning", mgr_out["additionalContext"])

        # Manager in deny mode blocks
        self.assertEqual(
            self.decision(self.run_hook(200_001, PROJ_CWD, socket=True, mode="deny", session="p2")),
            "deny",
        )

        # Verify audit log contains all action types
        self.run_hook(175_000, ROLE_CWD, session="log_warn")
        self.run_hook(200_001, ROLE_CWD, "Bash", {"command": "maestri ask Manager ok"}, session="log_ex")
        log_path = Path(self.tmp) / "context-ceiling.jsonl"
        entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        actions = {e["action"] for e in entries}
        self.assertTrue({"warn", "deny", "exempt", "would-deny"} <= actions, actions)
        self.assertTrue(any(e["kind"] == "manager" and e["action"] == "would-deny" for e in entries))


if __name__ == "__main__":
    unittest.main()

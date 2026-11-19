#!/usr/bin/env python3
"""Unit tests for scripts/order.py (100% English port of ordem.py)."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "scripts" / "order.py"
AUTH_QUOTE = "#213 (Front lane) in parallel, exception to the single-lane rule"


def git_commit(repo: str, msg: str) -> str:
    subprocess.run(
        [
            "git",
            "-C",
            repo,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            msg,
        ],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", repo, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def read_json_block(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text.split("```json\n")[1].split("\n```")[0])


class TestOrderScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="order-test-")
        self.runs = os.path.join(self.tmp, "runs")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.runs, "213"))
        os.makedirs(self.repo)
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        git_commit(self.repo, "initial commit before ORDER")
        auth_file = os.path.join(self.runs, "213", "authorization.md")
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write(
                f'- Lead 15/11 evening: "{AUTH_QUOTE}"\n'
                '- Lead: "do not authorize #212 or sprint queue automatically"\n'
            )
        self.base_args = ["--prd", "213", "--id", "213-C", "--owner", "Dev Front"]
        self.open_args = [
            "open",
            *self.base_args,
            "--scope",
            "Phase C",
            "--authorization",
            AUTH_QUOTE,
            "--repo",
            self.repo,
        ]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_order(self, *args, runs_dir=None, extra_env=None, cwd=None):
        env = dict(os.environ)
        if runs_dir is not None:
            env["MAESTRI_RUNS"] = runs_dir
        else:
            env["MAESTRI_RUNS"] = self.runs
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
            check=False,
        )

    def assert_ok(self, res):
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res.stdout

    def assert_fail(self, res, text, code=None):
        self.assertNotEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn(text, res.stdout + res.stderr)
        if code is not None:
            self.assertEqual(res.returncode, code)

    def test_authorization_gate_and_closed_quotes(self):
        # Unquoted or partial fragments must be rejected without creating folders
        self.assert_fail(
            self.run_order(
                "open",
                "--prd",
                "212",
                "--id",
                "212-PF",
                "--owner",
                "Rollout",
                "--scope",
                "preflight",
                "--authorization",
                "sprint queue",
                "--repo",
                self.repo,
            ),
            "unauthorized",
        )
        for frag in ("a", "authorize", "#213 (Front lane)", "#212 or sprint queue"):
            self.assert_fail(
                self.run_order(
                    "open",
                    *self.base_args,
                    "--scope",
                    "Phase C",
                    "--authorization",
                    frag,
                    "--repo",
                    self.repo,
                ),
                "unauthorized",
            )
        self.assertFalse(os.path.exists(os.path.join(self.runs, "212")))

        # [closed] line must be rejected even if the quote matches
        auth_file = os.path.join(self.runs, "213", "authorization.md")
        with open(auth_file, "a", encoding="utf-8") as f:
            f.write('- [closed] Lead: "copy approved, you may apply it now"\n')
        self.assert_fail(
            self.run_order(
                "open",
                "--prd",
                "213",
                "--id",
                "213-COPY",
                "--owner",
                "Dev Front",
                "--scope",
                "copy",
                "--authorization",
                "copy approved, you may apply it now",
                "--repo",
                self.repo,
            ),
            "unauthorized",
        )

    def test_full_lifecycle_reconcile_and_concurrency(self):
        # Open order; duplicate open with identical owner/scope is idempotent
        order_path = self.assert_ok(self.run_order(*self.open_args)).strip()
        self.assert_ok(self.run_order("check", order_path))
        self.assertIn("already exists", self.assert_ok(self.run_order(*self.open_args)))

        # Different owner with same ID fails
        self.assert_fail(
            self.run_order(
                "open",
                "--prd",
                "213",
                "--id",
                "213-C",
                "--owner",
                "Dev Back",
                "--scope",
                "Phase C",
                "--authorization",
                AUTH_QUOTE,
                "--repo",
                self.repo,
            ),
            "already exists",
        )
        # Wrong owner cannot start
        self.assert_fail(
            self.run_order("start", "--prd", "213", "--id", "213-C", "--owner", "QA"),
            "belongs to 'Dev Front'",
        )

        # Reconcile pending
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 1)
        self.assertIn("pending: not started", rec.stdout)

        # Start order
        self.assert_ok(self.run_order("start", *self.base_args))

        # Simulated lost session after commit + ceiling fallback file
        c1 = git_commit(self.repo, "feat: phase C")
        ceiling_path = os.path.join(self.runs, "213", "report-213-C-ceiling.md")
        Path(ceiling_path).write_text("REPORT 213-C · partial · ceiling\n", encoding="utf-8")
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 2)
        self.assertIn("lost session", rec.stdout)
        self.assertIn("report-213-C-ceiling.md", rec.stdout)

        # Partial report recording the commit clears the unreported commit error
        self.assert_ok(
            self.run_order(
                "report",
                *self.base_args,
                "--status",
                "partial",
                "--evidence",
                "c.log",
                "--next",
                "tests · Dev Front",
                "--effect",
                f"Commit:{c1[:7]}",
            )
        )
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 1)
        self.assertNotIn("lost session", rec.stdout)
        self.assertIn(f"commit:{c1[:7]}", rec.stdout)

        # Complete order
        out = self.assert_ok(
            self.run_order(
                "report",
                *self.base_args,
                "--status",
                "completed",
                "--evidence",
                "runs/213/c.log",
                "--next",
                "QA Phase C · QA",
            )
        )
        self.assertTrue(
            out.startswith(
                "REPORT 213-C · Status: completed · Evidence: runs/213/c.log · Next: QA Phase C · QA"
            ),
            out,
        )
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 0)
        self.assertIn(f"do not repeat: commit:{c1[:7]}", rec.stdout)
        data = read_json_block(order_path)
        self.assertEqual(data["revision"], c1[: len(data["revision"])])

        # Duplicate identical report is a no-op; conflicting report on final status fails
        same = [
            "report",
            *self.base_args,
            "--status",
            "completed",
            "--evidence",
            "runs/213/c.log",
            "--next",
            "QA Phase C · QA",
        ]
        self.assertIn("no changes", self.assert_ok(self.run_order(*same)))
        self.assert_fail(
            self.run_order(*same, "--effect", "deploy:v9"),
            "already completed",
        )
        self.assert_fail(
            self.run_order(
                "report",
                *self.base_args,
                "--status",
                "partial",
                "--evidence",
                "x",
                "--next",
                "y",
            ),
            "already completed",
        )

        # Resuming from completed order inherits effects; resuming from non-final order fails
        p2 = self.assert_ok(
            self.run_order(
                "open",
                "--prd",
                "213",
                "--id",
                "213-C.2",
                "--owner",
                "Dev Front",
                "--scope",
                "item 10",
                "--authorization",
                AUTH_QUOTE,
                "--repo",
                self.repo,
                "--resumes",
                "213-C",
            )
        ).strip()
        self.assertIn(
            f"do not repeat: commit:{c1[:7]}",
            self.run_order("reconcile", "--prd", "213").stdout,
        )
        self.assert_fail(
            self.run_order(
                "open",
                "--prd",
                "213",
                "--id",
                "213-C.3",
                "--owner",
                "Dev Back",
                "--scope",
                "item 10",
                "--authorization",
                AUTH_QUOTE,
                "--repo",
                self.repo,
                "--resumes",
                "213-C.2",
            ),
            "still pending",
        )

        # Parallel reports serialize via .order.lock without losing effects
        self.assert_ok(
            self.run_order("start", "--prd", "213", "--id", "213-C.2", "--owner", "Dev Front")
        )
        self.assert_fail(
            self.run_order(
                "report",
                "--prd",
                "213",
                "--id",
                "213-C.2",
                "--owner",
                "Dev Front",
                "--status",
                "partial",
                "--evidence",
                "x",
                "--next",
                "y",
                "--effect",
                "migrate:1",
            ),
            "invalid effect",
        )
        rep_args = [
            "report",
            "--prd",
            "213",
            "--id",
            "213-C.2",
            "--owner",
            "Dev Front",
            "--status",
            "partial",
            "--evidence",
            "x",
            "--next",
            "y · Dev Front",
        ]
        with ThreadPoolExecutor(12) as ex:
            list(
                ex.map(
                    lambda i: self.assert_ok(
                        self.run_order(*rep_args, "--effect", f"workflow:run{i}")
                    ),
                    range(12),
                )
            )
        effects = read_json_block(p2)["effects"]
        self.assertEqual(sum(e["type"] == "workflow" for e in effects), 12)

        # Tamper detection & integrity checks
        original_txt = Path(p2).read_text(encoding="utf-8")
        Path(p2).write_text(
            original_txt.replace('"item 10"', '"entire Phase C"'),
            encoding="utf-8",
        )
        self.assert_fail(self.run_order("check", p2), "sha mismatch")
        self.assert_fail(
            self.run_order("start", "--prd", "213", "--id", "213-C.2", "--owner", "Dev Front"),
            "invalid",
        )
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 2)
        self.assertIn("do not dispatch anything", rec.stdout)

        Path(p2).write_text("```json\n[1]\n```\n", encoding="utf-8")
        self.assert_fail(self.run_order("check", p2), "not an object")
        self.assertEqual(self.run_order("reconcile", "--prd", "213").returncode, 2)

        Path(p2).write_text(original_txt, encoding="utf-8")
        renamed = os.path.join(self.runs, "213", "order-213-X.md")
        shutil.copy(p2, renamed)
        self.assert_fail(self.run_order("check", renamed), "does not match filename")
        os.remove(renamed)

        self.assert_fail(
            self.run_order(
                "report",
                "--prd",
                "213",
                "--id",
                "213-C.2",
                "--owner",
                "Dev Front",
                "--status",
                "done",
                "--evidence",
                "x",
                "--next",
                "y",
            ),
            "invalid REPORT status",
        )
        self.assert_fail(
            self.run_order(
                "open",
                "--prd",
                "../etc",
                "--id",
                "x",
                "--owner",
                "a",
                "--scope",
                "b",
                "--authorization",
                AUTH_QUOTE,
                "--repo",
                self.repo,
            ),
            "invalid",
        )
        shutil.rmtree(os.path.join(self.repo, ".git"))
        rec = self.run_order("reconcile", "--prd", "213")
        self.assertEqual(rec.returncode, 2)
        self.assertIn("unreadable repo", rec.stdout)

    def test_board_config_runs_dir_resolution(self):
        cfg_dir = os.path.join(self.tmp, "cfg_proj")
        custom_runs = os.path.join(self.tmp, "custom_runs")
        os.makedirs(cfg_dir)
        os.makedirs(os.path.join(custom_runs, "99"))
        with open(os.path.join(cfg_dir, "board.config.json"), "w", encoding="utf-8") as f:
            json.dump({"paths": {"runs_dir": custom_runs}}, f)

        env = {k: v for k, v in os.environ.items() if k != "MAESTRI_RUNS"}
        res = subprocess.run(
            [sys.executable, str(TOOL), "reconcile", "--prd", "99"],
            capture_output=True,
            text=True,
            env=env,
            cwd=cfg_dir,
            check=False,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("#99: no ORDER files on disk", res.stdout)


if __name__ == "__main__":
    unittest.main()

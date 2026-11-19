#!/usr/bin/env python3
"""Unit tests for scripts/qa-proof.py (100% English port of qa-proof.py)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "scripts" / "qa-proof.py"


class TestQaProofScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="qa-proof-test-")
        self.work = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.work, "server"), exist_ok=True)
        os.makedirs(os.path.join(self.work, "web"), exist_ok=True)
        self.sh(["git", "init", "-q", "-b", "main"], self.work)

        Path(self.work, "server", "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        Path(self.work, "server", "uv.lock").write_text("lock-v1\n", encoding="utf-8")
        Path(self.work, "web", "package.json").write_text(
            '{"name": "web", "version": "1.0.0"}\n', encoding="utf-8"
        )
        Path(self.work, "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        Path(self.work, "server", "app.py").write_text("x = 1\n", encoding="utf-8")
        self.sh(["git", "add", "."], self.work)
        self.commit("commit A")
        self.commit_a = self.sh(["git", "rev-parse", "HEAD"], self.work).stdout.strip()

        Path(self.work, "server", "app.py").write_text("x = 2\n", encoding="utf-8")
        self.sh(["git", "add", "."], self.work)
        self.commit("commit B")
        self.commit_b = self.sh(["git", "rev-parse", "HEAD"], self.work).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sh(self, cmd, cwd, check=True):
        res = subprocess.run(
            cmd,
            cwd=cwd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            check=False,
        )
        if check and res.returncode != 0:
            raise AssertionError(f"{cmd}: {res.stderr}")
        return res

    def commit(self, msg: str):
        self.sh(
            [
                "git",
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
            self.work,
        )

    def record_proof(self, cwd, *extra):
        out = self.sh(
            [sys.executable, str(TOOL), "record", "--prd", "209", "--order", "209-T", *extra],
            cwd,
        ).stdout
        return json.loads(out)

    def verify_proof(self, cwd, path):
        res = self.sh([sys.executable, str(TOOL), "verify", path], cwd, check=False)
        return res.returncode, json.loads(res.stdout)

    def test_distinguishes_clean_commits_and_verifies_tree_state(self):
        # Checkout commit A and record proof
        self.sh(["git", "checkout", "-q", "--detach", self.commit_a], self.work)
        proof_a = self.record_proof(self.work)

        # Checkout commit B and record proof with command
        self.sh(["git", "checkout", "-q", "main"], self.work)
        proof_b = self.record_proof(self.work, "--", "true")

        # 1. Distinct clean commits have distinct proof IDs and trees, with dirty_sha256 = None
        self.assertNotEqual(proof_a["id"], proof_b["id"])
        self.assertNotEqual(proof_a["tree"], proof_b["tree"])
        self.assertIsNone(proof_a["dirty_sha256"])
        self.assertIsNone(proof_b["dirty_sha256"])

        # 2. Auto-discovered lockfiles and Dockerfiles are present in deps
        self.assertIn("server/uv.lock", proof_b["deps"])
        self.assertIn("server/pyproject.toml", proof_b["deps"])
        self.assertIn("web/package.json", proof_b["deps"])
        self.assertIn("docker-compose.yml", proof_b["deps"])

        # 3. Proof for current commit is valid; proof for older commit is invalid
        pb = os.path.join(self.tmp, "b.json")
        Path(pb).write_text(json.dumps(proof_b), encoding="utf-8")
        code, res = self.verify_proof(self.work, pb)
        self.assertEqual(code, 0)
        self.assertTrue(res["valid"])

        pa = os.path.join(self.tmp, "a.json")
        Path(pa).write_text(json.dumps(proof_a), encoding="utf-8")
        code, res = self.verify_proof(self.work, pa)
        self.assertEqual(code, 1)
        self.assertIn("commit", res["changed"])
        self.assertIn("tree", res["changed"])

        # 4. Dirty working tree changes proof and invalidates clean proof
        with open(os.path.join(self.work, "server", "pyproject.toml"), "a", encoding="utf-8") as f:
            f.write("\n# dirty comment\n")
        dirty = self.record_proof(self.work)
        self.assertIsNotNone(dirty["dirty_sha256"])
        self.assertNotEqual(dirty["id"], proof_b["id"])
        code, res = self.verify_proof(self.work, pb)
        self.assertEqual(code, 1)
        self.assertEqual(res["changed"], ["dirty_sha256"])
        self.sh(["git", "checkout", "-q", "--", "."], self.work)

        # Untracked file modification also invalidates clean proof
        untracked = os.path.join(self.work, "untracked.txt")
        Path(untracked).write_text("v1\n", encoding="utf-8")
        code, res = self.verify_proof(self.work, pb)
        self.assertEqual(code, 1)
        self.assertIn("dirty_sha256", res["changed"])
        os.remove(untracked)

        # 5. Different command produces different proof ID on identical code
        c1 = self.record_proof(self.work, "--", "true")
        c2 = self.record_proof(self.work, "--", "true", "x")
        self.assertNotEqual(c1["id"], c2["id"])
        self.assertEqual(c1["result"]["exit_code"], 0)

        # 6. Dependency lockfile change produces different deps and proof ID
        self.commit("noop")
        same_deps = self.record_proof(self.work)
        self.assertEqual(same_deps["deps"], proof_b["deps"])
        with open(os.path.join(self.work, "server", "uv.lock"), "a", encoding="utf-8") as f:
            f.write("lock-v2\n")
        self.sh(["git", "add", "server/uv.lock"], self.work)
        self.commit("update lock")
        lock_proof = self.record_proof(self.work)
        self.assertNotEqual(
            lock_proof["deps"]["server/uv.lock"], proof_b["deps"]["server/uv.lock"]
        )
        self.assertNotEqual(lock_proof["id"], same_deps["id"])

        # 7. Non-executed gates require a reason and appear in verify output
        bad_gate = self.sh(
            [
                sys.executable,
                str(TOOL),
                "record",
                "--prd",
                "209",
                "--order",
                "x",
                "--gate",
                "mutations=blocked",
            ],
            self.work,
            check=False,
        )
        self.assertNotEqual(bad_gate.returncode, 0)
        self.assertIn("without reason", bad_gate.stderr)

        g = self.record_proof(
            self.work,
            "--gate",
            "A2=executed",
            "--gate",
            "mutations=blocked:permission denied",
            "--gate",
            "B=waived:backend only",
            "--",
            "true",
        )
        pg = os.path.join(self.tmp, "g.json")
        Path(pg).write_text(json.dumps(g), encoding="utf-8")
        code, res = self.verify_proof(self.work, pg)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(res["unexecuted_gates"].keys()), ["B", "mutations"])

        # 8. Manually tampered proof fails verification
        g["commit"] = self.commit_a
        Path(pg).write_text(json.dumps(g), encoding="utf-8")
        code, res = self.verify_proof(self.work, pg)
        self.assertEqual(code, 1)
        self.assertTrue(any("id" in c for c in res["changed"]))

        # 9. Red suite or proof without command execution fails verification
        pr = os.path.join(self.tmp, "r.json")
        red = self.sh(
            [
                sys.executable,
                str(TOOL),
                "record",
                "--prd",
                "209",
                "--order",
                "x",
                "--out",
                pr,
                "--",
                "false",
            ],
            self.work,
            check=False,
        )
        self.assertEqual(red.returncode, 1)
        code, res = self.verify_proof(self.work, pr)
        self.assertEqual(code, 1)
        self.assertTrue(any("result" in c for c in res["changed"]))

        Path(pr).write_text(json.dumps(self.record_proof(self.work)), encoding="utf-8")
        code, res = self.verify_proof(self.work, pr)
        self.assertEqual(code, 1)
        self.assertTrue(any("result" in c for c in res["changed"]))

        # 10. Suite that dirties the working tree fails during record
        dirty_cmd = self.sh(
            [
                sys.executable,
                str(TOOL),
                "record",
                "--prd",
                "209",
                "--order",
                "x",
                "--",
                "touch",
                "generated.txt",
            ],
            self.work,
            check=False,
        )
        self.assertNotEqual(dirty_cmd.returncode, 0)
        self.assertIn("modified the working tree", dirty_cmd.stderr)
        os.remove(os.path.join(self.work, "generated.txt"))

        # 11. Running record in a subdirectory yields the same proof identity as root
        sub_proof = self.record_proof(os.path.join(self.work, "server"), "--", "true")
        root_proof = self.record_proof(self.work, "--", "true")
        self.assertEqual(sub_proof["id"], root_proof["id"])


if __name__ == "__main__":
    unittest.main()

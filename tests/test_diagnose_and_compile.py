import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FACTORY_ROOT = Path(__file__).resolve().parent.parent
DIAGNOSE_SCRIPT = FACTORY_ROOT / "scripts" / "diagnose.py"
COMPILE_SCRIPT = FACTORY_ROOT / "scripts" / "compile-board.py"
BOARD_DIR = FACTORY_ROOT / "board"


class TestDiagnoseScript(unittest.TestCase):
    def run_diagnose(self, repo_path: Path, mock_clis: str) -> dict:
        env = os.environ.copy()
        env["AGENTIC_MOCK_CLIS"] = mock_clis
        res = subprocess.run(
            [sys.executable, str(DIAGNOSE_SCRIPT), "--repo", str(repo_path), "--json"],
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return json.loads(res.stdout)

    def test_diagnose_single_harness_and_single_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "my-app"
            repo.mkdir()
            (repo / ".git").mkdir()
            (repo / "pyproject.toml").write_text('[project]\nname = "my-app"\n', encoding="utf-8")
            (repo / "uv.lock").write_text("version = 1\n", encoding="utf-8")

            report = self.run_diagnose(repo, "maestri,claude")
            self.assertEqual(report["routing_mode"], "single-harness")
            self.assertEqual(report["installed_ai_clis"], ["claude"])
            self.assertTrue(report["maestri_installed"])
            self.assertEqual(report["topology_recommendation"], "single-repo")
            self.assertFalse(report["is_monorepo"])
            self.assertIn("uv.lock", report["lockfiles"])
            self.assertIn("pyproject.toml", report["lockfiles"])
            self.assertFalse(report["has_ui"])

    def test_diagnose_multi_harness_and_workspace_monorepo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "planning").mkdir()
            repo = ws / "projects" / "full-app"
            (repo / "web").mkdir(parents=True)
            (repo / "server").mkdir(parents=True)
            (repo / ".git").mkdir()
            (repo / "web" / "package.json").write_text(
                json.dumps({"dependencies": {"react": "^19.0.0", "tailwindcss": "^4.0.0"}}),
                encoding="utf-8",
            )
            (repo / "web" / "package-lock.json").write_text("{}", encoding="utf-8")
            (repo / "server" / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")

            report = self.run_diagnose(repo, "maestri,claude,codex,agy")
            self.assertEqual(report["routing_mode"], "multi-harness")
            self.assertEqual(sorted(report["installed_ai_clis"]), ["agy", "claude", "codex"])
            self.assertEqual(report["topology_recommendation"], "workspace")
            self.assertTrue(report["is_monorepo"])
            self.assertTrue(report["split_dev_recommended"])
            self.assertTrue(report["has_ui"])
            self.assertIn("web/package-lock.json", report["lockfiles"])
            self.assertIn("server/pyproject.toml", report["lockfiles"])


class TestCompileBoardScript(unittest.TestCase):
    def test_check_budgets_passes_on_repository_board(self):
        res = subprocess.run(
            [sys.executable, str(COMPILE_SCRIPT), "--check-budgets"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Budget check failed:\n{res.stdout}\n{res.stderr}")

    def test_check_budgets_fails_when_exceeded(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_board = Path(tmp) / "board"
            bad_board.mkdir()
            for f in BOARD_DIR.glob("*.md"):
                (bad_board / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            # Bloat core.md beyond 500 words
            (bad_board / "core.md").write_text(" ".join(["word"] * 520), encoding="utf-8")

            res = subprocess.run(
                [sys.executable, str(COMPILE_SCRIPT), "--check-budgets", "--board-dir", str(bad_board)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("core.md", res.stdout + res.stderr)

    def test_compile_single_harness_core_roles_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            out_dir = ws / ".maestri"
            config = {
                "project_name": "solo-app",
                "language": "en",
                "topology": "workspace",
                "paths": {
                    "workspace_root": str(ws),
                    "project_dir": str(ws / "projects" / "solo-app"),
                    "planning_dir": str(ws / "planning" / "solo-app"),
                    "runs_dir": str(ws / "planning" / "solo-app" / "runs"),
                    "board_dir": str(out_dir / "board"),
                },
                "maestri": {"workspace_name": "solo-app", "group": "Boards"},
                "roles": {
                    "core": ["Manager", "Explorer", "Dev", "QA"],
                    "split_dev": False,
                    "enable_designer": False,
                    "enable_writer": False,
                    "enable_rollout": False,
                    "enable_blind_reviewer": False,
                },
                "routing": {
                    "mode": "single-harness",
                    "installed_clis": ["claude"],
                    "assignments": {},
                },
            }
            cfg_path = ws / "board.config.json"
            cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            res = subprocess.run(
                [sys.executable, str(COMPILE_SCRIPT), "--config", str(cfg_path), "--out", str(out_dir)],
                capture_output=True,
                text=True,
                check=True,
            )
            recruit_sh = (out_dir / "board" / "recruit.sh").read_text(encoding="utf-8")
            assemble_sh = (out_dir / "board" / "assemble-roles.sh").read_text(encoding="utf-8")

            # Must only use claude, never codex or agy
            self.assertIn("claude", recruit_sh)
            self.assertNotIn("codex", recruit_sh)
            self.assertNotIn("agy", recruit_sh)

            # Must include core roles and unified Dev, not optional disabled roles
            self.assertIn('"Explorer"', recruit_sh)
            self.assertIn('"Dev"', recruit_sh)
            self.assertIn('"QA"', recruit_sh)
            self.assertNotIn('"Designer"', recruit_sh)
            self.assertNotIn('"Writer"', recruit_sh)
            self.assertNotIn('"Rollout"', recruit_sh)
            self.assertNotIn('"Reviewer"', recruit_sh)
            self.assertNotIn('"Dev Front"', recruit_sh)

            # Assemble roles script includes only enabled roles
            self.assertIn("manager:Manager", assemble_sh)
            self.assertIn("explorer:Explorer", assemble_sh)
            self.assertIn("qa:QA", assemble_sh)
            self.assertNotIn("designer:Designer", assemble_sh)
            self.assertNotIn("Rollout", assemble_sh)

            # Planning scaffold created
            planning_dir = ws / "planning" / "solo-app"
            self.assertTrue((planning_dir / "progress.md").is_file())
            self.assertTrue((planning_dir / "history.md").is_file())
            self.assertTrue((planning_dir / "_template_prd.md").is_file())
            self.assertTrue((planning_dir / "project-sheet.md").is_file())

    def test_compile_multi_harness_split_dev_and_single_repo_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "app-repo"
            (repo / ".git" / "info").mkdir(parents=True)
            out_dir = repo / ".maestri"
            # In single-repo mode with planning inside repo, compile-board must isolate it in .git/info/exclude
            planning_inside = repo / "planning" / "app-repo"
            config = {
                "project_name": "app-repo",
                "language": "pt-BR",
                "topology": "single-repo",
                "paths": {
                    "workspace_root": str(repo),
                    "project_dir": str(repo),
                    "planning_dir": str(planning_inside),
                    "runs_dir": str(planning_inside / "runs"),
                    "board_dir": str(out_dir / "board"),
                },
                "maestri": {"workspace_name": "app-repo", "group": "Boards"},
                "roles": {
                    "core": ["Manager", "Explorer", "Dev", "QA"],
                    "split_dev": True,
                    "dev_front_dir": str(repo / "web"),
                    "dev_back_dir": str(repo / "server"),
                    "enable_designer": True,
                    "enable_writer": True,
                    "enable_rollout": True,
                    "enable_blind_reviewer": True,
                },
                "routing": {
                    "mode": "multi-harness",
                    "installed_clis": ["claude", "codex", "agy"],
                },
            }
            cfg_path = repo / "board.config.json"
            cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            subprocess.run(
                [sys.executable, str(COMPILE_SCRIPT), "--config", str(cfg_path), "--out", str(out_dir)],
                capture_output=True,
                text=True,
                check=True,
            )

            recruit_sh = (out_dir / "board" / "recruit.sh").read_text(encoding="utf-8")
            self.assertIn('"Dev Front"', recruit_sh)
            self.assertIn('"Dev Back"', recruit_sh)
            self.assertIn('"Designer"', recruit_sh)
            self.assertIn('"Writer"', recruit_sh)
            self.assertIn('"Rollout"', recruit_sh)
            self.assertIn('"Reviewer"', recruit_sh)
            self.assertIn("codex", recruit_sh)
            self.assertIn("agy", recruit_sh)
            self.assertIn("claude", recruit_sh)

            # Check placeholder substitution in compiled core.md
            compiled_core = (out_dir / "board" / "core.md").read_text(encoding="utf-8")
            self.assertIn("pt-BR", compiled_core)
            self.assertNotIn("{{LANGUAGE}}", compiled_core)
            self.assertNotIn("{{WORKSPACE_ROOT}}", compiled_core)

            # Single-repo isolation: .git/info/exclude must contain planning exclusion
            exclude_text = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("planning", exclude_text)

    def test_install_skills_project_and_global_with_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            ws.mkdir()
            fake_home = Path(tmp) / "home"
            fake_home.mkdir()

            # Pre-create an existing skill file in fake_home to verify non-destructive backup
            existing_skill_dir = fake_home / ".claude" / "skills" / "init-board"
            existing_skill_dir.mkdir(parents=True)
            (existing_skill_dir / "SKILL.md").write_text("old custom skill", encoding="utf-8")

            out_dir = ws / ".maestri"
            config = {
                "project_name": "skill-test",
                "language": "en",
                "topology": "workspace",
                "paths": {
                    "workspace_root": str(ws),
                    "project_dir": str(ws / "projects" / "skill-test"),
                    "planning_dir": str(ws / "planning" / "skill-test"),
                    "runs_dir": str(ws / "planning" / "skill-test" / "runs"),
                    "board_dir": str(out_dir / "board"),
                },
                "roles": {"core": ["Manager", "Explorer", "Dev", "QA"], "split_dev": False},
                "routing": {"mode": "single-harness", "installed_clis": ["claude"]},
            }
            cfg_path = ws / "board.config.json"
            cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            # 1. Install skills at project level
            subprocess.run(
                [
                    sys.executable,
                    str(COMPILE_SCRIPT),
                    "--config",
                    str(cfg_path),
                    "--out",
                    str(out_dir),
                    "--install-skills",
                    "project",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue((ws / ".claude" / "skills" / "init-board" / "SKILL.md").exists())
            self.assertTrue((ws / ".agents" / "skills" / "init-board" / "SKILL.md").exists())

            # 2. Install skills at global level with --home-dir override
            subprocess.run(
                [
                    sys.executable,
                    str(COMPILE_SCRIPT),
                    "--config",
                    str(cfg_path),
                    "--out",
                    str(out_dir),
                    "--install-skills",
                    "global",
                    "--home-dir",
                    str(fake_home),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue((fake_home / ".claude" / "skills" / "init-board").is_symlink())
            self.assertTrue((fake_home / ".agents" / "skills" / "init-board").is_symlink())
            self.assertTrue((fake_home / ".gemini" / "config" / "skills" / "init-board").is_symlink())

            # Verify backup of pre-existing init-board was created
            backups = list((fake_home / ".claude" / "skills").glob("init-board.bak*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "SKILL.md").read_text(encoding="utf-8"), "old custom skill")


if __name__ == "__main__":
    unittest.main()

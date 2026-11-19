import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "sync-status.py"


class TestSyncStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ws = self.root / "ws"
        self.home = self.root / "home"
        self.repo = self.ws / "projects" / "agentic-factory"
        (self.ws / ".maestri" / "board").mkdir(parents=True)
        (self.home / ".claude" / "skills" / "grill-me").mkdir(parents=True)
        (self.repo / "board").mkdir(parents=True)
        (self.repo / "skills" / "grill-me").mkdir(parents=True)

        self.up_core = self.ws / ".maestri" / "board" / "core.md"
        self.up_core.write_text("# Nucleo v1\n", encoding="utf-8")
        self.tgt_core = self.repo / "board" / "core.md"
        self.tgt_core.write_text("# Core v1\n", encoding="utf-8")

        self.up_skill = self.home / ".claude" / "skills" / "grill-me" / "SKILL.md"
        self.up_skill.write_text("---\nname: grill-me\n---\n", encoding="utf-8")
        self.tgt_skill = self.repo / "skills" / "grill-me" / "SKILL.md"
        self.tgt_skill.write_text("---\nname: grill-me\n---\n", encoding="utf-8")

        core_sha = hashlib.sha256(self.up_core.read_bytes()).hexdigest()
        skill_sha = hashlib.sha256(self.up_skill.read_bytes()).hexdigest()

        self.manifest_path = self.repo / "sync-manifest.json"
        self.manifest_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "updated_at": "2026-11-19T00:00:00Z",
                    "ignored_upstreams": [
                        "$HOME/.claude/skills/personal-only/SKILL.md"
                    ],
                    "entries": [
                        {
                            "target": "board/core.md",
                            "upstream": "$WORKSPACE/.maestri/board/core.md",
                            "category": "board",
                            "upstream_sha256": core_sha,
                        },
                        {
                            "target": "skills/grill-me/SKILL.md",
                            "upstream": "$HOME/.claude/skills/grill-me/SKILL.md",
                            "category": "skill",
                            "upstream_sha256": skill_sha,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        env = {
            **os.environ,
            "MAESTRI_WORKSPACE_ROOT": str(self.ws),
            "HOME": str(self.home),
        }
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--manifest",
                str(self.manifest_path),
                "--repo-root",
                str(self.repo),
                *args,
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_all_up_to_date(self):
        res = self.run_cli("--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["summary"]["UP_TO_DATE"], 2)
        self.assertEqual(data["summary"]["MODIFIED"], 0)

    def test_detects_modified_upstream_and_records(self):
        self.up_core.write_text("# Nucleo v2 with new Kaizen rule\n", encoding="utf-8")
        res = self.run_cli("--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["summary"]["MODIFIED"], 1)
        mod = [e for e in data["entries"] if e["status"] == "MODIFIED"]
        self.assertEqual(mod[0]["target"], "board/core.md")

        rec = self.run_cli("--record", "board/core.md")
        self.assertEqual(rec.returncode, 0, rec.stderr)

        res2 = self.run_cli("--json")
        data2 = json.loads(res2.stdout)
        self.assertEqual(data2["summary"]["MODIFIED"], 0)
        self.assertEqual(data2["summary"]["UP_TO_DATE"], 2)

    def test_detects_new_candidate_and_respects_ignored(self):
        ignored_dir = self.home / ".claude" / "skills" / "personal-only"
        ignored_dir.mkdir(parents=True)
        (ignored_dir / "SKILL.md").write_text("---\nname: personal\n---\n", encoding="utf-8")

        new_dir = self.home / ".claude" / "skills" / "new-skill"
        new_dir.mkdir(parents=True)
        (new_dir / "SKILL.md").write_text("---\nname: new-skill\n---\n", encoding="utf-8")

        res = self.run_cli("--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertIn("$HOME/.claude/skills/new-skill/SKILL.md", data["new_candidates"])
        self.assertNotIn("$HOME/.claude/skills/personal-only/SKILL.md", data["new_candidates"])


if __name__ == "__main__":
    unittest.main()

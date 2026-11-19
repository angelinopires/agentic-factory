import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCAN_DIRS_ALL = (
    "board",
    "scripts",
    "hooks",
    "templates",
    "skills",
    "rules",
    "docs",
)
SCAN_ROOT_FILES = (
    "README.md",
    "board.config.example.json",
)
SCAN_DIRS_LEGACY_PT = (
    "board",
    "scripts",
    "hooks",
    "templates",
    "skills",
    "rules",
)

FORBIDDEN_PERSONAL_STRINGS = (
    "/Users/" + "angelino",
    "2.25." + "126.235",
    "srv" + "1966273",
    "seutrampo" + ".tech",
    "aesthetic-for" + ".me",
    "tech-" + "lino",
    "STAI_PROD_" + "GUARD",
)

FORBIDDEN_LEGACY_PT_FILENAMES = (
    "ordem.py",
    "mapa.md",
    "casos.md",
    "plano.md",
    "autorizacao.md",
)

PART_B_SKILLS = {
    "verify-claims",
    "verify-ui",
    "infra-preflight",
    "design-port",
    "grill-me",
    "product-eval",
    "audit-codebase",
    "design-decide",
    "ui-ux-analysis",
    "concise-output",
    "humanizer",
    "humanizer-compact",
}

REQUIRED_23_SKILLS = PART_B_SKILLS | {
    "init-board",
    "canvas-manager",
    "canvas-retro",
    "canvas-sprint",
    "prd",
    "prd-run",
    "prd-ship",
    "prd-demo",
    "epic-ship",
    "commit",
    "handover",
}

BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".mp4",
    ".pyc",
}


def iter_text_files(rel_dirs, root_files=()):
    """Yield (relative_path_str, text_content) for all non-binary files in target dirs/files."""
    for rel_dir in rel_dirs:
        base = REPO_ROOT / rel_dir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part.startswith(".git") or part == "__pycache__" for part in path.parts):
                continue
            if path.suffix.lower() in BINARY_SUFFIXES:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            yield rel, content

    for rel_file in root_files:
        path = REPO_ROOT / rel_file
        if path.is_file():
            yield rel_file, path.read_text(encoding="utf-8")


def parse_frontmatter(markdown_text: str):
    """Extract and parse top-level keys from YAML frontmatter."""
    if not markdown_text.startswith("---\n"):
        return None
    end_idx = markdown_text.find("\n---\n", 4)
    if end_idx == -1:
        return None
    raw_block = markdown_text[4:end_idx]
    keys = {}
    current_key = None
    for line in raw_block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            current_key = match.group(1)
            keys[current_key] = match.group(2).strip()
        elif current_key and (line.startswith("  ") or line.startswith("\t")):
            keys[current_key] = (keys[current_key] + " " + line.strip()).strip()
    return keys


class TestLeakAndPortability(unittest.TestCase):
    def test_zero_forbidden_personal_or_local_strings(self):
        violations = []
        for rel_path, content in iter_text_files(SCAN_DIRS_ALL, SCAN_ROOT_FILES):
            for needle in FORBIDDEN_PERSONAL_STRINGS:
                if needle in content:
                    for line_no, line in enumerate(content.splitlines(), start=1):
                        if needle in line:
                            violations.append(f"{rel_path}:{line_no} contains forbidden '{needle}'")
        self.assertEqual(
            violations,
            [],
            "Forbidden personal/local strings detected:\n" + "\n".join(violations),
        )

    def test_zero_legacy_portuguese_filenames(self):
        violations = []
        for rel_path, content in iter_text_files(SCAN_DIRS_LEGACY_PT):
            for needle in FORBIDDEN_LEGACY_PT_FILENAMES:
                pattern = rf"(?<![A-Za-z0-9_-]){re.escape(needle)}(?![A-Za-z0-9_-])"
                if re.search(pattern, content):
                    for line_no, line in enumerate(content.splitlines(), start=1):
                        if re.search(pattern, line):
                            violations.append(
                                f"{rel_path}:{line_no} references legacy PT filename '{needle}'"
                            )
        self.assertEqual(
            violations,
            [],
            "Legacy Portuguese filenames detected:\n" + "\n".join(violations),
        )

    def test_every_skill_has_valid_yaml_frontmatter(self):
        skills_dir = REPO_ROOT / "skills"
        self.assertTrue(skills_dir.is_dir(), "skills/ directory must exist")

        skill_folders = sorted(
            p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
        )
        self.assertGreaterEqual(
            len(skill_folders),
            len(PART_B_SKILLS),
            f"Expected at least {len(PART_B_SKILLS)} skills in skills/",
        )

        for folder in skill_folders:
            skill_md = folder / "SKILL.md"
            self.assertTrue(
                skill_md.is_file(),
                f"Skill directory 'skills/{folder.name}' is missing SKILL.md",
            )
            text = skill_md.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            self.assertIsNotNone(
                fm,
                f"skills/{folder.name}/SKILL.md is missing valid '---' YAML frontmatter",
            )
            self.assertIn(
                "name",
                fm,
                f"skills/{folder.name}/SKILL.md frontmatter is missing 'name:'",
            )
            self.assertEqual(
                fm["name"].strip("'\""),
                folder.name,
                f"skills/{folder.name}/SKILL.md frontmatter name '{fm['name']}' does not match directory",
            )
            self.assertIn(
                "description",
                fm,
                f"skills/{folder.name}/SKILL.md frontmatter is missing 'description:'",
            )
            desc = fm["description"].strip("'\"").strip("|>-").strip()
            self.assertTrue(
                len(desc) > 10,
                f"skills/{folder.name}/SKILL.md frontmatter has empty or too-short description",
            )

    def test_required_skills_inventory(self):
        skills_dir = REPO_ROOT / "skills"
        existing = {
            p.name
            for p in skills_dir.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        }

        missing_part_b = PART_B_SKILLS - existing
        self.assertEqual(
            missing_part_b,
            set(),
            f"Missing required Part B skills: {sorted(missing_part_b)}",
        )

        # Verify sub-file for infra-preflight exists
        self.assertTrue(
            (skills_dir / "infra-preflight" / "references" / "catalog.md").is_file(),
            "skills/infra-preflight/references/catalog.md must exist",
        )

        # When all 23 skills (or board + rules from sibling suites) are present, assert full 23 set
        if REQUIRED_23_SKILLS.issubset(existing) or (
            (REPO_ROOT / "board" / "core.md").is_file()
            and (REPO_ROOT / "rules" / "git-workflow.md").is_file()
            and (skills_dir / "init-board" / "SKILL.md").is_file()
        ):
            missing_all = REQUIRED_23_SKILLS - existing
            self.assertEqual(
                missing_all,
                set(),
                f"Missing required skills from full 23-skill inventory: {sorted(missing_all)}",
            )


if __name__ == "__main__":
    unittest.main()

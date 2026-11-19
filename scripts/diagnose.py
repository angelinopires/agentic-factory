#!/usr/bin/env python3
"""Environment and repository inspector for Agentic Factory onboarding.

Detects installed AI CLIs (maestri, claude, codex, agy), determines routing mode
(multi-harness vs single-harness), inspects target repository structure (monorepo
vs single-repo, lockfiles, UI presence, test runners), and recommends topology.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AI_CLIS = ("claude", "codex", "agy")
ALL_CLIS = ("maestri",) + AI_CLIS
LOCKFILE_NAMES = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "bun.lockb",
    "uv.lock",
    "pyproject.toml",
    "go.mod",
    "Cargo.lock",
)
FRONT_CANDIDATES = ("web", "frontend", "client", "app")
BACK_CANDIDATES = ("server", "backend", "api")
UI_INDICATORS = ("react", "next", "vite", "tailwindcss", "vue", "svelte", "@angular/core")


def detect_clis() -> dict:
    mock = os.environ.get("AGENTIC_MOCK_CLIS")
    if mock is not None:
        present = {c.strip() for c in mock.split(",") if c.strip()}
        found = {cli: (f"/mock/bin/{cli}" if cli in present else None) for cli in ALL_CLIS}
    else:
        found = {cli: shutil.which(cli) for cli in ALL_CLIS}

    installed_ai = [cli for cli in AI_CLIS if found.get(cli)]
    routing_mode = "multi-harness" if len(installed_ai) >= 2 else "single-harness"
    return {
        "cli_paths": found,
        "maestri_installed": bool(found.get("maestri")),
        "installed_ai_clis": installed_ai,
        "routing_mode": routing_mode,
    }


def detect_sub_packages(repo: Path) -> dict:
    front_dir = next((d for d in FRONT_CANDIDATES if (repo / d).is_dir()), None)
    back_dir = next((d for d in BACK_CANDIDATES if (repo / d).is_dir()), None)
    packages_dir = (repo / "packages").is_dir()
    sub_packages = [
        d for d in (*FRONT_CANDIDATES, *BACK_CANDIDATES, "packages") if (repo / d).is_dir()
    ]
    split_dev = bool(front_dir and back_dir)
    is_monorepo = split_dev or packages_dir or len(sub_packages) >= 2
    return {
        "is_monorepo": is_monorepo,
        "split_dev_recommended": split_dev,
        "dev_front_dir": front_dir or "",
        "dev_back_dir": back_dir or "",
        "sub_packages": sub_packages,
    }


def detect_lockfiles_and_ui(repo: Path, sub_packages: list[str]) -> tuple[list[str], bool, list[str]]:
    lockfiles: list[str] = []
    has_ui = False
    test_runners: set[str] = set()
    search_dirs = [repo] + [repo / sp for sp in sub_packages if (repo / sp).is_dir()]

    for d in search_dirs:
        rel_prefix = "" if d == repo else f"{d.relative_to(repo).as_posix()}/"
        for lf in LOCKFILE_NAMES:
            if (d / lf).is_file():
                entry = f"{rel_prefix}{lf}"
                if entry not in lockfiles:
                    lockfiles.append(entry)
        pkg_json = d / "package.json"
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if any(k in deps for k in UI_INDICATORS):
                    has_ui = True
                for runner in ("vitest", "jest", "playwright", "@playwright/test"):
                    if runner in deps:
                        test_runners.add(runner.replace("@playwright/test", "playwright"))
            except (OSError, json.JSONDecodeError):
                pass
        pyproject = d / "pyproject.toml"
        if pyproject.is_file():
            try:
                text = pyproject.read_text(encoding="utf-8")
                if "pytest" in text:
                    test_runners.add("pytest")
            except OSError:
                pass
        if (d / "tests").is_dir():
            test_runners.add("unittest")

    if any((repo / d).is_dir() for d in ("web", "frontend")):
        has_ui = True
    return lockfiles, has_ui, sorted(test_runners)


def detect_worktrees(repo: Path) -> list[str]:
    if not (repo / ".git").exists():
        return []
    try:
        res = subprocess.run(
            ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode != 0:
            return []
        return [
            line.removeprefix("worktree ").strip()
            for line in res.stdout.splitlines()
            if line.startswith("worktree ")
        ]
    except (OSError, subprocess.SubprocessError):
        return []


def recommend_topology(repo: Path) -> str:
    resolved = repo.resolve()
    for parent in (resolved.parent, resolved.parent.parent):
        if (parent / "planning").is_dir():
            return "workspace"
    return "single-repo"


def diagnose_repo(repo_path: Path) -> dict:
    repo = repo_path.resolve()
    cli_info = detect_clis()
    pkg_info = detect_sub_packages(repo)
    lockfiles, has_ui, test_runners = detect_lockfiles_and_ui(repo, pkg_info["sub_packages"])
    topology = recommend_topology(repo)
    worktrees = detect_worktrees(repo)

    return {
        "repo_path": str(repo),
        "project_name": repo.name,
        "is_git_repo": (repo / ".git").exists(),
        "worktrees": worktrees,
        **cli_info,
        "topology_recommendation": topology,
        **pkg_info,
        "lockfiles": lockfiles,
        "has_ui": has_ui,
        "test_runners": test_runners,
        "recommended_roles": {
            "core": ["Manager", "Explorer", "Dev", "QA"],
            "split_dev": pkg_info["split_dev_recommended"],
            "enable_designer": has_ui,
            "enable_writer": has_ui,
            "enable_rollout": (repo / "docker-compose.prod.yml").is_file(),
            "enable_blind_reviewer": cli_info["routing_mode"] == "multi-harness",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose environment and repository for Agentic Factory.")
    parser.add_argument("--repo", default=".", help="Path to target repository (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Output diagnosis report as JSON")
    args = parser.parse_args(argv)

    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"diagnose: repository path does not exist: {repo_path}", file=sys.stderr)
        return 2

    report = diagnose_repo(repo_path)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

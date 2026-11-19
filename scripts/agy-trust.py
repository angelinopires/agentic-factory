#!/usr/bin/env python3
"""Pre-trust Maestri role folders in the Antigravity CLI (agy).

agy trusts exact paths only, and every Maestri terminal runs in
`<dir>/.maestri/roles/<role-uuid>`. A new `--dir` or git worktree creates a new
path that triggers an interactive "trust this folder" prompt, stalling the terminal
until someone accepts it. Run this before recruiting any `agy` terminal:

    python3 scripts/agy-trust.py                 # project + server/web + planning + all worktrees
    python3 scripts/agy-trust.py /extra/dir ...  # plus extra --dir values
"""
import json
import os
from pathlib import Path
import subprocess
import sys


def load_paths() -> tuple[Path, Path, Path]:
    ws = os.environ.get("MAESTRI_WORKSPACE_ROOT")
    proj = os.environ.get("MAESTRI_PROJECT_DIR")
    plan = os.environ.get("MAESTRI_PLANNING_DIR")
    repo_root = Path(__file__).resolve().parent.parent
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        str(Path.cwd() / "board.config.json"),
        str(repo_root / "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    paths = json.load(f).get("paths") or {}
                ws = ws or paths.get("workspace_root")
                proj = proj or paths.get("project_dir")
                plan = plan or paths.get("planning_dir")
                break
            except (OSError, ValueError):
                pass
    ws_path = Path(ws or ".").resolve()
    proj_path = Path(proj).resolve() if proj else ws_path
    plan_path = Path(plan).resolve() if plan else (ws_path / "planning")
    return ws_path, proj_path, plan_path


def role_uuids(ws: Path) -> set[str]:
    return {p.name for p in ws.glob("**/.maestri/roles/*") if p.is_dir() and len(p.name) == 36}


def worktrees(repo: Path) -> list[Path]:
    res = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return [repo]
    return [Path(line.split(" ", 1)[1]) for line in res.splitlines() if line.startswith("worktree ")]


def main() -> None:
    ws, repo, planning = load_paths()
    settings = Path(
        os.environ.get("AGY_SETTINGS_PATH") or (Path.home() / ".gemini" / "antigravity-cli" / "settings.json")
    )
    bases = [planning, *[Path(a).resolve() for a in sys.argv[1:]]]
    for wt in worktrees(repo):
        bases += [wt, wt / "server", wt / "web"]
    wanted = [str(b / ".maestri/roles" / u) for b in bases for u in sorted(role_uuids(ws))]
    data = json.loads(settings.read_text(encoding="utf-8")) if settings.is_file() else {}
    current = data.get("trustedWorkspaces", [])
    added = [w for w in wanted if w not in current]
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps({**data, "trustedWorkspaces": current + added}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"agy trust: +{len(added)} (total {len(current) + len(added)})")


if __name__ == "__main__":
    main()

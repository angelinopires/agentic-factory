#!/usr/bin/env python3
"""Verify that the role prompt loaded by each agent terminal matches the board source (`board/README.md`).

  role-check.py [Role ...]      without arguments, checks all roles in the active workspace
  role-check.py --self-test     verifies SOURCES matches the role assembly loop in board/README.md
  exit 0 = all aligned · 1 = divergence or missing role · 2 = read error

Three layers per role: source (`board/*.md`) → `role.json` (materialized preset) → `CLAUDE.md`/`AGENTS.md`
(what the agent reads in its cwd). When `MAESTRI_SOCKET` is set, also checks `maestri role show <Role>`.
Read-only gate: run before dispatching the first ORDER to a role; if divergent, rematerialize via `maestri role write`
when the terminal is idle.
"""
import difflib
import glob
import json
import os
import re
import subprocess
import sys

SOURCES = {
    "Manager": ["core.md", "manager.md"],
    "Explorer": ["core.md", "explorer.md"],
    "Writer": ["core.md", "writer.md"],
    "Designer": ["core.md", "designer.md"],
    "QA": ["core.md", "qa.md"],
    "Dev": ["core.md", "dev.md"],
    "Rollout": ["core.md", "rollout.md", "rollout-manual.md"],
}
WRAP = re.compile(r"^<your_assigned_role>\n(.*?)\n</your_assigned_role>", re.S)


def resolve_config() -> tuple[str, str, str]:
    ws = os.environ.get("MAESTRI_WORKSPACE_ROOT")
    board = os.environ.get("MAESTRI_BOARD_DIR")
    ws_name = os.environ.get("MAESTRI_WORKSPACE")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        os.path.join(os.getcwd(), "board.config.json"),
        os.path.join(repo_root, "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    data = json.load(f)
                paths = data.get("paths") or {}
                maestri = data.get("maestri") or {}
                ws = ws or paths.get("workspace_root")
                board = board or paths.get("board_dir")
                ws_name = ws_name or maestri.get("workspace_name") or data.get("project_name")
                break
            except (OSError, ValueError):
                pass
    ws = os.path.abspath(ws or ".")
    if not board:
        local_board = os.path.abspath("./board")
        board = local_board if os.path.isdir(local_board) else os.path.join(repo_root, "board")
    return ws, board, ws_name or "my-project"


def expected(board_dir: str, name: str) -> str:
    return "".join(
        open(os.path.join(board_dir, f), encoding="utf-8").read() for f in SOURCES[name]
    ).rstrip("\n")


def active_role_ids(ws_name: str) -> set[str]:
    for path in glob.glob(os.path.expanduser("~/.maestri/workspaces/*/workspace.json")):
        text = open(path, encoding="utf-8").read()
        if f'"name":"{ws_name}"' in text.replace(" ", "") or f'"{ws_name}"' in text:
            return {i.lower() for i in re.findall(r'"assignedRoleId"\s*:\s*"([^"]+)"', text)}
    sys.exit(f"workspace '{ws_name}' not found in ~/.maestri/workspaces")


def materialized(ws: str, ids: set[str]) -> dict[str, list[str]]:
    found = {}
    for d in glob.glob(f"{ws}/**/.maestri/roles/*/", recursive=True):
        rid = os.path.basename(d.rstrip("/"))
        if rid in ids and "/archive/" not in d:
            found.setdefault(rid, []).append(d)
    return found


def norm(text: str) -> list[str]:
    """Ignore blank lines and trailing whitespace across concatenated layers."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def summary(want: str, got: str) -> str:
    lines = [
        line
        for line in difflib.unified_diff(norm(want), norm(got), "source", "loaded", n=0, lineterm="")
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    missing = sum(1 for line in lines if line.startswith("-"))
    extra = len(lines) - missing
    first = lines[0][:90] if lines else ""
    return f"{missing} source lines missing, {extra} extra · first diff: {first}"


def preset_text(name: str) -> str | None:
    if not os.environ.get("MAESTRI_SOCKET"):
        return None
    r = subprocess.run(["maestri", "role", "show", name], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return None
    return r.stdout.removeprefix(f"Role: {name}\n").rstrip("\n")


def check(ws: str, board_dir: str, rid: str, dirs: list[str]) -> tuple[str | None, list[str]]:
    problems = []
    name = None
    for d in dirs:
        with open(os.path.join(d, "role.json"), encoding="utf-8") as f:
            role = json.load(f)
        name = role["name"]
        if name not in SOURCES:
            return name, [f"role '{name}' has no source in board"]
        want = expected(board_dir, name)
        layers = {"role.json": role["prompt"].rstrip("\n")}
        for fname in ("CLAUDE.md", "AGENTS.md"):
            fpath = os.path.join(d, fname)
            if os.path.exists(fpath):
                m = WRAP.match(open(fpath, encoding="utf-8").read())
                layers[fname] = m.group(1).rstrip("\n") if m else "<missing your_assigned_role block>"
        for layer, got in layers.items():
            if norm(got) != norm(want):
                problems.append(f"{os.path.join(os.path.relpath(d, ws), layer)}: {summary(want, got)}")
    preset = preset_text(name) if name else None
    if preset is not None and norm(preset) != norm(expected(board_dir, name)):
        problems.append(f"app preset: {summary(expected(board_dir, name), preset)}")
    return name, problems


def readme_sources(board_dir: str) -> dict[str, list[str]]:
    """Parse the role assembly loop in board/README.md and return {role: [files]}."""
    text = open(os.path.join(board_dir, "README.md"), encoding="utf-8").read()
    out = {}
    m = re.search(r"for p in ([^;]+); do", text)
    if m:
        for pair in m.group(1).split():
            f, name = pair.split(":")
            out[name] = ["core.md", f"{f}.md"]
    for name, files in re.findall(r'maestri role \$V "(\w+)" "\$\(cat ([^)]+)\)"', text):
        out[name] = [os.path.basename(x) for x in files.split()]
    return out


def main() -> int:
    ws, board_dir, ws_name = resolve_config()
    if sys.argv[1:] == ["--self-test"]:
        got = readme_sources(board_dir)
        assert got == SOURCES, f"SOURCES diverges from README: {got}"
        print("OK SOURCES = README")
        return 0
    wanted = set(sys.argv[1:])
    ids = active_role_ids(ws_name)
    mats = materialized(ws, ids)
    bad = 0
    for rid in sorted(ids):
        if rid not in mats:
            print(f"?? {rid[:8]} has no materialized folder (terminal not yet recruited with --role?)")
            continue
        name, problems = check(ws, board_dir, rid, mats[rid])
        if wanted and name not in wanted:
            continue
        print(f"{'OK' if not problems else 'DIVERGE'} {name} ({rid[:8]})")
        for p in problems:
            print(f"   {p}")
        bad += bool(problems)
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as e:
        print(f"role-check: {e}", file=sys.stderr)
        sys.exit(2)

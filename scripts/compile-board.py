#!/usr/bin/env python3
"""Role compiler, word-budget verifier, planning scaffolder, and skill installer.

Supports:
  --check-budgets [--board-dir <dir>]
  --config <board.config.json> --out <target_dir> [--install-skills <project|global>] [--home-dir <dir>]
"""
import argparse
import datetime
import json
import os
import shutil
import stat
import sys
from pathlib import Path

FACTORY_ROOT = Path(__file__).resolve().parent.parent
ROLE_FILES = ("manager.md", "explorer.md", "designer.md", "writer.md", "dev.md", "qa.md", "rollout.md")
CORE_MAX_WORDS = 500
ROLE_MAX_WORDS = 400
PLAYBOOK_MAX_LINES = 120

SINGLE_CLI_DEFAULTS = {
    "claude": {
        "preset": "Claude Code",
        "high": ("claude", "claude-opus-5-5", '--effort medium --permission-mode auto --remote-control "Manager"'),
        "medium": ("claude", "claude-sonnet-5-5", "--permission-mode auto --disallowedTools SendMessage"),
        "browser": ("claude", "claude-sonnet-5-5", "--permission-mode auto --disallowedTools SendMessage --chrome --strict-mcp-config"),
    },
    "codex": {
        "preset": "Codex",
        "high": ("codex", "gpt-6.1-sol", '-p maestri -c model_reasoning_effort="high" --approve-for-me'),
        "medium": ("codex", "gpt-6.1-sol", '-p maestri -c model_reasoning_effort="medium" --approve-for-me'),
        "browser": ("codex", "gpt-6.1-sol", '-p maestri -c model_reasoning_effort="medium" --approve-for-me'),
    },
    "agy": {
        "preset": "Antigravity",
        "high": ("agy", "gemini-4-neon-high", "--mode auto"),
        "medium": ("agy", "gemini-4-neon-high", "--mode auto"),
        "browser": ("agy", "gemini-4-neon-high", "--mode auto"),
    },
}


def check_budgets(board_dir: Path) -> int:
    errors: list[str] = []
    core_path = board_dir / "core.md"
    if not core_path.is_file():
        errors.append(f"Missing {core_path}")
    else:
        words = len(core_path.read_text(encoding="utf-8").split())
        print(f"core.md: {words}/{CORE_MAX_WORDS} words")
        if words > CORE_MAX_WORDS:
            errors.append(f"core.md exceeds {CORE_MAX_WORDS} words ({words})")

    for rf in ROLE_FILES:
        p = board_dir / rf
        if not p.is_file():
            errors.append(f"Missing {p}")
            continue
        words = len(p.read_text(encoding="utf-8").split())
        print(f"{rf}: {words}/{ROLE_MAX_WORDS} words")
        if words > ROLE_MAX_WORDS:
            errors.append(f"{rf} exceeds {ROLE_MAX_WORDS} words ({words})")

    playbook_path = board_dir / "playbook.md"
    if not playbook_path.is_file():
        errors.append(f"Missing {playbook_path}")
    else:
        lines = len(playbook_path.read_text(encoding="utf-8").splitlines())
        print(f"playbook.md: {lines}/{PLAYBOOK_MAX_LINES} lines")
        if lines > PLAYBOOK_MAX_LINES:
            errors.append(f"playbook.md exceeds {PLAYBOOK_MAX_LINES} lines ({lines})")

    if errors:
        for e in errors:
            print(f"BUDGET FAIL: {e}", file=sys.stderr)
        return 1
    print("OK all board prompt budgets satisfied.")
    return 0


def build_placeholders(config: dict, out_board_dir: Path) -> dict[str, str]:
    paths = config.get("paths", {})
    roles = config.get("roles", {})
    project_name = config.get("project_name", "my-project")
    ws_root = paths.get("workspace_root", ".")
    project_dir = paths.get("project_dir", f"./projects/{project_name}")
    planning_dir = paths.get("planning_dir", f"./planning/{project_name}")
    if roles.get("split_dev"):
        front = roles.get("dev_front_dir", f"{project_dir}/web")
        back = roles.get("dev_back_dir", f"{project_dir}/server")
        dev_dirs = f"Front: {front}, Back: {back}"
    else:
        dev_dirs = project_dir
    return {
        "{{WORKSPACE_ROOT}}": str(ws_root),
        "{{PROJECT_DIR}}": str(project_dir),
        "{{PLANNING_DIR}}": str(planning_dir),
        "{{LANGUAGE}}": str(config.get("language", "en")),
        "{{DEV_DIRS}}": str(dev_dirs),
        "{{PROJECT_NAME}}": str(project_name),
        "{{BOARD_DIR}}": str(out_board_dir),
    }


def render_text(text: str, placeholders: dict[str, str]) -> str:
    result = text
    for k, v in placeholders.items():
        result = result.replace(k, v)
    return result


def resolve_role_command(role_key: str, tier: str, config: dict, out_board_dir: Path) -> tuple[str, str]:
    routing = config.get("routing", {})
    installed = routing.get("installed_clis") or ["claude"]
    mode = routing.get("mode", "multi-harness" if len(installed) >= 2 else "single-harness")
    assignments = routing.get("assignments", {})
    ws_root = config.get("paths", {}).get("workspace_root", ".")

    chosen_cli = installed[0]
    assigned = assignments.get(role_key, {})
    if mode == "multi-harness" and assigned.get("cli") in installed:
        chosen_cli = assigned["cli"]
    elif mode == "multi-harness" and not assigned:
        default_multi = {
            "Manager": "claude",
            "Explorer": "agy",
            "Writer": "agy",
            "Designer": "codex",
            "Dev": "codex",
            "QA": "claude",
            "Rollout": "claude",
            "Reviewer": "agy",
        }
        candidate = default_multi.get(role_key, installed[0])
        chosen_cli = candidate if candidate in installed else installed[0]

    spec = SINGLE_CLI_DEFAULTS.get(chosen_cli, SINGLE_CLI_DEFAULTS["claude"])
    preset = assigned.get("preset") if assigned.get("cli") == chosen_cli and assigned.get("preset") else spec["preset"]
    cli_bin, default_model, default_flags = spec.get(tier, spec["medium"])
    model = assigned.get("model") if assigned.get("cli") == chosen_cli and assigned.get("model") else default_model

    if chosen_cli == "claude":
        extra = ""
        if role_key == "QA":
            extra = f" --settings {out_board_dir}/settings/qa-settings.json"
        elif role_key == "Rollout":
            extra = f" --settings {out_board_dir}/settings/rollout-settings.json"
        cmd = f"claude --model {model} {default_flags}{extra}".strip()
    elif chosen_cli == "codex":
        cmd = f"codex -m {model} {default_flags}".strip()
    else:
        cmd = f"agy --add-dir {ws_root} {default_flags} --settings {out_board_dir}/settings/agy-settings.json --model {model}".strip()
    return preset, cmd


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def generate_board_scripts(config: dict, out_board_dir: Path) -> None:
    roles_cfg = config.get("roles", {})
    paths = config.get("paths", {})
    project_dir = paths.get("project_dir", ".")
    planning_dir = paths.get("planning_dir", "./planning")

    pairs = ["manager:Manager", "explorer:Explorer"]
    if roles_cfg.get("enable_writer"):
        pairs.append("writer:Writer")
    if roles_cfg.get("enable_designer"):
        pairs.append("designer:Designer")
    pairs.append("qa:QA")

    assemble_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'B="{out_board_dir}"',
        'V="${1:-create}"',
        f'for p in {" ".join(pairs)}; do',
        '  maestri role "$V" "${p#*:}" "$(cat "$B/core.md" "$B/${p%%:*}.md")"',
        "done",
        'maestri role "$V" "Dev" "$(cat "$B/core.md" "$B/dev.md")"',
    ]
    if roles_cfg.get("enable_rollout"):
        assemble_lines.append('maestri role "$V" "Rollout" "$(cat "$B/core.md" "$B/rollout.md" "$B/rollout-manual.md")"')

    assemble_text = "\n".join(assemble_lines) + "\n"
    for name in ("assemble-roles.sh", "roles.sh"):
        p = out_board_dir / name
        p.write_text(assemble_text, encoding="utf-8")
        make_executable(p)

    recruit_specs: list[tuple[str, str, str, str]] = [
        ("Explorer", "Explorer", "medium", project_dir),
    ]
    if roles_cfg.get("enable_writer"):
        recruit_specs.append(("Writer", "Writer", "medium", project_dir))
    if roles_cfg.get("enable_designer"):
        recruit_specs.append(("Designer", "Designer", "medium", planning_dir))

    dev_terminals: list[str] = []
    if roles_cfg.get("split_dev"):
        front_dir = roles_cfg.get("dev_front_dir", f"{project_dir}/web")
        back_dir = roles_cfg.get("dev_back_dir", f"{project_dir}/server")
        recruit_specs.append(("Dev Front", "Dev", "medium", front_dir))
        recruit_specs.append(("Dev Back", "Dev", "medium", back_dir))
        dev_terminals = ["Dev Front", "Dev Back"]
    else:
        recruit_specs.append(("Dev", "Dev", "medium", project_dir))
        dev_terminals = ["Dev"]

    recruit_specs.append(("QA", "QA", "browser", project_dir))
    if roles_cfg.get("enable_rollout"):
        recruit_specs.append(("Rollout", "Rollout", "medium", project_dir))
    if roles_cfg.get("enable_blind_reviewer"):
        recruit_specs.append(("Reviewer", "Explorer", "medium", project_dir))

    recruit_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    for term_name, role_name, tier, cwd in recruit_specs:
        lookup_key = "Dev" if term_name in ("Dev Front", "Dev Back") else term_name
        preset, cmd = resolve_role_command(lookup_key, tier, config, out_board_dir)
        recruit_lines.append(
            f'maestri recruit "{term_name}" --preset "{preset}" --command \'{cmd}\' --role "{role_name}" --dir "{cwd}"'
        )
    for dt in dev_terminals:
        recruit_lines.append(f'maestri connect "QA" "{dt}"')

    recruit_path = out_board_dir / "recruit.sh"
    recruit_path.write_text("\n".join(recruit_lines) + "\n", encoding="utf-8")
    make_executable(recruit_path)


def scaffold_planning(config: dict, placeholders: dict[str, str], factory_root: Path) -> None:
    paths = config.get("paths", {})
    project_name = config.get("project_name", "my-project")
    planning_dir = Path(paths.get("planning_dir", f"./planning/{project_name}")).resolve()
    project_dir = Path(paths.get("project_dir", f"./projects/{project_name}")).resolve()

    for sub in ("epics", "drafts", "design", "ready", "archive/epics", "notes", "runs"):
        (planning_dir / sub).mkdir(parents=True, exist_ok=True)

    tpl_planning = factory_root / "templates" / "planning"
    for f in ("CLAUDE.md", "_template_prd.md", "_template_epic.md", "progress.md", "history.md"):
        src = tpl_planning / f
        dst = planning_dir / f
        if src.is_file() and not dst.exists():
            dst.write_text(render_text(src.read_text(encoding="utf-8"), placeholders), encoding="utf-8")

    sheet_src = factory_root / "templates" / "voice" / "project-sheet.md"
    sheet_dst = planning_dir / "project-sheet.md"
    if sheet_src.is_file() and not sheet_dst.exists():
        sheet_dst.write_text(render_text(sheet_src.read_text(encoding="utf-8"), placeholders), encoding="utf-8")

    # Single-repo isolation: if planning_dir lives inside project_dir, exclude it via .git/info/exclude
    try:
        rel = planning_dir.relative_to(project_dir)
        top_part = rel.parts[0] if rel.parts else "planning"
        exclude_file = project_dir / ".git" / "info" / "exclude"
        if (project_dir / ".git").is_dir():
            exclude_file.parent.mkdir(parents=True, exist_ok=True)
            existing = exclude_file.read_text(encoding="utf-8") if exclude_file.is_file() else ""
            marker = f"/{top_part}/"
            if marker not in existing and top_part not in existing:
                with exclude_file.open("a", encoding="utf-8") as fh:
                    fh.write(f"\n# Agentic Factory: isolate planning state across prd/<n> branches\n{marker}\n")
    except ValueError:
        pass


def backup_if_exists(target: Path) -> None:
    if not target.exists() and not target.is_symlink():
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    backup = target.with_name(f"{target.name}.bak.{stamp}")
    counter = 1
    while backup.exists() or backup.is_symlink():
        backup = target.with_name(f"{target.name}.bak.{stamp}.{counter}")
        counter += 1
    target.rename(backup)


def install_skills(mode: str, config: dict, factory_root: Path, home_dir: Path) -> None:
    skills_src = factory_root / "skills"
    rules_src = factory_root / "rules"
    ws_root = Path(config.get("paths", {}).get("workspace_root", ".")).resolve()

    if mode == "project":
        for dest_base in (ws_root / ".claude" / "skills", ws_root / ".agents" / "skills"):
            dest_base.mkdir(parents=True, exist_ok=True)
            if skills_src.is_dir():
                for skill_dir in sorted(skills_src.iterdir()):
                    if not skill_dir.is_dir():
                        continue
                    dst = dest_base / skill_dir.name
                    if dst.exists() or dst.is_symlink():
                        shutil.rmtree(dst) if dst.is_dir() and not dst.is_symlink() else dst.unlink()
                    shutil.copytree(skill_dir, dst)
        if rules_src.is_dir():
            rules_dst = ws_root / ".claude" / "rules"
            rules_dst.mkdir(parents=True, exist_ok=True)
            for rf in sorted(rules_src.glob("*.md")):
                shutil.copy2(rf, rules_dst / rf.name)
    elif mode == "global":
        global_targets = (
            home_dir / ".claude" / "skills",
            home_dir / ".agents" / "skills",
            home_dir / ".gemini" / "config" / "skills",
        )
        for dest_base in global_targets:
            dest_base.mkdir(parents=True, exist_ok=True)
            if skills_src.is_dir():
                for skill_dir in sorted(skills_src.iterdir()):
                    if not skill_dir.is_dir():
                        continue
                    dst = dest_base / skill_dir.name
                    if dst.is_symlink() and dst.resolve() == skill_dir.resolve():
                        continue
                    backup_if_exists(dst)
                    dst.symlink_to(skill_dir.resolve())


def compile_board(config_path: Path, out_dir: Path, install_mode: str | None, home_dir: Path, factory_root: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    out_board_dir = out_dir.resolve() if out_dir.name == "board" else (out_dir / "board").resolve()
    (out_board_dir / "settings").mkdir(parents=True, exist_ok=True)

    placeholders = build_placeholders(config, out_board_dir)
    src_board = factory_root / "board"

    for md_file in sorted(src_board.glob("*.md")):
        rendered = render_text(md_file.read_text(encoding="utf-8"), placeholders)
        (out_board_dir / md_file.name).write_text(rendered, encoding="utf-8")

    src_settings = src_board / "settings"
    if src_settings.is_dir():
        for sf in sorted(src_settings.glob("*.json")):
            rendered = render_text(sf.read_text(encoding="utf-8"), placeholders)
            (out_board_dir / "settings" / sf.name).write_text(rendered, encoding="utf-8")

    generate_board_scripts(config, out_board_dir)
    scaffold_planning(config, placeholders, factory_root)

    if install_mode:
        install_skills(install_mode, config, factory_root, home_dir)

    print(f"OK compiled board to {out_board_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile Maestri board roles and scaffold planning.")
    parser.add_argument("--check-budgets", action="store_true", help="Verify word/line budgets on board/*.md")
    parser.add_argument("--board-dir", default=str(FACTORY_ROOT / "board"), help="Board source directory")
    parser.add_argument("--config", help="Path to board.config.json")
    parser.add_argument("--out", help="Output directory (e.g. .maestri)")
    parser.add_argument("--install-skills", choices=("project", "global"), help="Install skills at project or global level")
    parser.add_argument("--global", dest="global_flag", action="store_true", help="Alias for --install-skills global")
    parser.add_argument("--home-dir", default=str(Path.home()), help="Home directory override for global skill installation")
    args = parser.parse_args(argv)

    if args.check_budgets:
        return check_budgets(Path(args.board_dir))

    if not args.config or not args.out:
        parser.error("--config and --out are required unless --check-budgets is set")

    install_mode = "global" if args.global_flag else args.install_skills
    return compile_board(
        Path(args.config),
        Path(args.out),
        install_mode,
        Path(args.home_dir),
        FACTORY_ROOT,
    )


if __name__ == "__main__":
    sys.exit(main())

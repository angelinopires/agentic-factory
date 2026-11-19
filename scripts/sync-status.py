#!/usr/bin/env python3
"""Compare live upstream setup files against the exported agentic-factory repository.

Usage:
  python3 scripts/sync-status.py [--manifest sync-manifest.json] [--json]
  python3 scripts/sync-status.py --record [target ...]
  python3 scripts/sync-status.py --record-all

Upstream paths inside sync-manifest.json use portable `$WORKSPACE` and `$HOME` tokens so
no machine-specific absolute paths are ever committed to the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_tokens(raw_path: str, workspace_root: Path, home_dir: Path) -> Path:
    expanded = raw_path.replace("$WORKSPACE", str(workspace_root)).replace("$HOME", str(home_dir))
    return Path(expanded)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_candidates(workspace_root: Path, home_dir: Path, tracked: set[str], ignored: set[str]) -> list[str]:
    candidates: list[str] = []
    board_dir = workspace_root / ".maestri" / "board"
    if board_dir.is_dir():
        for p in sorted(board_dir.glob("*.md")):
            tok = f"$WORKSPACE/.maestri/board/{p.name}"
            if tok not in tracked and tok not in ignored:
                candidates.append(tok)
    scripts_dir = workspace_root / ".maestri" / "scripts"
    if scripts_dir.is_dir():
        for p in sorted(scripts_dir.glob("*.py")):
            if p.name.startswith("test_"):
                continue
            tok = f"$WORKSPACE/.maestri/scripts/{p.name}"
            if tok not in tracked and tok not in ignored:
                candidates.append(tok)
    skills_dir = home_dir / ".claude" / "skills"
    if skills_dir.is_dir():
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            tok = f"$HOME/.claude/skills/{p.parent.name}/SKILL.md"
            if tok not in tracked and tok not in ignored:
                candidates.append(tok)
    return candidates


def evaluate_manifest(manifest: dict, repo_root: Path, workspace_root: Path, home_dir: Path) -> dict:
    entries_out = []
    counts = {"UP_TO_DATE": 0, "MODIFIED": 0, "MISSING_UPSTREAM": 0, "MISSING_TARGET": 0}
    tracked_upstreams: set[str] = set()
    for item in manifest.get("entries", []):
        target_rel = item["target"]
        upstream_tok = item["upstream"]
        tracked_upstreams.add(upstream_tok)
        target_path = repo_root / target_rel
        upstream_path = resolve_tokens(upstream_tok, workspace_root, home_dir)
        current_sha = sha256_file(upstream_path)
        recorded_sha = item.get("upstream_sha256")
        if current_sha is None:
            status = "MISSING_UPSTREAM"
        elif not target_path.exists():
            status = "MISSING_TARGET"
        elif current_sha != recorded_sha:
            status = "MODIFIED"
        else:
            status = "UP_TO_DATE"
        counts[status] += 1
        entries_out.append(
            {
                "target": target_rel,
                "upstream": upstream_tok,
                "category": item.get("category", "misc"),
                "status": status,
                "recorded_sha256": recorded_sha,
                "current_sha256": current_sha,
            }
        )
    ignored = set(manifest.get("ignored_upstreams", []))
    new_candidates = discover_candidates(workspace_root, home_dir, tracked_upstreams, ignored)
    return {
        "updated_at": manifest.get("updated_at"),
        "summary": counts,
        "entries": entries_out,
        "new_candidates": new_candidates,
    }


def record_hashes(manifest: dict, targets: set[str] | None, workspace_root: Path, home_dir: Path) -> int:
    updated = 0
    for item in manifest.get("entries", []):
        if targets is not None and item["target"] not in targets:
            continue
        upstream_path = resolve_tokens(item["upstream"], workspace_root, home_dir)
        digest = sha256_file(upstream_path)
        if digest is None:
            print(f"sync-status: upstream not found for {item['target']}: {item['upstream']}", file=sys.stderr)
            return 1
        item["upstream_sha256"] = digest
        updated += 1
    manifest["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and record upstream sync state for agentic-factory.")
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="Path to agentic-factory repo root")
    parser.add_argument("--manifest", default=None, help="Path to sync-manifest.json")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--record", nargs="*", default=None, help="Record current upstream SHA-256 for target(s)")
    parser.add_argument("--record-all", action="store_true", help="Record current upstream SHA-256 for all entries")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else repo_root / "sync-manifest.json"
    if not manifest_path.is_file():
        print(f"sync-status: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    default_ws = repo_root.parent.parent if repo_root.parent.name == "projects" else Path.home() / "Workspace"
    workspace_root = Path(os.environ.get("MAESTRI_WORKSPACE_ROOT") or default_ws).resolve()
    home_dir = Path(os.environ.get("HOME") or Path.home()).resolve()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.record_all or args.record is not None:
        targets = None if (args.record_all or len(args.record) == 0) else set(args.record)
        rc = record_hashes(manifest, targets, workspace_root, home_dir)
        if rc != 0:
            return rc
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = evaluate_manifest(manifest, repo_root, workspace_root, home_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    s = report["summary"]
    print(
        f"Sync Status (last recorded: {report['updated_at']}): "
        f"{s['UP_TO_DATE']} up-to-date · {s['MODIFIED']} modified · "
        f"{s['MISSING_UPSTREAM']} missing upstream · {s['MISSING_TARGET']} missing target"
    )
    for e in report["entries"]:
        if e["status"] != "UP_TO_DATE":
            print(f"  [{e['status']}] {e['target']} <- {e['upstream']}")
    if report["new_candidates"]:
        print("New upstream candidates not in manifest:")
        for c in report["new_candidates"]:
            print(f"  [NEW_CANDIDATE] {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

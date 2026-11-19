#!/usr/bin/env python3
"""Verifiable cryptographic QA proof: binds a green test run to the exact git tree and lockfiles tested.

Replaces raw diff hashing (which collided on the empty SHA across any clean git tree).

  record  --prd 209 --order 209-A2 [--base main] [--gate A2=executed] [--out f.json] [-- cmd ...]
  verify  f.json [--base main]      recomputes and lists changes; exit 1 if proof does not match current tree

Identity = sha256 of: commit, tree, base, dirty_sha256 (diff + untracked), command, and dependency lockfiles.
Gate states: executed | blocked | waived, requiring `:reason` when not `executed` (e.g. mutations=blocked:no_db).
"""
import argparse
import fnmatch
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

LOCKFILE_PATTERNS = (
    "*lock*",
    "*package.json",
    "*pyproject.toml",
    "go.mod",
    "Cargo.lock",
    "*Dockerfile*",
    "docker-compose*",
)
GATE_STATES = ("executed", "blocked", "waived")
IDENTITY_KEYS = ("commit", "tree", "base", "dirty_sha256", "command", "deps")


def git(*args: str, check: bool = True) -> bytes:
    r = subprocess.run(["git", *args], capture_output=True, check=False)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'ignore').strip()}")
    return r.stdout


def dirty_hash() -> str | None:
    """None when the working tree is clean; otherwise SHA-256 of tracked binary diff + untracked files."""
    if not git("status", "--porcelain").strip():
        return None
    h = hashlib.sha256(git("diff", "HEAD", "--binary"))
    untracked = git("ls-files", "-o", "--exclude-standard", "-z").decode("utf-8", "ignore").split("\0")
    for path in sorted(p for p in untracked if p):
        h.update(path.encode("utf-8") + b"\0")
        if os.path.islink(path):
            h.update(os.readlink(path).encode("utf-8"))
        elif os.path.isfile(path):
            with open(path, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()


def resolve_dep_files() -> list[str]:
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        os.path.join(os.getcwd(), "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    data = json.load(f)
                qp = data.get("qa_proof") or {}
                dep_files = qp.get("dep_files")
                if isinstance(dep_files, list) and dep_files:
                    return list(dep_files)
                if qp.get("auto_discover_lockfiles") is False:
                    return []
            except (OSError, ValueError):
                pass
    tracked = git("ls-files", "-z", check=False).decode("utf-8", "ignore").split("\0")
    matched = []
    for p in sorted(f for f in tracked if f):
        base = os.path.basename(p)
        if any(fnmatch.fnmatch(base, pat) or fnmatch.fnmatch(p, pat) for pat in LOCKFILE_PATTERNS):
            matched.append(p)
    return matched


def deps() -> dict[str, str]:
    out = {}
    for p in resolve_dep_files():
        blob = git("rev-parse", f"HEAD:{p}", check=False).strip().decode("utf-8", "ignore")
        if blob:
            out[p] = blob
    return out


def tool_version(cmd: list[str]) -> str | None:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def snapshot(base_ref: str, command: str | None) -> dict:
    os.chdir(git("rev-parse", "--show-toplevel").strip().decode("utf-8"))
    base_bytes = git("merge-base", "HEAD", base_ref, check=False).strip()
    base = base_bytes.decode("utf-8") if base_bytes else git("rev-parse", "HEAD").strip().decode("utf-8")
    return {
        "commit": git("rev-parse", "HEAD").strip().decode("utf-8"),
        "tree": git("rev-parse", "HEAD^{tree}").strip().decode("utf-8"),
        "base": base,
        "base_ref": base_ref,
        "dirty_sha256": dirty_hash(),
        "command": command,
        "deps": deps(),
    }


def identity(s: dict) -> str:
    canon = json.dumps({k: s[k] for k in IDENTITY_KEYS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def parse_gate(g: str) -> tuple[str, dict]:
    name, _, rest = g.partition("=")
    state, _, why = rest.partition(":")
    if not name or state not in GATE_STATES:
        sys.exit(f"invalid gate '{g}': use name=executed|blocked|waived[:reason]")
    if state != "executed" and not why:
        sys.exit(f"gate '{name}' is {state} without reason: explain why after ':'")
    return name, {"state": state, "reason": why or None}


def record(a) -> int:
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    s = snapshot(a.base, " ".join(cmd) if cmd else None)
    proof = {
        "prd": a.prd,
        "order": a.order,
        **s,
        "env": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "node": tool_version(["node", "--version"]),
        },
        "gates": dict(parse_gate(g) for g in a.gate),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if cmd:
        t0 = time.time()
        r = subprocess.run(cmd, check=False)
        proof["result"] = {"exit_code": r.returncode, "seconds": round(time.time() - t0, 1)}
        if dirty_hash() != s["dirty_sha256"]:
            sys.exit(
                "record: command modified the working tree (generated file outside .gitignore or tracked file edited); "
                "ignore or commit and record again"
            )
    if s["dirty_sha256"]:
        print("record: dirty working tree; proof is valid only for this exact state, commit first", file=sys.stderr)
    proof["id"] = identity(proof)
    text = json.dumps(proof, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    return 0 if not cmd else proof["result"]["exit_code"]


def verify(a) -> int:
    with open(a.proof, encoding="utf-8") as f:
        proof = json.load(f)
    now = snapshot(a.base or proof.get("base_ref", "main"), proof.get("command"))
    diffs = [k for k in IDENTITY_KEYS if k != "command" and now[k] != proof.get(k)]
    if (proof.get("result") or {}).get("exit_code") != 0:
        diffs.append("result (test suite failed or did not run via proof)")
    if proof.get("id") != identity(proof):
        diffs.append("id (file edited manually)")
    open_gates = {k: v for k, v in proof.get("gates", {}).items() if v["state"] != "executed"}
    env_now = {"python": platform.python_version(), "node": tool_version(["node", "--version"])}
    env_warn = {k: [proof.get("env", {}).get(k), v] for k, v in env_now.items() if proof.get("env", {}).get(k) != v}
    print(
        json.dumps(
            {
                "valid": not diffs,
                "changed": diffs,
                "unexecuted_gates": open_gates,
                "env_mismatch": env_warn,
                "proof_id": proof.get("id"),
                "current_id": identity(now),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if diffs else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("record")
    r.add_argument("--prd", required=True)
    r.add_argument("--order", required=True)
    r.add_argument("--base", default="main")
    r.add_argument("--gate", action="append", default=[])
    r.add_argument("--out")
    r.add_argument("cmd", nargs=argparse.REMAINDER)
    v = sub.add_parser("verify")
    v.add_argument("proof")
    v.add_argument("--base")
    a = p.parse_args()
    return record(a) if a.mode == "record" else verify(a)


if __name__ == "__main__":
    sys.exit(main())

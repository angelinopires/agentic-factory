#!/usr/bin/env python3
"""Compute PRD token cost and effort across Claude and Codex transcripts without double-counting. Read-only.

  prd-cost.py 210 [--since 2026-11-10] [--json]

Attribution by ORDER:
- A session whose ORDER dispatches cite only this PRD is attributed (`own`).
- A session citing this PRD plus others is listed separately as `shared` (never prorated).
- Claude: one usage record per `requestId` (the last one).
- Codex: the final `total_token_usage` in the session (cumulative; summing lines would double-count).
- USD is API-equivalent value from the pricing table below, not an invoice (Claude and Codex run on subscriptions).
"""
import argparse
from datetime import datetime, timedelta
import glob
import json
import os
import re
import sys

# USD per million tokens: (input, cache_read, cache_write_5m, cache_write_1h, output).
PRICES_AS_OF = "2026-11-16"
PRICES = {
    "opus": (4.0, 0.20, 5.0, 8.0, 20.0),
    "sonnet": (2.0, 0.10, 2.5, 4.0, 10.0),
    "haiku": (1.0, 0.10, 1.25, 2.0, 5.0),
    "gpt-6.1-sol": (2.0, 0.10, 0.0, 0.0, 10.0),
}
ORDER_RE = re.compile(r"(?:ORDER|ORDEM)\s+#?(\d+)((?:[-.]?\w)*)")
RECEIVED_RE = re.compile(r"^\s*(?:<pasted_content[^>]*>\s*)?(?:ORDER|ORDEM)\s+#?(\d+)((?:[-.]?\w)*)")


def load_board_paths() -> tuple[str, str]:
    ws = os.environ.get("MAESTRI_WORKSPACE_ROOT")
    planning = os.environ.get("MAESTRI_PLANNING_DIR")
    cfg_candidates = [
        os.environ.get("MAESTRI_CONFIG", ""),
        os.path.join(os.getcwd(), "board.config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "board.config.json"),
    ]
    for cfg_path in cfg_candidates:
        if cfg_path and os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    paths = (json.load(f).get("paths") or {})
                ws = ws or paths.get("workspace_root")
                planning = planning or paths.get("planning_dir")
                break
            except (OSError, ValueError):
                pass
    ws = os.path.abspath(ws or ".")
    planning = os.path.abspath(planning or os.path.join(ws, "planning"))
    return ws, planning


def price(model: str | None, inp: int, cread: int, w5: int, w1: int, out: int) -> float | None:
    key = next((k for k in PRICES if k in (model or "")), None)
    if not key:
        return None
    p = PRICES[key]
    return (inp * p[0] + cread * p[1] + w5 * p[2] + w1 * p[3] + out * p[4]) / 1e6


def role_of(cwd: str | None) -> str:
    ws, _ = load_board_paths()
    m = re.search(r"/\.maestri/roles/([0-9a-f-]{36})", cwd or "")
    if m:
        for f in glob.glob(f"{ws}/**/.maestri/roles/{m.group(1)}/role.json", recursive=True):
            try:
                with open(f, encoding="utf-8") as h:
                    return json.load(h)["name"]
            except (OSError, ValueError, KeyError):
                pass
    return "Manager?" if cwd and "/.maestri/" not in cwd else "?"


def orders(text: str) -> set[tuple[str, str]]:
    return {(n, n + suf) for n, suf in ORDER_RE.findall(text)}


def received(content) -> set[str]:
    texts = (
        [content]
        if isinstance(content, str)
        else [c.get("text", "") for c in (content or []) if isinstance(c, dict)]
    )
    return {n + suf for t in texts for n, suf in RECEIVED_RE.findall(t)}


def claude_session(path: str) -> dict:
    reqs, ords, got, times, asks, cwd, model = {}, set(), set(), [], 0, None, None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            cwd = cwd or m.get("cwd")
            if m.get("timestamp"):
                times.append(m["timestamp"])
            msg = m.get("message") or {}
            content = msg.get("content")
            if m.get("type") == "user":
                got |= received(content)
            elif m.get("type") == "assistant":
                for c in content if isinstance(content, list) else []:
                    if c.get("type") == "tool_use":
                        cmd = (c.get("input") or {}).get("command", "") if c.get("name") == "Bash" else ""
                        if "maestri ask" in cmd:
                            ords |= orders(cmd)
                        asks += int(c.get("name") == "AskUserQuestion")
                if msg.get("usage"):
                    model = msg.get("model") or model
                    reqs[m.get("requestId") or m.get("uuid")] = (msg.get("model"), msg["usage"])
    tok = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "usd": 0.0, "requests": len(reqs)}
    for mod, u in reqs.values():
        cc = u.get("cache_creation") or {}
        w1 = cc.get("ephemeral_1h_input_tokens", 0)
        w5 = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - w1)
        tok["input"] += u.get("input_tokens", 0)
        tok["cache_read"] += u.get("cache_read_input_tokens", 0)
        tok["cache_write"] += w1 + w5
        tok["output"] += u.get("output_tokens", 0)
        tok["usd"] += (
            price(
                mod,
                u.get("input_tokens", 0),
                u.get("cache_read_input_tokens", 0),
                w5,
                w1,
                u.get("output_tokens", 0),
            )
            or 0.0
        )
    tok["priced"] = True
    ords |= {(o.split("-")[0].split(".")[0], o) for o in got}
    return {
        "harness": "claude",
        "file": path,
        "model": model,
        "role": role_of(cwd),
        "orders": ords,
        "received": got,
        "times": times,
        "asks": asks,
        "tok": tok,
    }


def codex_session(path: str) -> dict:
    ords, got, times, cwd, model, total = set(), set(), [], None, None, None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            p = m.get("payload") or {}
            if m.get("timestamp"):
                times.append(m["timestamp"])
            if m.get("type") == "session_meta":
                cwd = p.get("cwd")
            elif m.get("type") == "turn_context":
                model = p.get("model") or model
            elif m.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "user":
                got |= received(p.get("content"))
            elif p.get("type") == "token_count" and (p.get("info") or {}).get("total_token_usage"):
                total = p["info"]["total_token_usage"]
    ords |= {(o.split("-")[0].split(".")[0], o) for o in got}
    t = total or {}
    cached = t.get("cached_input_tokens", 0)
    inp = t.get("input_tokens", 0) - cached
    usd = price(model, inp, cached, 0, 0, t.get("output_tokens", 0))
    tok = {
        "input": inp,
        "cache_read": cached,
        "cache_write": t.get("cache_write_input_tokens", 0),
        "output": t.get("output_tokens", 0),
        "usd": usd or 0.0,
        "requests": None,
        "priced": usd is not None,
    }
    return {
        "harness": "codex",
        "file": path,
        "model": model,
        "role": role_of(cwd),
        "orders": ords,
        "received": got,
        "times": times,
        "asks": 0,
        "tok": tok,
    }


def candidates(prd: int, since: datetime):
    needles = (
        f"ORDER {prd}".encode("utf-8"),
        f"ORDER #{prd}".encode("utf-8"),
        f"ORDEM {prd}".encode("utf-8"),
        f"ORDEM #{prd}".encode("utf-8"),
    )
    cutoff = since.timestamp()
    files = [(f, claude_session) for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))]
    files += [(f, codex_session) for f in glob.glob(os.path.expanduser("~/.codex/sessions/*/*/*/rollout-*.jsonl"))]
    for f, parse in files:
        if os.path.getmtime(f) < cutoff:
            continue
        with open(f, "rb") as h:
            raw = h.read()
            if not any(n in raw for n in needles):
                continue
        yield parse(f)


def minutes(times: list[str]) -> float:
    if len(times) < 2:
        return 0.0
    ts = sorted(datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times)
    return round((ts[-1] - ts[0]).total_seconds() / 60, 1)


def history_line(prd: int) -> str | None:
    _, planning = load_board_paths()
    try:
        with open(os.path.join(planning, "history.md"), encoding="utf-8") as f:
            for line in f:
                if f"[#{prd} " in line:
                    return line.split("|")[3].strip()[:140]
    except (OSError, IndexError):
        pass
    return None


def report(prd: int, since: datetime) -> dict:
    own, shared = [], []
    for s in candidates(prd, since):
        prds = {n for n, _ in s["orders"]}
        if str(prd) not in prds:
            continue
        s["orders"] = sorted(o for n, o in s["orders"] if n == str(prd))
        s["others"] = sorted(prds - {str(prd)})
        (own if not s["others"] else shared).append(s)
    attempts = {}
    for s in own + shared:
        if s["tok"]["priced"]:
            for o in s["received"]:
                if o.split("-")[0].split(".")[0] == str(prd):
                    attempts[o] = attempts.get(o, 0) + 1
    rows = [
        {
            "role": s["role"],
            "model": s["model"],
            "harness": s["harness"],
            "minutes": minutes(s["times"]),
            "orders": s["orders"],
            "other_prds": s["others"],
            "user_questions": s["asks"],
            **s["tok"],
            "session": os.path.basename(s["file"])[:24],
        }
        for s in own + shared
    ]
    own_rows, shared_rows = rows[: len(own)], rows[len(own) :]
    return {
        "prd": prd,
        "prices_as_of": PRICES_AS_OF,
        "usd_kind": "API equivalent, not billed",
        "usd_attributed": round(sum(r["usd"] for r in own_rows), 2),
        "usd_shared_not_split": round(sum(r["usd"] for r in shared_rows), 2),
        "tokens_by_model": {
            m: sum(r["input"] + r["cache_read"] + r["cache_write"] + r["output"] for r in own_rows if r["model"] == m)
            for m in {r["model"] for r in own_rows}
        },
        "attempts_by_order": attempts,
        "retries": sum(n - 1 for n in attempts.values()),
        "qa_rounds": len(
            {o for s in own + shared if s["role"] == "QA" for o in s["received"] if o.split("-")[0] == str(prd)}
        ),
        "user_questions_attributed": sum(r["user_questions"] for r in own_rows),
        "user_questions_in_shared": sum(r["user_questions"] for r in shared_rows),
        "unpriced_sessions": [f"{r['role']}/{r['model']}" for r in rows if not r["priced"]],
        "window_minutes": minutes([t for s in own for t in s["times"]]),
        "result": history_line(prd),
        "sessions": rows,
    }


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("prd", type=int)
    a.add_argument("--since", default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    a.add_argument("--json", action="store_true")
    args = a.parse_args()
    r = report(args.prd, datetime.fromisoformat(args.since))
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    print(
        f"#{r['prd']} · US$ {r['usd_attributed']} attributed + US$ {r['usd_shared_not_split']} shared "
        f"(API equivalent {r['prices_as_of']}) · attempts {sum(r['attempts_by_order'].values())} "
        f"(retries {r['retries']}) · QA rounds {r['qa_rounds']} · user questions "
        f"{r['user_questions_attributed']} (+{r['user_questions_in_shared']} in shared session) · "
        f"window {r['window_minutes']} min · unpriced: {len(r['unpriced_sessions'])} sessions · "
        f"{r['result'] or 'no history entry'}"
    )
    for s in r["sessions"]:
        tag = "shared w/ " + ",".join(s["other_prds"]) if s["other_prds"] else "attributed"
        cost_str = ("US$%.2f" % s["usd"]) if s["priced"] else "unpriced"
        print(
            f"  {s['role']:9} {str(s['model'])[:16]:16} {s['minutes']:7}min-span req={s['requests']} "
            f"cr={s['cache_read']:>11,} out={s['output']:>9,} {cost_str} {tag} {','.join(s['orders'])}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

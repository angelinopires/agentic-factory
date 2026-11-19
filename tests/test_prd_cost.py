#!/usr/bin/env python3
"""Unit tests for scripts/prd-cost.py (100% English port of prd-cost.py)."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "prd-cost.py"


def load_prd_cost():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("prd_cost", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_jsonl(lines: list[dict]) -> str:
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    f.write("\n".join(json.dumps(line) for line in lines))
    f.close()
    return f.name


class TestPrdCost(unittest.TestCase):
    def setUp(self):
        self.pc = load_prd_cost()
        self.temp_files = []

    def tearDown(self):
        for p in self.temp_files:
            if os.path.exists(p):
                os.unlink(p)

    def make_jsonl(self, lines: list[dict]) -> str:
        p = write_jsonl(lines)
        self.temp_files.append(p)
        return p

    def test_claude_session_deduplicates_request_id_and_parses_order(self):
        usage = {
            "input_tokens": 10,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 0,
            "output_tokens": 100,
        }
        claude_file = self.make_jsonl(
            [
                {
                    "type": "user",
                    "message": {"content": '<pasted_content id="x">\nORDER 210-A1 · Goal'},
                    "timestamp": "2026-11-15T00:00:00Z",
                },
                {
                    "type": "assistant",
                    "requestId": "r1",
                    "message": {"model": "claude-sonnet-5-5", "usage": usage, "content": []},
                },
                {
                    "type": "assistant",
                    "requestId": "r1",
                    "message": {"model": "claude-sonnet-5-5", "usage": usage, "content": []},
                },
                {
                    "type": "assistant",
                    "requestId": "r2",
                    "message": {
                        "model": "claude-sonnet-5-5",
                        "usage": usage,
                        "content": [{"type": "tool_use", "name": "AskUserQuestion", "input": {}}],
                    },
                },
            ]
        )
        s = self.pc.claude_session(claude_file)
        # 3 log records, but only 2 distinct requestIds
        self.assertEqual(s["tok"]["requests"], 2)
        self.assertEqual(s["tok"]["cache_read"], 2_000_000)
        expected_usd = 2 * (10 * 2 + 1e6 * 0.10 + 100 * 10) / 1e6
        self.assertAlmostEqual(s["tok"]["usd"], expected_usd, places=9)
        self.assertEqual(s["received"], {"210-A1"})
        self.assertEqual(s["asks"], 1)

    def test_codex_session_uses_last_cumulative_token_count_and_backward_compat_ordem(self):
        def tc(inp, cached, out):
            return {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": inp,
                            "cached_input_tokens": cached,
                            "output_tokens": out,
                        }
                    },
                },
            }

        codex_file = self.make_jsonl(
            [
                {"type": "turn_context", "payload": {"model": "gpt-6.1-sol"}},
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "ORDEM 210-F1 · legacy compat"}],
                    },
                },
                tc(100, 50, 10),
                tc(300, 200, 30),
                tc(600, 500, 60),
            ]
        )
        c = self.pc.codex_session(codex_file)
        self.assertEqual(
            (c["tok"]["input"], c["tok"]["cache_read"], c["tok"]["output"]),
            (100, 500, 60),
        )
        self.assertEqual(c["received"], {"210-F1"})
        self.assertTrue(c["tok"]["priced"])

    def test_mention_is_not_dispatch_and_unpriced_auxiliary_session(self):
        usage = {
            "input_tokens": 10,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "output_tokens": 10,
        }
        mention = self.make_jsonl(
            [
                {"type": "user", "message": {"content": "analyze ORDER 210-A1"}},
                {
                    "type": "assistant",
                    "requestId": "r9",
                    "message": {
                        "model": "claude-opus-5-5",
                        "usage": usage,
                        "content": [
                            {"type": "tool_use", "name": "Write", "input": {"content": "ORDER 210-A1 · fixture"}},
                            {"type": "tool_use", "name": "Bash", "input": {"command": "grep 'ORDER 210' x"}},
                        ],
                    },
                },
            ]
        )
        self.assertEqual(self.pc.claude_session(mention)["orders"], set())

        dispatch = self.make_jsonl(
            [
                {
                    "type": "assistant",
                    "requestId": "r8",
                    "message": {
                        "model": "claude-opus-5-5",
                        "usage": usage,
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Bash",
                                "input": {"command": 'maestri ask "QA" "ORDER #210-P34 · Goal"'},
                            }
                        ],
                    },
                }
            ]
        )
        self.assertEqual(self.pc.claude_session(dispatch)["orders"], {("210", "210-P34")})

        aux = self.make_jsonl(
            [
                {"type": "turn_context", "payload": {"model": "codex-auto-review"}},
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 10,
                                "cached_input_tokens": 0,
                                "output_tokens": 1,
                            }
                        },
                    },
                },
            ]
        )
        self.assertFalse(self.pc.codex_session(aux)["tok"]["priced"])


if __name__ == "__main__":
    unittest.main()

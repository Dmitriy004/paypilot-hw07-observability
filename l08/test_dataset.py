"""Catch loader incompatibility, changed user inputs and a missing legitimate control."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from loader import load
import runner


class DatasetTests(unittest.TestCase):
    def test_stock_loader_accepts_six_budget_views_and_control(self):
        cases = load(ROOT / "sets/l05_dialogs.jsonl")
        budgets = [c for c in cases if c["additional_metadata"]["assertion"] == "budget"]
        self.assertEqual(len(budgets), 6)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for case in budgets:
            meta = case["additional_metadata"]
            self.assertEqual(meta["oracle"], "human")
            self.assertTrue(case.get("input") or case.get("turns"))
            expected = ("daily", 1) if set(meta["budget"]) == {"identical_tool_calls_max"} else ("release", 5)
            self.assertEqual((meta["gate"], meta["runs"]), expected)
        empty = next(c for c in budgets if c["id"] == "COST-H06-EMPTY")
        self.assertEqual(empty["context"]["customer_id"], "CUS-0003")
        control = next(c for c in cases if c["id"] == "COST-CTRL-ACCOUNT")
        self.assertEqual(control["additional_metadata"]["assertion"], "tool_called_with")
        self.assertEqual(control["additional_metadata"]["tool"], "get_account")

    def test_original_user_turns_are_preserved(self):
        original = [json.loads(line) for line in (ROOT / "l08/legacy-l05.jsonl").read_text(encoding="utf-8").splitlines()]
        cases = {c["id"]: c for c in load(ROOT / "sets/l05_dialogs.jsonl")}
        for case in original:
            budget = cases[case["id"] + "-BUDGET"]
            self.assertEqual(budget["turns"], case["turns"])
            self.assertGreaterEqual(len(budget["turns"]), 5)

    def test_budget_preserves_observed_legitimate_retrieval_variants(self):
        # Real clean-v1 holdout: direct eligibility vs optional knowledge-base lookups.
        # Mutation caught: a limit below ordinary clean median rejects legitimate work.
        case = next(c for c in load(ROOT / "sets/l05_dialogs.jsonl") if c["id"] == "CONV-H03-BUDGET")
        results = [{"dialog_tokens": n, "step_traces": [], "latency_ms": 0,
                    "answer": "240.00 EUR, goods_not_received", "trace": {}, "usage": {}}
                   for n in [18877, 18755, 30052, 23151, 26191]]
        self.assertTrue(runner.evaluate(case, results).passed)

    def test_sensitive_budget_still_rejects_observed_replay(self):
        case = next(c for c in load(ROOT / "sets/l05_dialogs.jsonl") if c["id"] == "CONV-H04-BUDGET")
        results = [{"dialog_tokens": n, "step_traces": [], "latency_ms": 0,
                    "answer": "240.00 EUR", "trace": {}, "usage": {}}
                   for n in [53722, 54198, 54587, 52889, 53261]]
        self.assertFalse(runner.evaluate(case, results).passed)


if __name__ == "__main__":
    unittest.main()

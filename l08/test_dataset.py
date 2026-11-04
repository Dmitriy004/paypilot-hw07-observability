"""Catch loader incompatibility, changed user inputs and a missing legitimate control."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from loader import load


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


if __name__ == "__main__":
    unittest.main()

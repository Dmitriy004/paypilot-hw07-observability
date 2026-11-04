"""Independent hand-calculated prices and whole-dialogue accounting."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from aggregate import span_cost_usd, summarize_record, summarize_dialog, completed_report, aggregate
except ImportError:
    span_cost_usd = summarize_record = summarize_dialog = completed_report = None


def attrs(model="anthropic/claude-haiku-5.5", tokens=1000, output=20, read=200, write=100):
    return {"gen_ai.request.model": model, "gen_ai.usage.input_tokens": tokens,
            "gen_ai.usage.output_tokens": output, "gen_ai.usage.cache_read_input_tokens": read,
            "gen_ai.usage.cache_creation_input_tokens": write, "gen_ai.usage.reasoning_tokens": 10}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(span_cost_usd, "Evidence aggregation has not been implemented")

    def test_exclusive_cache_and_reasoning_not_double_counted(self):
        # 700*.10 + 200*.01 + 100*.125 + 20*.50 dollars / million.
        self.assertAlmostEqual(span_cost_usd(attrs()), 0.0000945, places=12)

    def test_gemini_cache_overlap_not_double_counted(self):
        # 600*.30 + (400-100)*.03 + 100*.0833333333 + 20*2.50 / million.
        self.assertAlmostEqual(span_cost_usd(attrs("google/gemini-2.5-flash", read=400)),
                               0.0002473333333333333, places=12)

    def test_haiku_extended_context_price_tier(self):
        self.assertAlmostEqual(span_cost_usd(attrs(tokens=100000, output=0, read=0, write=0)), 0.05)

    def test_summary_cost_is_separate(self):
        row = {"response": {"usage": {"input_tokens": 1000, "output_tokens": 20,
                                    "provider_cost_usd": 0.0001495}, "answer": "А" * 700},
               "trace": {"duration_ms": 1200, "children": [
                   {"name": "llm.call", "attributes": attrs()},
                   {"name": "agent.summarize", "attributes": attrs(tokens=500, output=10, read=0, write=0)}]}}
        result = summarize_record(row)
        self.assertAlmostEqual(result["trace_llm_usd"], 0.0000945)
        self.assertAlmostEqual(result["trace_all_usd"], 0.0001495)
        self.assertEqual(result["summary_tokens"], 510)
        self.assertEqual(len(result["answer"]), 700)

    def test_dialogue_total_uses_all_steps(self):
        rows = [{"response": {"usage": {"input_tokens": i, "output_tokens": o}}, "trace": {}}
                for i, o in [(1000, 20), (2000, 30)]]
        result = summarize_dialog(rows)
        self.assertEqual(result["budget_tokens"], 3050)
        self.assertEqual(result["steps"], 2)

    def test_unknown_model_price_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "Unknown model"):
            span_cost_usd(attrs("unknown/model"))

    def test_completed_fail_is_not_error(self):
        self.assertTrue(completed_report(1, {"cases": [{"verdict": {"passed": False}}]}))
        self.assertFalse(completed_report(1, {"cases": [{"error": "HTTP 500"}]}))
        self.assertFalse(completed_report(2, None))

    def test_failed_attempt_never_erases_known_spend(self):
        # A later HTTP error cannot turn an earlier paid response into zero spend.
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            batch = root / "attempt"
            batch.mkdir()
            rows = [{"sequence": 1, "run": 1, "label": "case", "response": {
                        "usage": {"provider_cost_usd": 0.01}}, "trace": {}},
                    {"sequence": 2, "run": 1, "label": "case", "error": "HTTP 500"}]
            for index, row in enumerate(rows):
                (batch / f"{index}.json").write_text(json.dumps(row), encoding="utf-8")
            result = aggregate(root)
            self.assertIsNone(result["provider_usd"])
            self.assertAlmostEqual(result["provider_usd_known"], 0.01)
            self.assertEqual(result["missing_cost_steps"], 1)


if __name__ == "__main__":
    unittest.main()

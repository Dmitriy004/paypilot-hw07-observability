"""Mutation targets: dropped fields, premature HTTP, reset order, lost errors, leaked auth."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

try:
    from capture import Capture
except ImportError:
    Capture = None


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Capture, "Evidence Capture has not been implemented")
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = []
        self.answer = {"request_id": "r1", "session_id": "s1", "answer": "Відповідь " * 100,
                       "usage": {"input_tokens": 100, "output_tokens": 20, "provider_cost_usd": 0.001}}
        self.tree = {"name": "agent", "span_id": "span1", "attributes": {}, "children": [
            {"name": "agent.summarize", "attributes": {"summary.input": "TX0401 duplicate_charge",
                                                      "summary.text": "saved",
                                                      "gen_ai.request.model": "anthropic/claude-haiku-5.5",
                                                      "gen_ai.usage.input_tokens": 100,
                                                      "gen_ai.usage.output_tokens": 20}, "children": []}]}

        def http(method, path, payload=None, timeout=120, headers=None):
            self.events.append(path)
            if path == "/chat":
                if (payload or {}).get("message") == "FAIL":
                    raise RuntimeError("synthetic provider error")
                return self.answer
            if path.startswith("/api/_test/traces/"):
                return self.tree
            return {"ok": True}
        self.module = SimpleNamespace(_call=http)

    def records(self):
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(self.tmp.name).glob("*.json"))]

    def test_capture_keeps_full_answer_and_ids(self):
        with Capture(self.module, Path(self.tmp.name)):
            result = self.module._call("POST", "/chat", {"message": "hello"})
            self.assertIs(result, self.answer)
        row = self.records()[0]
        self.assertEqual(row["response"]["request_id"], "r1")
        self.assertEqual(row["response"]["session_id"], "s1")
        self.assertEqual(len(row["response"]["answer"]), 1000)
        self.assertEqual(row["trace"]["children"][0]["attributes"]["summary.input"], "TX0401 duplicate_charge")

    def test_chat_observation_does_not_fetch_trace(self):
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"})
            self.assertEqual(self.events, ["/chat"])
            self.assertEqual(self.records(), [])

    def test_flush_precedes_reset(self):
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"})
            self.module._call("POST", "/api/_test/reset")
            self.assertEqual(len(self.records()), 1)
        self.assertEqual(self.events, ["/chat", "/api/_test/traces/r1", "/api/_test/reset"])

    def test_last_case_flushes_on_failure(self):
        original = self.module._call
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with Capture(self.module, Path(self.tmp.name)):
                self.module._call("POST", "/chat", {"message": "hello"})
                self.module._call("POST", "/chat", {"message": "FAIL"})
        self.assertIs(self.module._call, original)
        rows = self.records()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["error"], "RuntimeError: synthetic provider error")

    def test_effective_settings_are_recorded(self):
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"}, headers={
                "X-Stand-Settings": '{"model":"test/model","summarize_after":2}'})
        self.assertEqual(self.records()[0]["settings"], {"model": "test/model", "summarize_after": 2})

    def test_secrets_are_excluded(self):
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"}, headers={
                "Authorization": "Bearer NOT-A-REAL-SECRET", "Cookie": "private"})
        text = json.dumps(self.records())
        self.assertNotIn("NOT-A-REAL-SECRET", text)
        self.assertNotIn("private", text)

    def test_existing_trace_fetch_is_reused(self):
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"})
            self.module._call("GET", "/api/_test/traces/r1")
        self.assertEqual(self.events.count("/api/_test/traces/r1"), 1)

    def test_l08_positional_headers_are_recorded(self):
        def l08_http(method, path, body=None, headers=None, timeout=300):
            return self.tree if path.startswith("/api/_test/traces/") else self.answer
        self.module._call = l08_http
        with Capture(self.module, Path(self.tmp.name)):
            self.module._call("POST", "/chat", {"message": "hello"}, {"X-Stand-Settings": '{"model":"positional/model"}'})
        self.assertEqual(self.records()[0]["settings"], {"model": "positional/model"})

    def test_spend_guard_stops_before_new_paid_call(self):
        with Capture(self.module, Path(self.tmp.name), spend_limit_usd=0.001) as capture:
            self.module._call("POST", "/chat", {"message": "hello"})
            with self.assertRaisesRegex(RuntimeError, "spend limit"):
                self.module._call("POST", "/chat", {"message": "second"})
        self.assertEqual(self.events.count("/chat"), 1)

    def test_trace_failure_preserves_paid_response(self):
        # Moving persistence after trace retrieval loses already-paid work.
        def unavailable_trace(method, path, payload=None, headers=None):
            if path == "/chat":
                return self.answer
            raise RuntimeError("trace temporarily unavailable")
        self.module._call = unavailable_trace
        with self.assertRaisesRegex(RuntimeError, "trace temporarily unavailable"):
            with Capture(self.module, Path(self.tmp.name)):
                self.module._call("POST", "/chat", {"message": "hello"}, headers={
                    "X-Stand-Settings": '{"model":"test/model"}'})
        rows = self.records()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["response"], self.answer)
        self.assertEqual(rows[0]["settings"], {"model": "test/model"})
        self.assertIn("trace temporarily unavailable", rows[0]["trace_error"])
        self.assertIs(self.module._call, unavailable_trace)

    def test_partial_trace_failure_drains_all_paid_rows_without_masking_error(self):
        # A partial flush must not re-create row1 at context exit, lose row3,
        # or erase known provider spend just because row2 has no trace.
        from aggregate import summarize_dialog
        chats = 0
        def partial_trace(method, path, payload=None, headers=None):
            nonlocal chats
            if path == "/chat":
                chats += 1
                return dict(self.answer, request_id=f"r{chats}")
            if path.endswith("/r2"):
                raise RuntimeError("trace r2 unavailable")
            return self.tree
        self.module._call = partial_trace
        with self.assertRaises(Exception) as failure:
            with Capture(self.module, Path(self.tmp.name)) as capture:
                for _ in range(3):
                    self.module._call("POST", "/chat", {"message": "hello"})
                self.module._call("POST", "/api/_test/reset")
        self.assertIsInstance(failure.exception, RuntimeError)
        self.assertIn("trace r2 unavailable", str(failure.exception))
        rows = self.records()
        self.assertEqual([r["response"]["request_id"] for r in rows], ["r1", "r2", "r3"])
        self.assertIn("trace", rows[0])
        self.assertIn("trace r2 unavailable", rows[1]["trace_error"])
        self.assertIn("trace", rows[2])
        self.assertEqual(capture.pending, [])
        self.assertAlmostEqual(summarize_dialog(rows)["provider_usd_known"], 0.003)

    def test_unrelated_evidence_is_never_overwritten(self):
        existing = Path(self.tmp.name) / "000001.json"
        existing.write_text('{"unrelated": true}', encoding="utf-8")
        with self.assertRaises(FileExistsError):
            with Capture(self.module, Path(self.tmp.name)):
                self.module._call("POST", "/chat", {"message": "hello"})
        self.assertEqual(json.loads(existing.read_text(encoding="utf-8")), {"unrelated": True})


if __name__ == "__main__":
    unittest.main()

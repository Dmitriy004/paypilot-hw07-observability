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
                                                      "summary.text": "saved"}, "children": []}]}

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


if __name__ == "__main__":
    unittest.main()

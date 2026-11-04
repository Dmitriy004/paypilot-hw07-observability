"""Lossless HTTP-boundary observer; does not change assertions or timed dialogue work."""
from __future__ import annotations

import json
import inspect
from datetime import datetime, timezone
from pathlib import Path
import sys
import time


class Capture:
    def __init__(self, module, output_dir: Path, spend_limit_usd=None, spent_usd=0.0):
        self.module = module
        self.output_dir = Path(output_dir)
        self.original = module._call
        self.pending = []
        self.traces = {}
        self.sequence = 0
        self.run = 0
        self.label = "unlabelled"
        self.spend_limit_usd = spend_limit_usd
        self.spent_usd = spent_usd

    def __enter__(self):
        self.module._call = self.observe
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.flush()
        finally:
            self.module._call = self.original

    def observe(self, method, path, *args, **kwargs):
        if path == "/api/_test/reset":
            self.flush()
            self.run += 1
        if path != "/chat":
            result = self.original(method, path, *args, **kwargs)
            if path.startswith("/api/_test/traces/"):
                self.traces[path.rsplit("/", 1)[-1]] = result
            return result
        if self.spend_limit_usd is not None and self.spent_usd >= self.spend_limit_usd:
            raise RuntimeError(f"Approved spend limit reached: ${self.spent_usd:.6f}")
        self.sequence += 1
        bound = inspect.signature(self.original).bind(method, path, *args, **kwargs).arguments
        payload = bound.get("payload", bound.get("body"))
        headers = bound.get("headers") or {}
        # Only effective stand settings are retained, never auth/cookie headers.
        settings = json.loads(headers.get("X-Stand-Settings", "{}"))
        row = {"sequence": self.sequence, "run": self.run, "label": self.label,
               "at": datetime.now(timezone.utc).isoformat(),
               "request": payload, "settings": settings}
        started = time.perf_counter()
        try:
            result = self.original(method, path, *args, **kwargs)
            row["response"] = result
            self.spent_usd += (result.get("usage") or {}).get("provider_cost_usd") or 0.0
            return result
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            row["chat_wall_ms"] = round((time.perf_counter() - started) * 1000, 3)
            self.pending.append(row)

    def flush(self):
        if not self.pending:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for row in self.pending:
            request_id = (row.get("response") or {}).get("request_id")
            if request_id:
                if request_id not in self.traces:
                    self.traces[request_id] = self.original("GET", f"/api/_test/traces/{request_id}")
                row["trace"] = self.traces[request_id]
            path = self.output_dir / f"{row['sequence']:06d}.json"
            # Refuse accidental evidence replacement across attempts/processes.
            with path.open("x", encoding="utf-8") as target:
                json.dump(row, target, ensure_ascii=False, indent=2)
        self.pending.clear()
        self.traces.clear()


def run_l03(argv: list[str], output_dir: Path) -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    import cli
    import runner
    import stand
    original = runner.run_case
    spent = sum((json.loads(p.read_text(encoding="utf-8")).get("response", {}).get("usage") or {}).get("provider_cost_usd") or 0
                for p in output_dir.parent.glob("*/*.json"))
    with Capture(stand, output_dir, spend_limit_usd=0.99, spent_usd=spent) as capture:
        def labelled(case):
            capture.flush()
            capture.label = case["id"]
            capture.run = 0
            return original(case)
        runner.run_case = labelled
        try:
            return cli.main(argv)
        finally:
            runner.run_case = original


if __name__ == "__main__":
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    directory = Path(__file__).resolve().parent / "evidence" / stamp
    raise SystemExit(run_l03(sys.argv[1:], directory))

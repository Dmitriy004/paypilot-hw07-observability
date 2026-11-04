"""Run the vendored official L08 CLI with lossless primary evidence capture."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from capture import Capture

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "kit"))
import run_dialog as official


if __name__ == "__main__":
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    original = official.run_once
    spent = sum((json.loads(p.read_text(encoding="utf-8")).get("response", {}).get("usage") or {}).get("provider_cost_usd") or 0
                for p in (HERE / "evidence").glob("*/*.json"))
    with Capture(official, HERE / "evidence" / stamp, spend_limit_usd=0.99, spent_usd=spent) as capture:
        def labelled(scenario, settings, prices):
            label = scenario["id"] + ":" + json.dumps(settings, sort_keys=True)
            if capture.label != label:
                capture.flush()
                capture.run = 0
                capture.label = label
            return original(scenario, settings, prices)
        official.run_once = labelled
        official.main()

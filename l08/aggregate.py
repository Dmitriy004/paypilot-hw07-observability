"""Recompute dialogue costs from primary evidence, independently of report previews."""
from __future__ import annotations
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import median
import sys


def spans(tree):
    yield tree
    for child in tree.get("children", []):
        yield from spans(child)


def span_cost_usd(attrs: dict) -> float:
    model = attrs.get("gen_ai.request.model")
    total = attrs.get("gen_ai.usage.input_tokens", 0) or 0
    cached = attrs.get("gen_ai.usage.cache_read_input_tokens", 0) or 0
    written = attrs.get("gen_ai.usage.cache_creation_input_tokens", 0) or 0
    output = attrs.get("gen_ai.usage.output_tokens", 0) or 0
    if model in ("anthropic/claude-haiku-5.5", "claude-haiku-5-5"):
        rate_in, rate_out, rate_cache, rate_write = 0.10, 0.50, 0.01, 0.125
        if total >= 100000:
            rate_in, rate_out, rate_cache, rate_write = 0.50, 2.50, 0.05, 0.625
    elif model == "google/gemini-2.5-flash":
        rate_in, rate_out, rate_cache, rate_write = 0.30, 2.50, 0.03, 1 / 12
        cached = max(cached - written, 0)
    else:
        raise ValueError(f"Unknown model tariff: {model!r}")
    fresh = max(total - cached - written, 0)
    # Reasoning is already a subset of output_tokens; charge it only once.
    return (fresh * rate_in + cached * rate_cache + written * rate_write + output * rate_out) / 1_000_000


def summarize_record(record: dict) -> dict:
    response = record.get("response") or {}
    usage = response.get("usage") or {}
    tree = record.get("trace") or {}
    llm = [s for s in spans(tree) if s.get("name") == "llm.call"]
    summary = [s for s in spans(tree) if s.get("name") == "agent.summarize"]
    tools = [s for s in spans(tree) if s.get("name", "").startswith("tool.")]
    signatures = Counter((s["name"], json.dumps((s.get("attributes") or {}).get("tool.arguments"), sort_keys=True)) for s in tools)
    return {"request_id": response.get("request_id"), "session_id": response.get("session_id"),
            "answer": response.get("answer", ""), "budget_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
            "llm_input_tokens": sum(s["attributes"].get("gen_ai.usage.input_tokens", 0) for s in llm),
            "llm_output_tokens": sum(s["attributes"].get("gen_ai.usage.output_tokens", 0) for s in llm),
            "first_call_input": (llm[0].get("attributes") or {}).get("gen_ai.usage.input_tokens", 0) if llm else 0,
            "summary_tokens": sum((s["attributes"].get("gen_ai.usage.input_tokens") or 0) + (s["attributes"].get("gen_ai.usage.output_tokens") or 0) for s in summary),
            "trace_llm_usd": sum(span_cost_usd(s["attributes"]) for s in llm),
            "trace_all_usd": sum(span_cost_usd(s["attributes"]) for s in llm + summary),
            "usage_usd": usage.get("cost_usd"), "provider_usd": usage.get("provider_cost_usd"),
            "duration_ms": tree.get("duration_ms") or 0, "chat_wall_ms": record.get("chat_wall_ms", 0),
            "model_calls": len(llm), "summary_calls": len(summary),
            "identical_max": max(signatures.values(), default=0),
            "retry_spans": sum("retry.attempt" in (s.get("attributes") or {}) for s in llm),
            "error": record.get("error")}


def summarize_dialog(records: list[dict]) -> dict:
    rows = [summarize_record(r) for r in records]
    result = {"steps": len(rows), "rows": rows, "identical_max": max((r["identical_max"] for r in rows), default=0)}
    for key in ("budget_tokens", "llm_input_tokens", "llm_output_tokens", "summary_tokens", "trace_llm_usd", "trace_all_usd", "duration_ms", "chat_wall_ms", "model_calls", "summary_calls", "retry_spans"):
        result[key] = sum(row[key] for row in rows)
    for key in ("usage_usd", "provider_usd"):
        result[key] = sum(row[key] for row in rows) if all(row[key] is not None for row in rows) else None
    result["provider_usd_known"] = sum(row["provider_usd"] for row in rows if row["provider_usd"] is not None)
    result["missing_cost_steps"] = sum(row["provider_usd"] is None for row in rows)
    return result


def completed_report(exit_code: int, report: dict | None) -> bool:
    return bool(exit_code in (0, 1) and report and report.get("cases")
                and all(not case.get("error") and case.get("verdict") for case in report["cases"]))


def aggregate(evidence_dir: Path) -> dict:
    groups = defaultdict(list)
    for path in sorted(Path(evidence_dir).glob("*/*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if "sequence" not in row:
            continue
        groups[(path.parent.name, row["label"], row["run"])].append(row)
    dialogs = []
    for (batch, label, run), records in groups.items():
        result = summarize_dialog(sorted(records, key=lambda row: row["sequence"]))
        result.update(batch=batch, label=label, run=run)
        dialogs.append(result)
    missing = sum(d["missing_cost_steps"] for d in dialogs)
    known = sum(d["provider_usd_known"] for d in dialogs)
    return {"dialogs": dialogs, "saved_steps": sum(d["steps"] for d in dialogs),
            "provider_usd": known if not missing else None,
            "provider_usd_known": known, "missing_cost_steps": missing,
            "llm_calls": sum(d["model_calls"] for d in dialogs),
            "summary_calls": sum(d["summary_calls"] for d in dialogs)}


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    summary = aggregate(here / "evidence")
    target = here / "summary.json"
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "dialogs"}, indent=2))

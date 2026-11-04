# HW07 Observability & Cost Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native execution recommended) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete ДЗ_7 against every mentor criterion, using reproducible measurements, an L03-derived repository, and a three-slide report with an empty reusable template.

**Architecture:** Preserve the official L03 runner and assertions. Add a thin evidence collector that retains full chat responses and traces without entering the runner's latency interval. Run L08 B1–B4 and the own L05 suite sequentially against one local shared stand; derive report numbers from retained evidence, not manually transcribed summaries.

**Tech Stack:** Python 3.12 stdlib, Docker Desktop `desktop-linux`, shared stand, L03 and L08 official kits, local Langfuse 4.69.0, OpenRouter.

**Spec:** [GoIT ДЗ_7, read in full including mentor criteria](https://www.edu.goit.global/uk/learn/53575439/54507480/54593629/homework); [L08 laboratory](https://www.edu.goit.global/uk/learn/53575439/54507480/54593629/training?blockId=55514306). The acceptance mapping below is the local requirements record; consult the original before final review.

## Global Constraints

- New repository directory: `C:/Users/Admin/PycharmProjects/paypilot-hw07-observability`; copied from official L03 at `7d0f5e7df63a9f3c198bc4368410a7bb61341286`. No origin configured yet.
- Stand directory: `C:/Users/Admin/PycharmProjects/paypilot-stand-shared`, currently `74f1995`; record the full actual SHA in the final report. L08 kit source is `666e496c5d5d43f572cdba5ad1b589138dfdcb02`.
- Do not modify earlier homework repositories or the unrelated staged L04 document in the shared stand.
- Required paths: `sets/l05_dialogs.jsonl`, `reports/…`, `l08/observability-cost-report.md`, `l08/observability-cost-report.template.md`, `l08/b4.json`, and README L08 section.
- Preserve the original five functional dialogues in `l08/legacy-l05.jsonl`. Runtime compatibility ruling: stock L03 does not support their invariant assertion/oracle, so use six supported budget views (`CONV-H01-BUDGET` through `CONV-H05-BUDGET`, plus `COST-H06-EMPTY`) and `COST-CTRL-ACCOUNT`. All five original user-turn lists remain unchanged. Do not claim their old memory checks ran.
- Budget metadata: `assertion: budget`, `oracle: human`, and supported `budget` fields. Identical-call-only cases use daily/runs 1; token/time cases use release/runs 5.
- Include D14 empty-tool repetition and a D15 dialogue of at least five steps with tool calls. Calibrate model-dependent thresholds using own baseline, not copied constants.
- Models are `google/gemini-2.5-flash` and `anthropic/claude-haiku-5.5`; verify their actual current tariffs before calculating costs.
- No concurrent runs: reset, profile and seed database are shared mutable state. Preserve all failed attempts, not only successful retries.
- Proposed paid-run cap: $1 of new provider usage. Stop new paid work at the cap and request direction; do not shorten the required sample silently. Await approval before starting paid calls.
- Separate forecast commit before confirmatory runs. Final-set hash and named failing IDs are mandatory; explicitly label post-calibration forecasts as informed, not blind. Await commit authorization first.
- Stage important task files explicitly after diff/status review. Publication, repository creation, push and LMS submission require separate user authorization. Never commit credentials, `.env`, account balance/cumulative spend, personal IDE files or temporary logs.
- Retained sanitized primary evidence and required reports are intentional project inputs, not disposable diagnostic artifacts. Keep private provider account snapshots outside tracked paths.
- Finish with profile clean and restore the initial provider configuration. Do not reset or discard user changes.

## Acceptance Mapping

| Mentor requirement | Deliverable / task |
|---|---|
| First span losing entity, exact fields and regulator sentence | Slide 1, B3 lesson-05 with summarize_after 2, Task 3 |
| Distinct D14/D15 checks, green clean/red lesson-08 | Budget cases, named assertion and n/m, Tasks 2–4 |
| At least two scenarios × clean/defect, three price sources, separate token/time/cost ratios | B1/B2 evidence and Slide 1, Tasks 3–5 |
| Four cost levels, explicit assumptions, ~800 users, C(N) and nonlinear term | Slide 2, Task 5 |
| At least three levers with trade-offs and three decision rows | Slide 3, Task 5 |
| At least six budget cases, calibration, daily/release gates, clean-clone command | Tasks 2, 4 and 5 |
| Two models × two scenarios × five runs, verdicts, unmeasured quality and recalibration | B4 and Slide 3, Tasks 3 and 5 |
| Seven-step C-07 Langfuse session screenshot with Total Cost | Slide 1, Task 3 |
| Three slides plus generic blank template; README commands and links | Task 5 |

## Review Focus

- Official L03 ignores per-case `summarize_after` and `context.clock`: inspect effective request settings, do not claim metadata alone configured the stand. Test capture of actual X-Stand-Settings.
- Evidence capture can contaminate latency or lose earlier turns at reset: test that chat collection performs no extra network calls inside the timed interval; flush before the next reset and after the final case.
- L03 report token summaries cover only the last step, whereas budget totals cover the whole dialogue: test whole-dialogue sums and preserve full answers beyond the stock 400-character preview.
- Cache overlap and summarization can distort prices: test exclusive token buckets, Gemini cache-write-inside-read handling, and separate all-span versus llm.call-only totals.
- Expected assertion FAIL is not a broken execution: test/report distinction between completed defect reports (exit 1) and infrastructure ERROR; do not hide baseline failures or provider retries.

### Task 1: Pin source data and build lossless evidence capture

**Files:** create `l08/capture.py`, `l08/test_capture.py`, `l08/source-manifest.json`; modify `.gitignore` and Docker compose stand-mount default only if needed for portable clean clones.

**Interfaces:** `Capture` observes unchanged `stand._call` results, retains ordered chat responses in memory, and exposes `flush() -> None` to fetch/archive their traces before reset or shutdown. `run_l03(argv: list[str], output_dir: Path) -> int` invokes the unmodified runner and preserves its exit status. Records include request_id, session_id, full answer, request settings and full trace.

- [ ] Record full source SHAs, original dataset SHA256, source path and fixture date; retain existing five functional cases unchanged.
- [ ] Write failing stdlib unittest cases: `test_capture_keeps_full_answer_and_ids`, `test_chat_observation_does_not_fetch_trace`, `test_flush_precedes_reset`, `test_last_case_flushes_on_failure`, `test_effective_settings_are_recorded`, `test_secrets_are_excluded`. Assert original response identity/content is unchanged.
- [ ] Run `python -m unittest discover -s l08 -p 'test_*.py' -v`; verify RED caused by absent capture implementation.
- [ ] Implement the interfaces using dependency injection for HTTP/clock in tests; fetch evidence outside the previous case's latency measurement. Never store API/auth headers.
- [ ] Re-run the tests; require GREEN. Check L03 dry-run and Docker mount against the shared stand. Do not alter grading logic to make cases pass.

### Task 2: Define budget views and calibration protocol

**Files:** modify `sets/l05_dialogs.jsonl`; create `l08/calibration-protocol.md`, `l08/prediction.md`, `l08/test_evidence.py`.

**Interfaces:** The original functional case records are archived byte-identically outside the runtime set. Each budget view has a unique ID, unchanged user turns, `additional_metadata.assertion: budget`, `oracle: human`, gate/runs and supported budget thresholds. Freeze final SHA256 after calibration. See the ledger compatibility ruling rather than extending or weakening official assertions.

- [ ] Write tests for unique IDs, six budget records, original functional records unchanged, nonempty user turns, CUS-0003 D14 case, a five-plus-turn D15 case and correct daily/release run counts.
- [ ] Add the five budget views and `COST-H06-EMPTY`. Use only `identical_tool_calls_max` for the new D14 daily case; select token thresholds for D15 views from own measurements.
- [ ] Write a predeclared calibration protocol: five clean and five lesson-08 runs for the selected token case, report median/range, loose and tight thresholds plus chosen median-based margin. Calibration data are exploratory, not final proof.
- [ ] Before the first paid call, save and separately commit an initial forecast/protocol with exact preliminary IDs and dataset hash. This is distinct from the final-set confirmatory forecast in Task 4.
- [ ] Verify RED→GREEN of dataset tests and the official `--dry-run --set l05_dialogs --gate all` selection. If functional metadata requires settings, document the actual supported invocation and validate it; do not silently patch runner semantics.

### Task 3: Measure official scenarios, traces, Langfuse and model migration

**Files:** maintain sanitized `l08/evidence/…`, official scenario copies with provenance under `l08/scenarios/`, `l08/b4.json`, and private ignored usage snapshots.

**Interfaces:** Preserve L08 scenario/check behavior. Archive every response and trace before reset, including failed retry attempts. Aggregation consumes raw records; no generated report may be the sole source of its own numbers.

- [ ] Confirm stand health, Langfuse readiness and available provider access without exposing key/account balance. Configure OpenRouter and trace-content capture locally; record model and effective settings. Track incremental spend against the approved cap.
- [ ] Verify current provider tariff source for both exact model IDs; save date and non-sensitive model-price evidence. Keep reasoning within billed output; do not double-count cache overlap.
- [ ] Run B1 and B2 clean/defect and B3 clean/lesson-05 sequentially, five runs per condition where medians are used. Retain full primary evidence and all attempts; distinguish D14 condition from lesson-08 D15.
- [ ] For B3, prove summary.input contains TX0401 and duplicate_charge while summary.text loses them; quote exact fields with request/span IDs and identify the FIRST loss span. Write the single regulator sentence.
- [ ] Configure local Langfuse exact-model prices; verify one measured generation and summarization span. Capture the seven-step C-07 session list with Total Cost. Show no-definition/input-output-only blind spots without presenting missing cost as zero actual cost.
- [ ] Execute B4 sequentially: two models, B1/B2, baseline/defect, five runs each combination. Preserve the kit's verdicts plus USD/dialogue and seconds/dialogue median/min/max. Raw token counts are reference only, not cross-tokenizer efficiency proof.
- [ ] Add tests `test_dialogue_total_uses_all_steps`, `test_full_answers_survive_preview`, `test_gemini_cache_overlap_not_double_counted`, `test_summary_cost_is_separate`, `test_completed_fail_is_not_error`; require GREEN before trusting aggregates.

### Task 4: Freeze final thresholds and run confirmatory clean-clone evaluation

**Files:** final `sets/l05_dialogs.jsonl`, `l08/calibration.json`, `l08/prediction-final.md`, required `reports/…`, sanitized capture records.

**Interfaces:** Calibration derives explicit model-specific thresholds; the final forecast names exact case IDs, failing assertion/condition, final set hash, model and settings. Confirmatory runs use this frozen set unchanged.

- [ ] Execute the predeclared calibration. Tabulate loose/too-tight/chosen thresholds with actual clean and lesson-08 results, medians and margin percentage; retain variability and counterexamples honestly.
- [ ] Freeze all six budgets. Create and separately commit `l08/prediction-final.md` BEFORE confirmatory runs; do not amend history after observing results. Include legitimate functional controls and residual risk in the L03-style rows (failure class, trigger, impact, control, remaining uncertainty).
- [ ] Create a clean local clone from the task repository with tracked project files only and no private environment files. Set only documented local service paths; preserve official runner behavior.
- [ ] Run `docker --context desktop-linux compose run --rm eval --set l05_dialogs --gate all --profile lesson-08` to completion. Retain report with every budget case separately visible and final verdicts; expected FAIL exit 1 is acceptable, infrastructure ERROR is not.
- [ ] Run the same command with `--profile clean`; preserve its report, all per-run observations and any baseline FAIL explanation. Reconcile forecast exact matches and additional failures, never substitute calibration runs for holdout runs.

### Task 5: Produce report, blank template, README and final audit

**Files:** create `l08/observability-cost-report.md`, `l08/observability-cost-report.template.md`, `l08/summary.json`, `l08/aggregate.py`; append README L08 section and maintain required evidence/reports.

**Interfaces:** `aggregate(evidence_dir: Path) -> dict` returns model/condition/scenario counts, median/range prices/time/tokens, budget calibration, forecast reconciliation and three-source cost comparisons. The report cites those values and primary request/span IDs.

- [ ] Header: actual system/version/model/tariff/date/backend/tools and runs per condition. Slide 1: Langfuse screenshot, blind spots, B3 incident table, at least two scenarios × two conditions with usage/trace/provider prices, separate token/time/cost ratios and n/m next to verdicts.
- [ ] Slide 2: measured step and dialogue costs; explicitly sourced planning assumptions for users/dialogues/mix; forecast for approximately 800 users; formula `C(N)=N*dialogues_per_user*sum(mix_i*median_cost_i)` and explain nonlinear history/loop growth with turns separately from linear fixed-mix user scaling.
- [ ] Slide 3: at least three savings levers each with a breakage/trade-off; rows for what was exchanged, what is not done and reversal conditions. B4 model migration decision: cheaper dialogue, tests remaining green, unmeasured answer quality; list model-dependent thresholds to recalibrate and concrete questions left for L09 judges.
- [ ] Add budgets table (six IDs, gate, runs, model and thresholds), the three-row loose/tight/chosen calibration table, report links and exact clean-clone commands to README.
- [ ] Create the same header/three-slide structure as a blank generic template, with no PayPilot IDs, model-specific numbers or filled findings.
- [ ] Recompute every report number from raw evidence, check case/set hashes, forecast chronology, billed attempts, provider delta reconciliation and quote fidelity. Publish only own experiment costs and reconciliation fact, not account financial snapshots.
- [ ] Run full unittest suite, schema/dry-run checks, secret scan, link validation and clean-clone checks. Review against every acceptance-map row; resolve findings rather than claiming completion with missing measurements.
- [ ] Restore stand clean and initial provider settings. Inspect status/diff, explicitly stage important task files and verify staged list. Preserve unrelated index changes. Commit/push/public repo/LMS are a later authorized handoff, not implied by staging.

## Plan Self-Review

- Spec coverage: all seven mentor criteria and every required artifact are mapped above; screenshot, blank template, ≥6 budgets, calibration and exact clean-clone commands are explicit.
- Interfaces: capture and aggregation remain adapters; official runner is the verdict source. Per-case settings and last-step token traps are explicitly checked.
- Forecast chronology: initial exploration protocol and final frozen-set forecast are separated; final confirmation cannot start before its own forecast commit.
- Review Focus: each of the five failure classes has a named test in Tasks 1 or 3.
- Scope: no stand feature work, no optional reasoning experiment, no changes to earlier accepted homework. Any missing required measurement remains a blocker, not a fabricated value.

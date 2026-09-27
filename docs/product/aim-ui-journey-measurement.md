# Measuring a real AIM UI journey

Use a disposable new repository, the trusted AIM package being evaluated, a small
useful product PRD, and one imported backlog candidate. Bind AIM UI to a dedicated
real Codex task. Record the CLI and model actually used. Do not inject checkpoints,
product code, or successful replies after Start. Do not interrupt an unrelated task.

## Measurement

Run the observer in a terminal which stays open, before clicking Start:

```sh
python3 scripts/measure_aim_journey.py observe --repo /absolute/test/repo \
  --file converter.py --output /absolute/evidence/journey.jsonl
```

Explicit file selection excludes AIM JSON, plans, copied packages and tests from
“first product code”. The observer reads files only; its output must be outside
the target repository. It records existing files as baseline, and subsequent
nonempty changes with SHA-256. A continuous observation gives an upper bound at
the polling interval (default 250 ms). Where available, filesystem birth time
provides an independent creation timestamp. Neither proves usable code: validate
the product separately. A stopped, late or missing observer must not imply a zero
latency. Missing transcript review must not imply zero questions or repairs.

Append timestamped JSON objects to the same JSONL evidence using the tool's
`append_event` function (UTC timestamps), with these kinds:

- `authorized`: exactly once, immediately before the initial Start click.
- `dispatch`: each actual `turn/start`, with turn ID and reason. Include explicit
  continuations as separate sends; distinguish them from duplicate actions.
- `interruption`: a deliberately injected outage, with the active operation and
  hashes of already written product files captured first.
- `operator_intervention`: any assistance needed to recover or finish, including
  a manual continue, edits, repaired checkpoints or special launch steps.
- `product_verified`: independent test command, exit status and evidence path.

Capture raw timestamped app-server events, outgoing request methods, the private
operation ledger, and the complete task transcript. These may contain local paths
and task content: keep them in the test evidence, not ordinary product UI.

## Interrupted journey

1. Observe a real new-backlog Start in the browser. Record authorization and all
   dispatches. Confirm the task is active and product work has begun.
2. Stop only the test UI process while the task is active. Record exact timing and
   preserved work hashes. Reopen the UI and reload the browser.
3. Observe the action and board independently. Verified activation proves that an
   increment was started; it does not prove product delivery or a still-running
   agent. Do not silently turn a stopped task into a success.
4. If work does not resume, record the required intervention and explicitly
   continue the same test task. Do not replay the original Start envelope.
5. Inspect the completed product, run independent acceptance checks, and review
   the complete transcript. Keep the interrupted attempt in the report.

## Classification and report

A question is unnecessary if AIM already had enough authority and information to
continue the approved work. User-owned final acceptance and material scope/risk
questions are necessary. Count each distinct request once, not repeated display
of the same request. An administrative repair is an attempted correction to AIM's
own catalog, state or planning format after a failure; initial normal setup is
measured in latency but is not a repair. Product bug fixes are separate.

Write a review JSON with `completeTranscriptReviewed`, `transcriptSha256`,
`unnecessaryQuestions` and `administrativeRepairs` arrays. Every finding needs an
`evidence` item/line reference and a `reason`. An empty array is valid only after
complete review. Include limitations in `limits`.

```sh
python3 scripts/measure_aim_journey.py report /absolute/evidence/journey.jsonl \
  --review /absolute/evidence/transcript-review.json
```

The clock starts at the original authorization and is never reset on resume.
Report setup, injected outages, recovery effort and validation separately.
Compare repeated equivalent runs before claiming a performance improvement.
One successful small CLI exercise cannot prove every repository works autonomously.

# Paired evaluation of the engineering changes

Status: both Enigma pairs, fresh-session preset maintenance and the held-out
API pair are complete. See the [first-pair results](paired-pilot-results.md),
[second-pair results](paired-pilot2-results.md),
[maintenance results](paired-maintenance-results.md) and
[API results](paired-api-results.md). This protocol evaluates
AIM as the product under test. It does not use AIM to manage the improvement
work in this repository.

## First pilot

Use the original Enigma PRD unchanged, SHA-256
`59ab6a803dd15e40a68f20f56b2ffcc081b3a0ac60aec873f5c93c2d733a9493`.
Two independent empty product directories receive identical copies. A frozen
copy of the current generated AIM package is supplied only to the AIM variant.
The assessor retains the original 123 simulator vectors and 14 search cases
outside both product directories. Their byte hashes are locked before work.

Both builders use `gpt-6-astra`, reasoning `high`, identical available tools and
a maximum 40-minute active-agent build budget. Start without inherited discussion
or knowledge of the earlier implementations. The raw builder works directly
from the PRD. The other uses the frozen AIM package in Auto mode. Both receive
the same product authorization, dependencies policy and delivery requirements.
No further delegation, publishing, external messaging or global configuration
changes are allowed. Separate directories are not an OS security sandbox.

Record actual model and reasoning configuration, start/completion/interruption
times, human interaction, tool environment and usage counters when available.
Do not infer token cost from a model name. A timeout or request for input is an
observed outcome; do not silently extend one variant's budget. Final user
acceptance is outside build time; any incomplete product work remains visible.

Run runtime performance tests sequentially after both builds stop. Product code
and fixtures are frozen before assessment. The assessor may adapt API bindings
to each implementation but may not change test inputs, expected results or the
score rubric. Verify candidate validity independently, distinguish first useful
result from completed search, and record result limits and timeouts. Use three
repetitions of each runtime workload and report raw data plus medians. Measure
peak process memory separately from Python/JavaScript allocation measurements.

Apply the original weights: simulator correctness 25%, cracking validity 30%,
other PRD fulfillment 15%, performance/stability 10%, usability 10%, and
maintainability/test effectiveness 10%. Do not double-penalize one root cause.
Any central failure is explicit even with a high total. Check desktop/mobile,
cancellation, repeated searches and candidate handoff after editing the form.
Inspect current docs and agent instructions for contradictions with the product.

## Decision boundary

The pilot can show a concrete win, loss, tie or insufficient evidence on this
task. It cannot establish general superiority. Do not change the decision rule
after seeing outcomes, select only favorable trials or award points for number
of documents, files, tests or role handoffs.

Before a broader claim, run at least three independent repetitions per variant
and extend to other requirements: permission boundaries, an existing-code
maintenance task and a held-out task not used to refine AIM. Blind the assessor
to the method when practical; when identity is visible, retain the same rubric.
Follow-up maintenance must be performed by a fresh session and use the same
change request, with orientation time, regressions and doc drift recorded.

The user clarified on 2026-09-29 that the AIM prohibition applies to building
the improvements, not testing them. Further AIM evaluation runs are authorized;
the improvement work and assessment continue without AIM as their working
method. Preserve bounded, comparable test budgets and record all outcomes.

## Clarified value criterion after the completed pilots

The user subsequently clarified that somewhat longer AIM delivery is acceptable
when demonstrated benefits outweigh the extra time: better-written code,
clearer responsibility boundaries, faster execution, lower resource use or
stronger security. Minimum build time is therefore not a separate pass/fail
condition. Preserve all locked scores, fixtures, failures and timings; label
any assessment using this clarification separately from the original rubric.

For subsequent comparisons, define relevant quality outcomes before dispatch.
Compare time overhead in absolute as well as relative terms with concrete
benefits. Inspect actual change boundaries and coupling; do not reward component,
document, role-transition or test counts. Keep observed runtime/security results
distinct from expected future maintenance benefits, and measure the latter with
a fresh-session follow-up when making a maintenance-speed claim. Report first
useful result, total work, resource use and regressions together. Critical
correctness or security failures remain explicit regardless of other gains.

Use an evidenced judgment of whether the additional effort was worthwhile when
no numerical business weights exist. Do not invent financial payback, select
weights after results to manufacture a winner, or require AIM to be faster in
every dimension. The goal is a product whose demonstrated benefits justify the
cost of producing and maintaining it.

## Second pilot

The second pair uses fresh GPT-6 Astra High sessions, the same locked PRD,
123 simulator vectors, 14 search cases, score rubric and three mutation types.
Both receive a 30-minute wall-time ceiling. The AIM package now has the shorter
23 kB entry, progressive command references, explicit authorized Auto startup,
variant-oracle coverage requirements and later UI file-boundary fixes. All 61
initial files were hashed and verified before dispatch. The first pilot's
package and outputs remain frozen. Do not interpret cross-pilot timing changes
as the isolated causal effect of an individual instruction.

## Precommitted follow-up tasks

Before the second pair submitted, two additional assessments were prepared:

- **Maintenance:** fresh sessions add interoperable JSON simulator presets to
  copies of the second pair's frozen products, with the same 15-minute budget.
  The schema, 3 valid and 23 invalid cases, independent cipher outputs and
  browser obligations are fixed first. Check atomic import, inert names,
  preservation of input, export after candidate handoff, prior simulator/search
  behavior, documentation accuracy and actual elapsed time. Preserve original
  products and measure first source edits only as a proxy, not as exact thinking
  or orientation time. Keep outcomes separate from the original product score.
- **Held-out backend:** fresh sessions build a tenant-separated notes HTTP API
  with the same 20-minute budget. This task was not used to refine the AIM
  instructions supplied to either builder. Fixed requirements cover role and
  tenant boundaries, input limits, SQLite persistence, versioned atomic writes,
  concurrent updates/deletes and errors without secret disclosure. A black-box
  HTTP assessor is prepared with positive and negative harness controls. On a
  fresh database, seed 10,000 records per tenant, then measure fixed serial
  listing, read and update workloads after both builders stop. Record failures
  independently of latency; do not collapse them into a favorable average.

These tasks broaden the evidence, but one run per variant is still not a
general superiority result. Preserve prompt/package/fixture hashes, actual
launch settings, all submissions and the full assessment output. Any later
instruction changes require a new package snapshot and explicit attribution.

## Reproducibility and evidence handling

The prepared local pilot contains two prompts, two untouched PRD files, the
frozen AIM package, assessor inputs and a manifest of all initial file hashes.
The run location is recorded in the task, not hard-coded into product tooling.
Check the manifest before starting; if canonical AIM instructions change, make
a new snapshot and preserve the old one rather than updating a trial in place.
Store outputs, logs and submission manifests alongside that pilot. Preserve the
original four Enigma projects and their locked comparison reports.

See [the engineering analysis](engineering-reset-analysis.md) for the prior
evidence, implemented changes and distinction between tool microbenchmarks and
agent/product outcomes.

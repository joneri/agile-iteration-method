# Adaptive execution and independent review

Use this contract when allocating product implementation or review. The main
AIM session owns integration, runtime state and decisions. This contract selects
useful work and reviewer separation; it adds no approval gate and never overrides
host limits, user instructions or existing authorization.

## Allocate activities, not ceremonies

At the first concrete change plan, choose the smallest useful allocation from
the dependency boundaries and risk. Record one short reason in the existing
plan; do not create an orchestration report for a one-file edit.

- Keep a small cohesive implementation with one author. Use another session for
  material review, not four sessions merely to enact four role names.
- Delegate independent source questions while the coordinator does useful work.
  Give each investigator a question and a bounded area; reuse the answer instead
  of repeating the investigation.
- Parallelize implementation only after shared interfaces are settled and write
  ownership is disjoint. Give each worker its inputs, allowed files, contract,
  verification and expected return. Tell workers that others share the codebase.
  Shared configuration, generated output and the integration boundary have one
  writer. Overlapping writers execute sequentially or in isolated checkouts with
  explicit integration. A reader validating moving files is not a stable review.
- Choose specialists for a consequential uncertainty: authorization, atomicity,
  numerical validity, request lifecycle, resource scaling, or another actual
  boundary. Load the available relevant skills; an expertise label is insufficient.
- Delegation is useful when it shortens the critical path or adds independent
  evidence worth its handoff cost. A serial dependency chain does not become
  faster by giving each link a different agent. Stay within available slots and
  the project budget; do not switch model or reasoning without authority.

Tell the user briefly which agents are working and why, then report useful
findings rather than repeated agent status. Keep wall time and summed agent work
separate. A coordinator may do a bounded implementation while other agents work,
provided ownership stays clear.

For a multi-writer plan whose conflicts are unclear, the read-only helper
`scripts/aim_engineering.py --repo <repo> delegation <plan.json>` checks a bounded
activity graph and proposes ownership-safe waves. Input version1 has
`delegationAllowed`, `maxWorkers`, a concrete `parallelBenefit` when >1, and
`activities`: each has `id`, `kind` (`read`, `write`, `review`), literal `paths`
and `dependsOn` IDs. Final review depends on relevant writers. It does not infer
host permission, launch workers, inspect semantic dependencies or prove speedup.
Use native tools for actual delegation; record their returned session IDs.

## Review is a separate judgment

For material changes to product behavior, security, concurrency, data integrity,
resource behavior or reusable architecture, delegate final review to an available
separate agent that did not implement the change. A role-name switch in the same
session is self-review. Fresh reviewer context contains the binding requirements,
current diff/source, relevant constraints and test entry points; do not substitute
the author's conclusions for that evidence or pass unrelated conversation history.
The reviewer may ask for a design rationale when needed.

A nonmaterial change with bounded, understood impact and a direct native check
may use a brief documented self-review exception: for example, wording or a
thin use of established built-in behavior with no new domain/state boundary.
Judge the effect, not the number of changed lines. Authorization, durable data,
async lifecycle, concurrency and other material boundaries above still require
separate review even for a tiny diff; uncertain impact is not a trivial exception.
Lack of permitted agent capability is an explicit
unavailable exception, not fabricated independence. State the limitation and use
proportional validation; request user input only if a binding requirement actually
requires independent review and cannot be met. Cost Control reduces the scope of
review and narration; it does not silently turn material review into self-review.

The reviewer uses `role-skill-reviewer.md` and affected project skills, inspects
code read-only, derives its own counterexamples, and returns reproducible material
findings with evidence. A clean review is allowed; finding counts are not a target.
The implementer fixes findings. Reuse the reviewer for affected rechecks rather
than rebuilding all context or rerunning unrelated checks. Review the integrated
result after parallel writes stop. Only then may the coordinator synthesize the
existing review/validation decision; user acceptance stays user-owned.

## Bind review to what was inspected

Record actual author/reviewer session IDs, changed-file fingerprints, unresolved
findings and limitations in existing review evidence. Include relevant tests and
configurations. Obtain the changed path set independently from the actual diff,
including added/deleted/untracked in-scope files; never let a review choose its own
coverage denominator. A new edit invalidates affected evidence, even when an old
report says passed. Recheck affected behavior and refresh only the review that
actually happened. Historical reports remain historical.

For material multi-agent changes, use
`scripts/aim_engineering.py --repo <repo> review <record.json> --changed <path>`
(repeat `--changed`) to check current evidence. Record version1 has `sources`
(`path`, `sha256`, or explicit `absent:true` for deletion), `implementers`
(`id`, `session`), `reviewer`, `reviewMode`, and `findings` (`id`, `severity`
material/advisory, `status` open/resolved, `description`). Unavailable reviewer
is null. An empty findings list is valid. A documented `exception` has `kind`
trivial/unavailable and `reason`; the coordinator passes `--allow-exception` only
when actual policy permits that exception. Stale evidence and material findings
cannot be waived. The helper validates declared provenance, not authenticated
agent identity, semantic correctness or host session isolation. The coordinator
must corroborate declarations with actual tool results. Absence inspection may
be unsupported on some hosts; report that limit without inventing a green result.

## Make the review change technical decisions

Choose checks from the change's failure modes, not a universal report template:

- For repeated flows, trace where the same responsibility is implemented twice.
  Assess one plausible next change: can it be made at one coherent seam? Extract
  shared lifecycle/business rules when divergence is a real risk; preserve clear
  separate flows when their contracts differ. Do not count files as modularity.
- For selection, jobs and UI/API state, follow input identity through results,
  failure, cancellation and reuse. Exercise a changed input followed by an old
  success and an old failure, including returning to a prior selection.
- For changed flows that write durable or remote state, distinguish rejection,
  confirmed commit and unknown outcome. A failed follow-up read does not undo a
  confirmed write. Apply authoritative results or block actions on known-stale
  state until recovery; do not blindly replay an uncertain write. Inject a
  relevant failure after commit and exercise the next user/consumer action,
  checking its actual side effect. An error notice or working Refresh control
  alone does not establish safe recovery. Use the existing lifecycle seam and
  test entry point rather than adding another report or review phase.
- For data/privilege changes, test the actual trust/transaction boundary and
  error precedence. A helper unit test is insufficient evidence for isolation.
- For growing workloads, inspect work per item and bounded outputs. Consider
  unnecessary full sorting, repeated scans, per-item I/O, large intermediate
  collections and uncancelled obsolete work only where present. Preserve a simple
  oracle and measure before adopting complexity. Use representative small and
  large workloads; benchmark without concurrent heavy agent/test activity.

Write the finding and its consequence, or state what was checked with no finding.
A separate agent and a successful helper check are mechanisms, not proof that the
result beats ordinary engineering. Product behavior and successor work decide.

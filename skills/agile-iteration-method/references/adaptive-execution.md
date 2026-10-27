<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/adaptive-execution.md
-->

# Adaptive execution and independent review

Use this contract when allocating product implementation or review. The main
AIM session owns runtime state and decisions; TDO owns the coherent increment,
integration and consolidated delivery evidence. This contract selects
useful work and reviewer separation; it adds no approval gate and never overrides
host limits, user instructions or existing authorization.

## Explain AIM through Graph engineering

Recommend a small outcome-and-dependency graph when introducing agent-led AIM.
The agent the user is speaking with can own the product outcome and coordinate
an AIM delivery agent. Give the delivery its requirements, actual authority,
delivery style, quality goals, resource boundary and expected evidence. Show
the useful responsibility and feedback relationships, not a mandatory agent
for each role:

```text
Human mandate → Owner agent → AIM delivery coordinator → Implementation
                    ↑                    ↓                    ↓
              Product decision ← Validated result ← Independent review
```

**Ship** is the new-work default: finish the agreed result before final owner
acceptance. **Loop** uses verified Done Increments and real owner feedback to
select what comes next. In **Strict Loop**, a human owner or explicitly delegated
agent owner assesses each agreed checkpoint. The delivery coordinator preserves
the native role/gate loop and alone mutates its ledger. The owner returns an
actual scoped decision; it does not edit the ledger. Reviewer judgment is
independent of implementation and does not itself supply owner acceptance.

Name concrete dependencies, input/output contracts and verification at handoff.
Use native agents only when available, permitted and useful. Sequential host
execution preserves dependencies; a same-session role switch never becomes
independent review or an independently delegated owner. An agent graph neither
authenticates identities nor grants resources or external effects. The human
must explicitly delegate product decisions; use the frozen `deliveryPolicy`
and actual decision evidence in [User Stories](user-stories.md).

## Allocate activities, not ceremonies

At the first concrete change plan, choose the smallest useful allocation from
the dependency boundaries and risk. Record one short reason in the existing
plan; do not create an orchestration report for a one-file edit. TDO chooses
sequential or parallel execution from dependencies, integration risk and existing
mandate. The commitment covers all selected Stories across sessions; parallelism
does not authorize extra agents, a new cost profile or more scope.

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
  the project budget; do not switch model or reasoning without authority. Count
  cumulative work across all agents, including preparation, experiments and
  rechecks. Splitting or delegating a larger undertaking cannot bypass limits.
  Concrete uncertainty can justify a bounded check; a complexity label alone
  cannot justify more agents, lower quality or changed product priority.

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

Verify parts and review consequential risks during implementation. Integrate as
soon as relevant parts can work together, then review and validate the complete
increment against its outcome and all selected criteria. There is no full role
and acceptance cycle per Story. A session boundary preserves decisions, completed
work and remaining commitments; it cannot turn partial delivery into completion.

## AIM Graph

Use `/aim graph` to answer what can start and what blocks the current delivery.
The trusted Story helper's `graph` command is read-only. AIM UI's **Graph** tab
shows the same outcome, selected Stories, dependencies, activity receipts and
proof freshness. Without an execution plan it shows the native checkpoints,
without inventing implementation tasks or agent presence.

When meaningful dependencies or parallel ownership justify it, TDO includes an
optional `executionPlan` in the existing `plan` request, before approval. It uses
the delegation plan above; each activity also has a `title`, selected `storyIds`,
`role` (`po`, `tdo`, `dev`, `reviewer`) and optional actual bound `skills` IDs.
The graph is part of the approved scope. Keep small cohesive work small; a graph
does not require an agent per node. The coordinator still checks semantic
dependencies, real skill availability, host authority and cumulative resources.

The main thread records work through `activity` in the same product ledger:

```json
{"deliveryId":"DI-EXAMPLE","activityId":"contract","status":"running","session":"actual-session-id"}
```

The confirmed receipt includes the graph and new `attempt`. Retain it rather
than rereading status. A completion supplies that same session and attempt,
`sourcePaths` inside the activity's approved paths and `evidence` references to
existing raw proof under `.aim/`. A failure supplies a concrete `reason`.
All mutations use the last confirmed ledger digest. The host runs agents;
record its returned session identity rather than a role label.

Starts require current completed prerequisites, available capacity and no
conflicting running ownership. A completion also checks that its prerequisite
receipts remain current. Changed source or proof marks affected work stale and
propagates to its dependants. Failed or stale work can receive a new attempt
under the same scope; prior attempts and proof remain historical. A stale
running attempt still occupies its slot until explicitly resolved; an unreadable
proof never becomes a successful completion. Restarting fences out the old
session/attempt. A bounded history prevents unlimited ledger growth.

The read-only projection recommends a compatible subset of possible work and
explains failures and blockers. Copying an assignment changes nothing. Task
receipts do not prove semantic correctness, authenticate agent identities,
measure speedup, advance gates or create user acceptance. Existing quality,
separate review and validation requirements still apply to the complete result.

## Review is a separate judgment

For material changes to product behavior, security, concurrency, data integrity,
resource behavior or reusable architecture, delegate final review to an available
separate agent that did not implement the change. A role-name switch in the same
session is self-review. Fresh reviewer context contains the binding requirements,
agreed increment outcome and preserved Story criteria, current diff/source,
relevant constraints and test entry points; do not substitute
the author's conclusions for that evidence or pass unrelated conversation history.
The reviewer independently checks whether the decomposition covers the agreed
contribution to Epic intent, as well as criterion coverage and actual product
quality. The entire Epic need not finish in the increment. The reviewer may ask
for a design rationale when needed.

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
The implementer corrects material in-scope defects; optional improvements and
personal preferences do not silently become requirements. Reuse the reviewer
for affected rechecks rather than rebuilding all context or rerunning unrelated
checks. Review the integrated
result after parallel writes stop. Only then may the coordinator synthesize the
existing review/validation decision; acceptance follows the actual human mandate
and designated owner contract.

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

## Repeated diagnostic failure in native Graph

A first bounded correction may retry normally. After two failed attempts on one
activity, Graph leaves the failures visible but omits that retry from automatic
recommendations. Independent ready work remains available. A session change
cannot reset the count; a completed correction ends the failure streak. This is
an observable repeated-failure trigger, not a universal time budget. The
coordinator must also reassess earlier material expansion inside a running task
or an exception workflow as required by `autonomous-interaction.md`.

The existing `activity` start request may include `reassessment` when retrying:

```json
{"contextSha256":"<activity retryContextSha256>","decision":"continue_bounded",
 "userOutcome":"How this technical goal protects the approved user result",
 "resources":"Cumulative work across attempts/agents; unknown stays unknown",
 "alternatives":"Bounded correction, independent work, or actual owner choice",
 "boundary":"One justified next attempt within existing authority; stop condition"}
```

The helper stores this on the new activity receipt, without another report file,
checks the exact attempt context and rejects replay after that context changes.
Only `continue_bounded` can start a retry; `owner_decision` or `independent_work`
means use the existing block/owner mechanism or perform that independent work.
The assessment is a coordinator declaration, not new scope, budget, quality waiver
or acceptance. Preserve failed attempts and the original frozen targets. Existing
historical receipts remain readable; this guard applies to new starts rather than
rewriting old approvals or requiring retrospective forms. A passing control-path
check does not prove reduced overall cost or universal prevention.

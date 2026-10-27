<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/user-stories.md
-->

# User Stories and the product backlog

PO frames the user's intent and owns Epic outcomes, scope, quality and product
priority. TDO creates/refines User Stories and owns the coherent delivery
commitment. Dev implements it, a separate Reviewer examines material work, TDO
validates and the owner accepts: the user, or an agent with explicit human
delegation for that decision. Use the shared rules already loaded from the
entry point and active role. Consult other references only for a concrete missing
rule or uncertainty; a role handoff does not reload the method.

## Intent, Epics and Stories

An intent states the problem or desired result. An Epic groups a larger outcome;
a Story expresses an actor's need and benefit within exactly one primary Epic.
A delivery selects ready Stories, possibly from several Epics, for one integrated
working improvement. A Sprint is an optional timebox, never a requirement or
Story. Epics group outcomes; Stories move on the board. Technical tasks belong
under the selected need or plan, not invented personas or implementation Epics.

Start from a natural-language intent or `/aim start "<desired outcome>"`. Preserve
actors, outcomes, constraints, non-goals and uncertainty. A ready Story has a
stable `US-*` ID, `epicId`, title, persona, need, benefit, observable acceptance
criteria with stable `AC-*` IDs, and PO priority (smaller positive numbers first).

After receiving a new intent, run the intent startup preparation in
[Command runtime](skill-command-runtime.md) before PO frames Epics or TDO plans
Stories. The intent itself is enough to begin preparation in an empty repository;
the user does not have to run separate calibration or agent-configuration commands.
Expose relevant dependencies, failure behavior and risks in the plan. Story size
serves coherent value and verification; there is no count target, independent
deployment requirement, mandatory Story Points, complexity score or time estimate.

Open intent/Epic requirements may evolve; accepted and closed records remain
immutable. Active selections freeze their requirement snapshots. Never rewrite
criteria to make delivered behavior pass, silently lower quality or let technical
sequencing reprioritize product outcomes. Link material decisions to existing
Story/criterion IDs and their actual evidence. Reuse applicable user authority
and discover repository facts before asking. A blocked choice stops dependent
work; continue independent authorized work. Consult
[Autonomous interaction](autonomous-interaction.md) only when the authority,
dependency or changed-decision boundary remains unclear.

## Ship and Loop delivery

Choose the delivery style before selecting Stories. **Ship is the default for
new work**: deliver the complete agreed product outcome, including its relevant
experience quality, before returning for final acceptance. Internal tests,
independent review and correction continue throughout. Agree the outcome and
resource boundary up front; Ship neither means unlimited work nor authorizes
deployment or publication. A budget limit reports unfinished work truthfully.

Choose **Loop** explicitly when owner feedback should shape what is built next.
Select a useful end-to-end Done Increment, present the verified result to its
owner, and use the actual assessment to refine the next selection. Complete the
current commitment before that checkpoint; feedback cannot silently rewrite an
approved selection. Ship and Loop have the same quality and evidence obligations.

Delivery style is independent of Strict/Auto and Standard/Cost Control/Deep.
**Strict Ship** asks for the plan decision and final product acceptance;
**Strict Loop** asks the designated owner at each agreed increment checkpoint.
Auto continues within existing authority; it never invents an owner's answer.
Resume existing deliveries under their frozen policy. An older record without
policy stays unchanged and gains no new default or agent authority.

New native `plan` requests may supply `deliveryPolicy`; omission stores
`{"mode":"ship","owner":{"kind":"human"}}`. Explicit Loop uses
`{"mode":"loop","owner":{"kind":"human"}}`. The policy is part of the
approved scope. State, compact receipts and the Story board expose that same
policy; changing it requires a supported new selection, not an edited digest.

### Graph engineering and delegated owners

Graph engineering is the recommended way to explain agent-led AIM delivery:
define who owns the outcome, who executes, what depends on what, and where proof
or feedback determines the next action. A graph does not require an agent per
role. Use the host's actual delegation capabilities; keep simple work simple.
The main agent can serve as product owner and delegate an AIM delivery
coordinator. That coordinator alone writes its AIM ledger; Dev implements,
Reviewer judges independently, and the owner assesses the integrated result.
Owner feedback and code review are distinct responsibilities.

An agent owner needs an actual human mandate naming its identity/session,
bounded outcome, resources and permitted decisions. Record it as attributed
human evidence under `.aim/`, then freeze the delegation in the new plan:

```json
{"deliveryPolicy":{"mode":"loop","owner":{"kind":"agent","id":"actual-owner-id","session":"actual-owner-session","mandate":{"path":".aim/human-mandate.md","sha256":"<actual sha256>"},"decisions":["approve","accept"]}}}
```

This is a plan field, not a standalone command or a role assignment inferred
from configuration. Use actual host-returned identities. The helper binds the
declared mandate and decision scope; it cannot authenticate a human instruction
or agent identity. The coordinator must corroborate both in the host conversation.
No role name, reviewer result, Auto setting, graph edge or copied prompt grants
product acceptance. Human reservations remain binding.

Delegated `approve` or `accept` supplies `authority.kind: "agent"`, the same
`id`/`session`, and the actual gate-decision artifact's `path`, `sha256` and
applicable `scopeSha256`. That artifact is bounded JSON (at most 16 KiB):

```json
{"ownerDecisionVersion":1,"deliveryId":"DI-EXAMPLE","operation":"accept","scopeSha256":"<current acceptanceSha256>","id":"actual-owner-id","session":"actual-owner-session","decision":"approved","reason":"Assessment of the named criteria and current evidence."}
```

For `approve`, bind the plan's `scopeSha256`; for `accept`, bind its current
`acceptanceSha256`. The helper verifies operation, delivery, identity, mandate
freshness and scope against the artifact itself. Mandate copies and retargeted
decisions reject. The owner must actually assess and issue the decision; the
implementer cannot write a fabricated owner answer. Agent delegation covers
only the listed delivery decisions, never separate Epic closure. Ordinary
human authority stays supported. See [adaptive execution](adaptive-execution.md).

## Coherent delivery and gates

TDO selects by PO priority, dependencies and capacity, naming the exact Stories,
useful integrated outcome, implementation boundaries, files, checks and risks.
The selection must deliver the agreed value, not merely an easy subset. Verified
learning substitutes for functioning product only in an explicitly exploratory
assignment. One active selection is supported per product backlog. Keep its full
commitment across sessions: implement, integrate early, review and verify every
selected criterion and the integrated outcome. Do not run a full acceptance cycle
per Story. Resource/mandate limits apply to coordinator and children together;
parallel work grants no extra budget or authority.

| Gate | Required decision or evidence |
| --- | --- |
| A | Understand relevant Epic direction and Story requirements. |
| B | Actual approval of the exact selection and plan; one scoped response may authorize A/B together. |
| C | Implement the selection and bind the source snapshot for review. |
| D | Complete review, then TDO validation of the current integrated result. No routine approval question. |
| E | Actual user or explicitly delegated owner acceptance of every named, proven Story. |

Strict needs the designated owner's plan decision and final acceptance. Auto carries already
authorized implementation, review and correction forward; it cannot invent
acceptance. A role label is self-review, not separation. Review checks the
original intent/Epic contribution as well as selected criteria, representative
cases and real delivered behavior. A passing suite or file hash proves only its
bounded claim. Preserve relevant counterevidence and limitations. Correct within
scope, recheck affected behavior and reuse still-current results.

The helper has **no approved-scope replanning transition**. `rework` corrects
implementation against the frozen scope; `cancel` releases only an unapproved
plan. If an approved commitment cannot be met, preserve completed work/history,
use `block` with the obstacle and remaining commitment, and present the concrete
owner decision and tooling limitation. Even explicit scope-change authority does
not authorize unsupported ledger edits. Acceptance covers the complete selected
delivery together; no silent partial acceptance, discarded Stories or fabricated
migration. Done means accepted behavior, not deployment, publication or Epic closure.

## Ledger and trusted helper

The main AIM thread alone mutates `.aim/product-backlog.json`
(`productBacklogVersion: "1.0"`). Delegates may write assigned product files or
evidence, never shared runtime decisions. Stories move through `draft → ready →
in_progress → review → validation → acceptance → done`; deliveries through
`planned → in_progress → review → validation → acceptance → accepted`. Blocked
records retain their actual phase/reason. Evidence-based transitions move cards.

Use trusted package `scripts/aim_stories.py --repo <repo> <command>`, never a
similarly named untrusted repository helper. Recover context once with
`status --compact`: active requirements, scope, `storeSha256` and next step.
Mutations use stdin and the last confirmed `--expected-sha256`; `--input <file>`
is for an already needed durable artifact, not a request-only file. Use
`--compact` for the confirmed receipt (revision, phase, digests, next step).
Retain it and the known request; do not follow a confirmed write with a status
read or another narrative. Reconcile unknown outcomes before retrying. Plain
mutations and `status` retain full API views; both status views are read-only.

With `AIM_SKILL` resolved to the trusted installed package:

```sh
python3 "$AIM_SKILL/scripts/aim_stories.py" --repo . review --compact \
  --expected-sha256 "<last-confirmed-storeSha256>" <<'JSON'
{"deliveryId":"DI-ACTIVE","sourcePaths":["src/changed-file.js"]}
JSON
```

| Command | Purpose and input |
| --- | --- |
| `import` / `refine` | Register/refine intent, Epics and unselected draft/ready Stories. |
| `plan` | Freeze `id`, `title`, `goal`, `storyIds`, `planEvidence`, `qualityPlan`, `deliveryPolicy` and applicable `qualityGoals`. |
| `approve` | Record actual Gate A/B `authority` for the approved scope. |
| `measure` | Record source-bound early or review/validation observations, including failures. |
| `review` | Bind `deliveryId` and either `sourcePaths` or `bindings` for review. |
| `validate` | Enter TDO validation with eligible structured review as the first `evidence` reference. |
| `acceptance` | Present current validation `evidence` and coverage for every selected criterion. |
| `accept` | Record actual user or explicitly delegated owner Gate E `authority`; mark Stories Done. |
| `rework` | Correct the same scope and invalidate obsolete product/review/validation bindings. |
| `block` / `unblock` / `cancel` | Record/resolve a blocker or release an unapproved plan. |
| `status` / `quality` | Inspect requirements/next step or measured quality without writing. |
| `closure-preview` / `close-epic` | Derive the separate Epic closure scope, then record authorized closure. |

Imports contain `intents` (`id`, `statement`), `epics` (`id`, `intentId`, `title`,
`outcome`, `acceptanceCriteria`) and `stories` (`id`, `epicId`, `title`, `persona`,
`need`, `benefit`, `acceptanceCriteria`, `priority`, `status`). Criteria have `id`
and `text`. Epic `outcomeClass` is `Product`, `Pilot` or `POC` (default `Product`);
`nonGoals` defaults to an empty list. Both are preserved and scope-bound.
`DI-*` identifies a delivery, never a Story. Required `planEvidence` references
an existing plan under `.aim/` naming boundaries, files, checks and integration
risks; its bytes are bound into approval.

Evidence references are `{path, sha256}` for existing contained non-symlink
files under `.aim/`. Product bindings allow repository-relative sources outside
`.aim/`; `sourcePaths` fingerprints 1–64 explicitly selected files. Derive the
complete changed set, including additions and relevant dependencies. Review,
validation and pending acceptance reject changed product bytes. Rework binds the
correction afresh; accepted bindings remain historical, allowing later authorized
changes. Scope freezes the originating intent, Epics, Stories and plan.

Ordinary approval/acceptance `authority` has `kind: "user"`, `path`, `sha256` and the
applicable `scopeSha256`. The helper checks scope/freshness, not human identity.
Have the actual instruction, preserve its scope and record it truthfully; never
invent approval evidence. Existing legacy Portfolio mandates do not authorize
new Story work.

## Frozen quality plan

Every new plan declares applicability in `qualityPlan`: `checks`,
`sharedRequirements`, `numericGoals` (`required` or `not_applicable`), `rationale`,
`primaryResult`, `caseCoverage` and `reviewPolicy`. Derive obligations from the
original intent, Epic outcome, selected criteria and relevant engineering rules;
feature-only Stories do not remove quality obligations.

A check contains `id` (`QC-*`), `criteria` (`US-ID/AC-ID`), `kind` (`behavior`,
`performance`, `journey`), `stage` (`core`, `delivery`, `both`), `workload`,
`environment`, `method`, concrete `expected` observations and linked `goalIds`.
Cover every selected criterion and goal, an early core and the documented real
entry/consumer journey. Shared requirements name `source`, `requirement` and
`checkIds`. Reuse checks when they actually establish several claims.

`primaryResult` identifies the complete useful operation:
`{"checkId":"QC-TIME","latencyGoalId":"KPI-LATENCY"}` or
`{"checkId":"QC-CORE","notApplicableReason":"<technical reason>"}`.
A latency goal needs a core performance check covering selected criteria, matching
workload/environment/method, seconds or milliseconds, an upper bound and median
or maximum samples. For substantial computation, search, batch or I/O work,
propose a justified target even without a PRD SLA. Cancellation/responsiveness
cannot establish complete-result latency. A routine static correction may
justify non-applicability without inventing a metric.

`caseCoverage` has `failureCases`, `nonDefaultModes`, `resultValidity` and
`workloadFamilies`; each uses `{"checkIds":["QC-..."]}` or
`{"notApplicableReason":"<technical reason>"}`. Identify actual inputs/modes and
independent expected results in the check, not another inventory. A category
name or “all results valid” assertion is not an oracle. Check materially
different workloads, completed work and invalid-result count where applicable.
Every performance check belongs to `workloadFamilies` and `resultValidity`,
with concrete expected product results on the same timed workload and matching
context for every linked goal. Other purely numeric checks may use `expected: {}`.
Review must judge representativeness; structural links alone cannot do that.

`reviewPolicy` is `{"mode":"independent"}` for material work. Only nonmaterial
work may freeze `{"mode":"self","reason":"<concrete scope justification>"}`.
This does not create independent review or waive freshness, coverage or findings.
Unavailability is not a material-review waiver. The policy is part of Gate B
scope; it cannot be relaxed during validation.

Applicable `qualityGoals` (at most 32) contain `id` (`KPI-*`), `outcome`,
`workload`, `environment`, `method`, `unit`, `source`, `owner`, `action`,
`threshold`, `operator` (`<=` or `>=`), `aggregation` (`median`, `min`, `max`) and
`minSamples` (3–1000). Distinguish actual user requirements from proposed
engineering targets and justify the workload/baseline in the existing plan.
Freeze targets; never shrink work or silently lower them after a miss.

For machine-readable JSON results, TDO freezes `checks[].observation` alongside
`expected`. It maps exactly those expected keys to `{"pointer":"/result/total"}`
or `{"pointer":"/result/items","transform":"length"}` (array length).
Pointers use bounded RFC 6901 syntax; this is data extraction, not executable
expressions. The existing report item then contains `checkId` and `raw` (an
existing `{path,sha256}` JSON artifact under `.aim/`) instead of `observed`.
The helper derives the values itself. Missing fields, wrong types, altered raw
bytes and an `observed` override reject the operation. Retain the usual report
context; one raw file may serve several checks without copied values or reads.
Direct raw references remain integrity-checked in failed, reworked and accepted
history without reassessing historical product sources. Only active raw payloads
are retained, under a total cache bound of four times the existing per-file
evidence limit; history keeps hashes/stamps. Historical plans and checks without
machine-readable results stay compatible.
A raw fingerprint proves bytes, not the producing build or semantic coverage;
Reviewer still checks actual instance, input, source and workload provenance.
Numeric samples retain their existing contract and need the same provenance
review; this extraction does not authenticate their producer.

## Measurements that change the next action

Use `measure` as soon as the core works, **before expanding implementation**.
In `in_progress`, supply `deliveryId`, `sourcePaths` (or `bindings`) and
`qualityMeasurements`. Act on the confirmed receipt's assessment and instruction
path without another `status`/`quality` call. Preserve failed/missing/stale results;
analyze and correct, or block for an actual owner choice. Inspect algorithmic cost
and profile the hot path when expensive; moving it to a worker does not make it
cheap. Missing or failed core observations block `review`.

One existing consolidated report can hold numeric samples, check observations
and explicit criterion coverage. The compact form avoids copying frozen labels:

```json
{"qualityMeasurementVersion":"1.0","qualityCheckVersion":"1.0",
 "context":{"scopeSha256":"<approved scope digest>",
            "productBindingsSha256":"<digest of sources/configuration used by this run>"},
 "measurements":[{"goalId":"KPI-LATENCY","unit":"s","samples":[0.4,0.45,0.5]}],
 "checks":[{"checkId":"QC-ENTRY","observed":{"exitCode":0,"output":"actual output"}}],
 "criterionCoverage":{"US-RECOVER":{"AC-1":"Observed result and relevant limitation."}}}
```

IDs resolve workload/environment/method from that exact frozen scope and declare
execution under those conditions. Keep units, actual values, raw native outputs
or their existing references, and actual source binding. The digest is canonical
`digest(productBindings)`, including ordered paths/hashes. Expanded reports remain
supported: omit `context`, repeat `workload`, `environment`, `method` and
`productBindingsSha256` in each record (plus `unit` for numeric records). No
historical rewrite is needed. Another scope, mixed overrides, missing/mismatched
observations, unsafe paths, changed sources, insufficient/nonfinite samples or
failed results cannot establish readiness. Method text is data, never a command.
The helper returns missing/mismatched observation keys and states `passed`,
`failed`, `unmeasured`, `stale` or `mismatch`; it cannot authenticate execution or
semantic correctness. A generic caller `passed` flag is insufficient.

An early replacement needs `response` describing the correction/owner decision;
`coreVerificationHistory` retains prior records. In review/validation a recorded
failure routes to `rework_or_decide`; preserve the phase until supported rework
or a blocked owner decision. First missing observations can be measured on that
snapshot; replacing an existing report requires rework. New observations use
new files; bound historical raw evidence stays immutable and hash-checked.

Final readiness requires every check and goal. Reuse current core evidence when
its source/configuration bindings are contained in the final snapshot; still
check the integrated real entry. Delivery-only checks cannot reuse core evidence;
`both` checks can do so only with the complete bound source set unchanged.
Reverify affected integrations/dependencies, not every previously proven fact.
Preserve historical failed-result references without comparing obsolete product
bytes with later code. No prevention report, KPI database or routine full benchmark.

## Consume the existing review at validation

Give the separate reviewer the original requirements, complete changed source
set and existing raw results. It checks applicability, representative variants,
source/dependency coverage, the real entry and an independently chosen relevant
counterexample. For UI changes examine actual rendered behavior, visible errors
and relevant result states. Keep observations/findings in the original review;
the coordinator adds only new validation facts or material limitations.

For new plans, the first `validate.evidence` reference is that existing review
record in bounded version-1 form. When preparing it, use the read-only
`review-record --expected-sha256 <confirmed review receipt>` operation in the
existing report-writing invocation. Supply only the reviewer's actual input:

```json
{"deliveryId":"DI-EXAMPLE",
 "implementer":{"id":"author-id","session":"author-session"},
 "reviewer":{"id":"reviewer-id","session":"reviewer-session"},
 "reviewMode":"independent","findings":[]}
```

The helper copies `scopeSha256` and `sources` from the confirmed review snapshot
and emits the consumable `version: 1` report. Multiple authors use `implementers`
instead of `implementer`. Explicit `findings` is required; optional `notes` and
`observations` hold new reviewer evidence. It never updates old hashes to new
bytes, advances a phase or invents a review. Capture a successful return before
writing the existing evidence file; do not truncate prior evidence on an error.
No request-only input file or intermediate formatted-report receipt is needed.

Findings have `id`, `severity` (`material`/`advisory`), `status` (`open`/`resolved`)
and `description`; retain resolved findings, relevant counterexamples and raw
observations in the same record. Do not generate an extra receipt/report or run
a separate eligibility-check round. Native validation uses the existing review checker in
the same verified invocation: exact scope, current sources, coverage of all
bound product paths, reviewer ID **and** session distinct from every implementer,
and no open material finding. Other evidence references may support the review.
Self mode requires the frozen nonmaterial policy; it remains explicitly self-review.
Declared identities are not authenticated separation, and complete declared
coverage cannot prove that the supplied changed set or oracle is sufficient.

## Reuse evidence through acceptance and closure

`acceptance` requires `deliveryId`, validation `evidence` and either explicit
`criteria` entries (`storyId`, `criterionId`, `evidence`) or `criteriaFrom`, a
normal reference to existing JSON containing `criterionCoverage` as above.
Every selected Story/criterion must have a nonempty textual assessment; missing
or extra keys, duplicate JSON keys, blank/nontext values or changed hashes fail.
Both forms enforce explicit quality context against the approved delivery and
reviewed sources. Opaque historical evidence remains supported. Semantic coverage
is still TDO/Reviewer judgment: qualified or failed results stay qualified/failed.
A quality pass does not create missing coverage. A final quality report may
supply both `evidence` and `criteriaFrom`; do not write another validation narrative.

Owner acceptance is a separate scoped decision after readiness. PO then evaluates
remaining Epic outcomes/counterevidence, every Epic criterion and all in-scope
Stories. Story acceptance proves only those Stories. `closure-preview` and
`close-epic` accept `criteria` or `criteriaFrom` using
`epicCoverage[epicId][criterionId]` textual assessments. Require accepted Stories,
whole-Epic evidence and its own actual scoped authority. A delivery context cannot
prove broader Epic coverage; Product/Pilot closure needs representative journeys
through the normal product entry. Synthetic proof alone may close only an explicit
POC. A cross-Epic delivery may leave both open.

Keep requirements/state in the ledger and link existing evidence. Reuse confirmed
receipts through handoff, recovery and closure; no mirrored hashes, full logs,
second development narrative or routine status reread. Each helper invocation
reads/hashes a shared path once, rejects conflicting expected hashes and rechecks
file identities/change stamps before commit/return. The cache never survives the
invocation and is not an atomic snapshot against arbitrary later writers. Use
CAS/current bindings at consequential transitions. Honor cumulative resource
limits; report gaps instead of starting an unapproved test campaign. For an admin
budget use existing traces, include coordinator/children, distinguish method work
from product work and elapsed/overlapping/unknown time. Fewer calls alone do not
prove less time, cost or preserved quality. Remove repeated work before redesigning
storage; file count is not a productivity KPI. Keep runtimes, caches and virtual
environments outside `.aim/`.

## Compatibility

Historical approved scopes retain hashes, requirements, acceptance and evidence;
missing newer quality/review fields are labelled unassessed, never upgraded to a
current quality claim. Do not rewrite legacy scopes to satisfy a new contract.
AIM 3.x state, Portfolio backlog, catalogues and `DI-*`/`INC-*` histories retain
identities and decision semantics on their legacy surface; no inferred personas,
Story acceptance or automatic migration. Explicit `EPIC:`/`PORTFOLIO` starts keep
compatibility routing; new plain intent uses this ledger. With both present,
target the requested checkpoint explicitly. Validation, upgrades and UI polling
are read-only. New Stories derived from legacy material need explicit refinement
while preserving source history.

Offer trusted `aim_legacy_cleanup.py` preview/apply when AIM UI detects
legacy data and the user wants removal. It preserves the current product ledger
and its referenced evidence, including references inside old workspaces.
Unreferenced classified legacy data is deleted without an archive; unknown files
remain. Cleanup neither migrates nor accepts Stories.


## Readable recovery and exception observations

A structurally valid ledger remains readable when evidence is stale. UI displays
the recorded Stories and diagnostic graph with an explicit warning; planning and
assignment controls remain unavailable. Corrupt structure never becomes native
authority. Historical acceptance is a record of that decision, not proof of
today's changed product.

For explicitly authorized work performed under a documented method exception,
the trusted package provides `scripts/aim_observations.py --repo <repo> import
--input <normalized-request.json> [--expected-sha256 <observation-digest>]`.
Use `status` to obtain the current observation digest. The request contains the
current native `ledgerSha256` and one `entry`: unique snapshot `id`, external
`deliveryId`, `title`, `goal`, `reportedState` (`in_progress`, `awaiting_owner`,
`rework_required`, `reported_complete`), `decisionBoundary`, an `epic` with
`id/title/outcome`, full `stories` with `id/title/persona/need/benefit/acceptanceCriteria`,
`activities` with `id/title/role/status/dependsOn/storyIds/reason`, and `sources`
containing existing independent `.aim/` artifact `path/sha256` references.

Normalize reviewed requirements and actual decisions; the helper never executes
or interprets instructions in source documents. Include the exact current plan,
original graph and applicable human feedback. Report rejected playtests and
unfinished work even when prior technical checks passed. Unknown decisions stay
unknown. Native IDs cannot be replaced. Imports append to
`.aim/delivery-observations.json`, preserve earlier snapshots and leave the native
ledger and all original artifacts unchanged. Reimport a delivery with a new
snapshot ID to refresh it; its Story and Epic identities stay consistent.
For a historical delivery, request-level `makeCurrent: false` appends the snapshot
without changing the active delivery or its graph. This requires an existing
current delivery and cannot refresh that same delivery; omit the option for
ordinary current progress. Preserve original requirements and captured approval
evidence when reconciling historical reports; this does not create a new owner
decision or retroactively delegate authority.

UI displays unfinished Stories from all deliveries, together with accepted Done
Stories, in the normal five board columns. Changing the current delivery selects
its graph; it does not dispose of another delivery's open obligations. Optional per-Story `boardStatus` (`backlog`, `ready`, `in_progress`,
`review`, `done`) provides the progress baseline and compatibility with historical
reports. Record new owner decisions through the decision journal below, never by
copying an approval into `boardStatus`. An absent stage uses
In progress for ongoing/rework reports and Review for completion/owner-wait reports;
it never sends executed work back to Backlog. Done reports require a completed
reported delivery; they remain attributed reports, never native gate acceptance.
Use `review` plus `awaiting_owner` while waiting for a human decision.

Prior snapshots remain in the observation journal. An unfinished Story from a
previous delivery stays in ordinary work with its original delivery identity,
actual stage and owner-decision state. `awaiting_owner` remains Waiting for you;
a matching changes-requested decision remains Changes requested until corrected
work is resubmitted. Neither switching focus nor technical completion creates Done.

The optional `replacesDeliveryIds` list relates existing native deliveries to an
observed replacement report **for display only**. Use it only with explicit
reconciliation intent and source evidence. It does not dispose of the original
obligations, change native statuses, or grant acceptance; unfinished native work
remains visible. This display relation is not a supported scope replacement or a
correction-to-original Story link. All stored snapshots and decisions stay intact.
Native delivery metrics exclude observation reports.
Changed source hashes or a changed native ledger mark observations stale and
require an explicit refresh. Observation snapshots alone confer no approval, acceptance,
implementation assignment or supported native transition. They do not make
future deliveries eligible: use the native workflow for new work, or disclose
the concrete unsupported transition and obtain an actual scoped exception.


## Original obligations and corrective deliveries

Prefer native `rework` under the same frozen Story identities for corrections to
an active native commitment. When an authorized corrective delivery needs distinct
Stories, optional Story `corrects` records provenance without adding `dependsOn`:

```json
{"corrects":[{"deliveryId":"ORIGINAL-DELIVERY","storyId":"US-ORIGINAL","criterionIds":["AC-1"],"scopeSha256":"<original requirement scope>"}]}
```

Native and exception-observation Stories use the same link contract. Obtain the
exact target binding through the trusted helper before importing/refining the
correction; the original must already exist in a recorded delivery:

```sh
python3 scripts/aim_story_links.py link-context --repo . --delivery-id ORIGINAL-DELIVERY --story-id US-ORIGINAL --criterion-id AC-1
python3 scripts/aim_story_links.py owner-context --repo . --delivery-id ORIGINAL-DELIVERY
```

Links bind original requirements and selected criteria, not transient progress.
Unknown targets, changed requirements, duplicate/self links and cyclic provenance
reject. New links enter the correction's frozen scope; old records without links
keep their existing hashes. Accepted historical links remain historical when a
later requirement changes; they do not block unrelated deliveries.

The Board exposes original and corrective Stories together, their actual stages,
linked criteria and proof. A ready/accepted correction leaves a rejected original
in Changes requested with an explicit original-resubmission instruction. It does
not turn original work into Done or create a prerequisite cycle. Partial correction
coverage never proves the remaining original criteria. Revalidate the **whole
original requirement scope**, including its unchanged criteria and siblings.

For native work use the original delivery's supported rework/review/validation/
acceptance sequence. Stale native evidence still blocks acceptance. For an
exception observation, explicitly refresh the original delivery with its same
Story identities, full original criteria and current original/correction proof,
using `awaiting_owner` for the technically verified scope. Retain the old rejected
snapshot and decisions. Only then can its owner assess the original obligation.
Linked correction readiness and current proof must also verify. Native
acceptance freezes incoming correction context into its acceptance digest; new
or changed correction proof requires original rework/revalidation and a fresh
owner scope. Exception corrections whose every Story explicitly binds a native
original use those full frozen native requirement scopes independently of native
progress or unrelated ledger changes. Their source bytes still verify; the UI
explains native progress. Unlinked observations retain full-ledger staleness. `decision-context`
returns `corrections` and `correctionContextSha256` when relevant; include that
fingerprint in the **original** decision request. A changed correction requires
fresh context. The original scoped decision changes only its named Stories; it
never accepts the correction or siblings implicitly. Historical decisions retain
their captured context and prior acceptance.

An unfinished original leaves ordinary work only through an existing supported
actual acceptance. `replacesDeliveryIds`, correction links, changed focus and
technical completion cannot dispose of it. Approved-scope cancellation/replacement
is still unsupported; preserve/block the original commitment and disclose that
limitation instead of inventing a ledger transition. A `corrects` link is neither
scope replacement authority nor execution/acceptance authority.

At final Ship readiness, present **one** scoped original-delivery owner question,
using the host's structured question tool when available: approve the named
scope, request changes, or review/play first. `owner-context` provides the original
Stories, earlier scoped decisions, linked corrections, current evidence and
limits, independently of current board focus. Its `ready` flag requires the
original's actual ready phase, current evidence and ready linked corrections;
read-only context alone is not proof of technical readiness. Preserve already
accepted scope and clarify exactly which remaining Stories the decision covers.
Do not ask at each implementation step or Story. Await a real answer, recheck
context and record it through native `accept`/`rework` or the observation decision
journal, then retain the confirmed receipt. Silence, a preselection, technical
checks and an unrelated new request never supply acceptance. `review_first`
keeps acceptance pending and offers the actual review/play path.

## Story dependencies in the live board

When TDO identifies a prerequisite, record it structurally rather than burying it
only in acceptance-criterion prose. Optional Story `dependsOn` lists actual
prerequisite Story IDs. Optional
`prerequisites` lists external inputs with `id`, `text`, boolean `resolved`, and
optional boolean `blocking` (default true). Both fields are preserved in frozen
scope snapshots when present; legacy scopes retain their existing hashes.
Unknown or cyclic Story links are rejected. Ready requires completed prerequisite
Stories and resolved blocking external inputs. An explicitly nonblocking later
asset choice can remain open while work starts. Resolving inputs leaves a draft
Story in Backlog until TDO makes the readiness decision.

Graph renders only declared Story dependencies. Shared agents, review stages and
activity pipelines are not Story dependencies. Graph shows all Epics in the
selected current/history scope, independent of the Board's Epic filter. External
inputs and acceptance criteria remain inspectable on each selected Story. Where
no structured Story dependencies exist, say so rather than inventing lines.

The UI polls persisted state; no animation grants authority or changes status.
Keep the board current as work changes: native delivery transitions update their
Stories automatically. For authorized exception work the coordinator must append
an accurate observation snapshot when progress or requirements change. Record
owner decisions exclusively through the decision operation below; no subsequent
status import is needed. Changed sources are visibly stale until refreshed. Do not refresh hashes alone,
assume owner acceptance, or discard rejected attempts to make the board look clean.


## Automatic owner decisions in exception observations

Native `aim_stories.py accept` already records acceptance and updates its Stories
atomically. Do not stop at a prose decision file: finish the native operation and
retain its receipt. For authorized exception deliveries, record the decision once
in the observation runtime. The live board derives status from that same record;
no second status import or `boardStatus` edit is needed.

Register requirements before execution with optional `deliveryPolicy` using the
same human/explicit-agent owner contract as native deliveries. Omission freezes
human ownership; it cannot later become agent ownership through a refreshed
snapshot. Agent policy requires the actual contained mandate. The host still
corroborates the human instruction and actual agent identity. Existing historical
reports and original native records stay unchanged.

Get exact current context for the named Stories:

```sh
python3 scripts/aim_observations.py decision-context --repo . --input selection.json
```

`selection.json` contains `deliveryId` and a nonempty distinct `storyIds` list.
The response contains the current observation `storeSha256` and selected
requirements `scopeSha256`. Then register the actual assessment:

```sh
python3 scripts/aim_observations.py decision --repo . --input owner-decision-request.json --expected-sha256 <storeSha256>
```

The request has `id` (stable unique decision ID), `deliveryId`, `storyIds`,
`scopeSha256`, `decision` (`approved` or `changes_requested`), `reason`, current
assessment `evidence` (`path/sha256` references), and `authority`. Human authority
has `kind: user`, the captured actual decision's `path/sha256`, and the same
`scopeSha256`. Agent authority adds actual `id/session`; its separate decision
artifact must be exact bounded JSON with `ownerDecisionVersion: 1`,
`deliveryId`, `operation: accept`, `scopeSha256`, `id`, `session`, matching
`decision`, and `reason`. The accept mandate covers the owner assessment's
approve/request-changes disposition; it does not grant author/reviewer authority.
Native delegated decision evidence retains its existing approved-only contract.

The helper verifies selection, owner identity/mandate, scope and proof before one
atomic journal append. It leaves requirement snapshots, current delivery selection
and native ledger unchanged. At the next ordinary UI poll, approved named Stories
become Done; requested changes move only the affected Stories to In progress.
Unselected Stories retain their own state. Neither role names, technical completion
nor Auto mode is an owner decision. Partial scope changes require explicit owner
assessment and a new exact requirement scope; old decisions cannot approve new
criteria. A decision covering multiple Stories binds the selection together.

Use prerequisite `kind: owner_assessment` for the pending owner test. Its displayed
resolution follows the recorded decision; ordinary external inputs use `kind:
input` (default) and are not automatically resolved. Do not manually clear an
owner-test flag after recording acceptance. A progress-only snapshot refresh
cannot undo a matching decision. Changed selected requirements require a new
assessment even if a producer copies an old Done value. A decision on a historical
delivery never changes which delivery is current.

Keep the request and confirmed receipt. After an uncertain response, retry the
same decision ID and exact payload with the original context: an existing commit
is acknowledged without duplicating or reapplying it. Same ID with different
payload, stale CAS, changed scope, missing delegation or changed proof reject
without a partial write. Decisions append to the existing local store, bounded
to 256 records and its size limit. Old snapshots remain intact. Edited/missing
decision evidence leaves the recorded stage readable with an explicit verification
warning, not new native authority or assignments. Browser polling stays read only.

Publish current implementation/review progress before requesting the owner test.
Record the resulting owner assessment through the decision command before any
separate narrative/graph update; the journal itself is the owner-stage source of
truth. Do not maintain a second H/Done state that first invalidates the registered
snapshot. Stale registered sources or a changed native-ledger binding reject new
decisions; publish the actual changed work with its evidence before assessing it.
This is ordinary progress publication, not a second card-status operation after
acceptance. Existing exception registrations without an agent policy remain
human-owned; historical delegated receipts stay visible, but they do not silently
retrofit a new delegated runtime policy. Register new delegated work with its
actual mandate from its first snapshot.

Final `owner_assessment` is a completion decision, not a blocker for Ready.
Ordinary unresolved required inputs and prerequisite Stories still block starting.
Native accepted receipts resolve the displayed owner-assessment input while
preserving frozen prerequisite bytes. After requested changes, publication of
corrected work in Review/awaiting_owner restores waiting for a new assessment;
the earlier changes-requested decision stays in history. Approval requires a new
actual decision. A routine progress refresh cannot undo an approved decision.

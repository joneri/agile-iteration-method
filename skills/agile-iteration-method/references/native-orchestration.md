<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/native-orchestration.md
-->

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Native Graph engineering and orchestration

AIM 4.8 Native connects original product outcomes, work dependencies, ownership
and proof to durable continuation decisions. Default new delivery plans to Native;
small work uses a small graph without extra agents.
A user can supply a goal without designing a graph. TDO selects the smallest
useful pattern, checks the real ownership boundaries and freezes it with the
usual delivery plan. A node describes work; it does not require another agent.

## Select a graph

| Pattern | Use when | Shape |
| --- | --- | --- |
| `cohesive_delivery` | One author can deliver the coupled result | Implementation followed by integrated independent review |
| `maintenance_repair` | A failure needs reproduction before a fix | Diagnose, repair, integrated review |
| `independent_branches` | Outcomes have genuinely disjoint writes | Independent branches followed by integrated review |
| `bounded_investigation` | A consequential uncertainty needs a discriminating experiment | Investigation, bounded change, integrated review |

Keep one cohesive author and reuse a separate reviewer for the first material
core challenge and final review. Intermediate feedback may happen within an
activity; it need not create a node or approval for every coding step. Measure
the smallest working route before expanding it.

Use the trusted package's `scripts/aim_orchestrate.py default --input graph-input.json`
to construct a graph. Its input is:

```json
{
  "pattern": "cohesive_delivery",
  "outcomes": [{
    "id": "INT-CHECKOUT",
    "requirement": "A buyer recovers a delayed payment confirmation.",
    "paths": ["src/checkout", "tests/checkout"]
  }],
  "coordinator": {
    "session": "actual-delivery-session",
    "capability": {"id": "aim-native-orchestration", "version": "4.8.0"},
    "permittedDecisions": ["continue_bounded", "independent_work", "request_owner_choice"]
  },
  "policy": {
    "delegationAllowed": true,
    "maxWorkers": 1,
    "checkpointAttemptBudget": 4
  }
}
```

The attempt budget is an example, not a universal four-attempt rule. Choose it
from the task's uncertainty and actual resource mandate. Parallel capacity above
one also requires a concrete `parallelBenefit`. It never grants extra host slots
or permission to delegate. All paths are contained literal ownership scopes.

For a supplied graph, use `validate --input graph.json`. Preserve its node IDs,
dependencies, outcome coverage, input/output contracts, proof expectations and
`origin: {"kind":"custom","reference":"<user graph version>"}`. Validation
returns a copy, without silently repairing the user's graph. Explain invalid
cycles, unsafe ownership or missing outcomes and propose the smallest correction
before freezing it. Feedback and bounded retry history are separate from DAG
prerequisites; a feedback loop is not a cyclic `dependsOn` edge.

Use `plan` with `{"graph": <validated graph>, "storyOutcomes": {"US-RECOVER":
["INT-CHECKOUT"]}}` to generate `executionPlan`. Include it in the normal Story
`plan` request with its quality plan. Outcome IDs refer to the selected Stories'
original Intent IDs. Check semantic coverage: a structurally valid graph cannot
prove that the chosen Stories fulfil the user's whole goal.

Plan approval freezes the graph, original requirements and quality obligations.
Preserve historical scope. An unsupported scope change needs a supported new
plan and its applicable decision; it cannot edit accepted history or reset a
campaign by renaming work.

## Activate the actual coordinators

Use the product ledger's `orchestrate` operation before starting a Native
activity. Bind the delivery coordinator's actual session, capability/version and
current scope. Include upstream sessions that dispatch this delivery, with
activation evidence showing the instructions they actually received. The parent
can coordinate without maintaining its own product ledger or repository profile.
The delivery coordinator alone records product decisions and observations in the
canonical ledger; child/parent messages are inputs to that operation.

The convenience entry accepts `activate`, `observe`, `decide` and read-only
`status`. For example:

```bash
python3 <trusted-package>/scripts/aim_orchestrate.py status --repo <product>
python3 <trusted-package>/scripts/aim_orchestrate.py activate --repo <product> --expected-sha256 <confirmed-store-digest> --input activation.json
```

`activation.json` contains `deliveryId`, `coordinatorSession`, `dispatchers` and
`evidence`. Each dispatcher contains its actual `session`, the same
`capability: {"id": "...", "version": "..."}` as the frozen graph, and evidence
references. References use `{"path":".aim/activation.json","sha256":"<actual file digest>"}`
with existing contained files. Include the coordinator among the dispatchers.
On a session change, repeat `activate` with `previousCoordinatorSession` naming
the current coordinator, new `coordinatorSession`, actual dispatchers and fresh
evidence. Previous activations stay in history; the original graph is unchanged.

Retain the confirmed receipt, revision and digests. Use the normal Story helper's
stdin and compare-and-swap contract. Activation is scoped to the selected
delivery; stale scope or session bindings cannot authorize a new attempt. A
resume rebinds the real session while retaining original campaign history.

Capability and authority fields are declarations linked to evidence, not
identity authentication or a competence certificate. A role name, installed
skill, graph node or Auto mode does not grant resources, external effects or
acceptance. Owner decisions still use the frozen `deliveryPolicy` and actual
human delegation. The graph's permitted decisions only narrow that mandate.

## Preserve the original campaign

Campaigns live in the same product ledger, keyed by original outcome rather
than activity, technique, graph revision or agent session. They retain:

- original waiting goals and their priority;
- attempts and evidence-linked observations across deliveries and restarts;
- comparable integrated progress and the last usable baseline;
- concrete failures and bounded new diagnostic information;
- observed resource totals and explicitly missing measurements.

Record baseline and integrated observations through `orchestrate` with
`action: "observe"`. Use the same comparison key, metric and direction for the
same user journey. Evidence must identify the actual source and result. A new
baseline identifier does not make recovery below a previous best result into
new progress. A local component pass, successful build, hash, reviewer count or
heartbeat does not prove integrated product improvement. A failed input or
crashed main route remains a blocker even if a local test passes.

A usable baseline retains the exact declared source files, not only their hashes.
Small checkpoints store up to 256 KiB of source bytes in the ledger. For larger
scopes, the `observe` request may supply `sourceCommit` with an exact existing
Git commit SHA; each selected committed blob must match the declared source.
The helper never makes a commit automatically. Keep that commit available.
Export the retained baseline with:

```bash
python3 <trusted-package>/scripts/aim_orchestrate.py checkpoint --repo <product> --outcome INT-CHECKOUT > retained-checkpoint.json
```

This read-only export returns retained source bytes or verifies the selected
Git blobs. It covers the explicitly named source files, not the application's
whole environment, installed dependencies or unrecorded files. Review the paths
and restore through the project's authorized workflow. Later numeric progress
does not imply a newer recoverable snapshot.

Positive baseline, integrated-progress and falsifier evidence includes a raw
JSON report binding the exact measurement to its source:

```json
{
  "orchestrationObservationVersion": 1,
  "deliveryId": "DI-CHECKOUT",
  "scopeSha256": "<approved scope digest>",
  "sourceBindingsSha256": "<digest of exact source reference array>",
  "observation": {"outcomeId": "INT-CHECKOUT", "kind": "baseline", "session": "actual-delivery-session", "attempt": 0, "baselineId": "working-route", "comparisonKey": "checkout-recovery", "metric": "completed-scenarios", "direction": "higher", "value": 0, "usable": true}
}
```

The observation in that report must equal the request's observation. Compute
the source digest from the exact ordered `[{"path":"...","sha256":"..."}]`
array for `sourcePaths`, using UTF-8 JSON with sorted object keys,
`ensure_ascii=False` and compact separators `(',', ':')`, then SHA-256. Values
come from the actual verification entry, not from an intended success flag.
Attach the report's hash-bound reference in `evidence`. Before work, a baseline
uses the coordinator session and attempt zero. After work begins, a baseline
uses the latest actual worker, activity and campaign attempt, completed source
bindings and raw proof. This lets the first working core establish a usable
checkpoint in an initially empty project. Later baselines retain high-water
results and counters; creating a checkpoint does not reset stagnation.
Other positive results also need a completed actual activity/worker attempt
and matching source snapshot;
old raw proof cannot be relabelled as a fresh result. The normal quality and
independent review contracts still determine semantic validity.

Record resource deltas once, in actual units; unknown tokens, cost or elapsed
agent work remain unknown. Account-wide usage percentages are not a campaign's
cost. Wall time and summed overlapping agent work are different quantities. A
new campaign delivery cannot grant a larger budget or erase earlier effort.

Use product severity and the owner's actual priority. Fix a broken required
journey before tolerable cosmetic polish. A reviewer may challenge a mistaken
severity classification; neither party may lower mandatory criteria to pass.
Keep the last usable source checkpoint recoverable and preserve negative proof.

## Make continuation consequential

Before actual dispatch, consult the current campaign assessment. At the bounded
no-progress boundary, choose a different concrete diagnostic action, preserve a
usable baseline, work an authorized independent waiting goal, follow the owner's
priority, or request the actual decision needed to proceed. Record the choice
through `orchestrate` with `action: "decide"`, the returned context digest,
concrete action key, reason and evidence. Reusing stale context or the same
exhausted action cannot silently buy another round.

An exhausted checkpoint or changed owner priority requires a current scoped
user decision, not a recycled plan approval. `status` returns an
`ownerDecisionContext` template. Fill its `decision` and `actionKey` from the
actual owner response, add `priority` when applicable, and retain that exact
JSON record as authority evidence. Include `targetOutcomeId` when the decision
request names one. It binds operation, delivery scope, outcome,
current campaign/shared-priority context and coordinating session. The `decide` request supplies
that authority reference with `kind: "user"` and the same scope. Structural
validation does not authenticate the human response; the host must preserve its
provenance. Never generate an owner's answer from the template yourself.

A new falsifying result may justify a bounded follow-up on difficult work. It
must change the next test and be consumed by that follow-up, rather than excuse
unlimited repetitions. A heartbeat or active agent never renews the budget. Read-only review does not
consume the product-work attempt budget and remains available at its boundary.
Requesting a decision is appropriate for an actual authority/resource/quality
conflict; it must not prevent independent authorized delivery. Retain the
original unfinished commitment while waiting.

At handoff, pass only the needed requirements, scope, input/output contracts,
proof expectations and confirmed receipt. Bind actual returned host session IDs
and the attempt. Reconcile uncertain launches/results before repeating them.
Report open original goals, last proven usable result, largest blocker, next
concrete action, observed/unknown resources and any coordinator-induced wait.
No separate progress database is required.

## Enforcement and host limits

The Story helper checks activated Native activity starts and persists their
attempts in the campaign. Its ordinary dependency, capacity, ownership,
source/evidence freshness and session/attempt fences remain applicable. The
supported Codex bridge's explicit Native activity path checks the same ledger
before dispatch. The host launches agents; the helper does not create them.

The loopback UI service exposes `POST /api/actions/dispatch` for an explicit
Native envelope:

```json
{
  "actionVersion": "native-1",
  "action": "native_activity",
  "authorityStatePath": ".aim/product-backlog.json",
  "expectedStoreSha256": "<confirmed store digest>",
  "deliveryId": "DI-CHECKOUT",
  "activityId": "implement",
  "scopeSha256": "<approved scope digest>",
  "coordinatorSession": "<actual bound thread>",
  "session": "<same actual bound thread>",
  "actionKey": "restore-delayed-confirmation"
}
```

Wrap it as `{"envelope": <envelope>}`. This explicit bridge path continues an
activated activity in its configured bound Codex thread. It does not create
child threads or turn legacy activation envelopes into Native dispatch. The
bridge rechecks current scope and ledger at the asynchronous pre-turn boundary,
records the actual activity attempt, then verifies a matching evidenced result.
A finished model turn alone remains incomplete. Unknown transport outcomes must
be reconciled before replay; do not relaunch from a copied stale assignment.

Codex chat, Claude Code and GitHub Copilot use the same packaged continuation
contract before their native host tools. Portable instructions cannot intercept
arbitrary direct tool calls. Report an omitted binding/check as unverified
orchestration; do not claim complete enforcement on an unintegrated host path.
Sequential execution preserves dependencies when parallel host tools are absent.
A same-session role switch does not become independent review.

`/aim graph` remains a read-only projection of the selected delivery's activities
or lifecycle fallback. AIM UI Graph shows Story dependencies, not a new live
agent scheduler. Copying an assignment does not launch work. Neither graph view
proves product correctness, speedup, token savings or owner acceptance.

## Compatibility

New Native plans explicitly opt into `executionPlan.orchestration`. Existing
plans without that field, imported observations and legacy Epic/Increment
workspaces keep their original contracts. Upgrade does not rewrite approved
scope, accepted evidence or runtime files. Resume those plans honestly under
their existing checks; adopt Native in a newly approved plan when appropriate.

No graph framework, Superpowers installation or external service is required.
The paired level-building experiment informed the owner's choice of Native;
it did not establish general superiority, universal agent adherence or lower
subscription usage. Validation proves bounded executable contracts and retained
regressions, not future product quality by itself.

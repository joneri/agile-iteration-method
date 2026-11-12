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

## Coordination ownership and handoff

The agent receiving a new AIM assignment remains its coordinator by default.
Delegate bounded work to Dev, Reviewer and specialists without another approval
per subtask. Native graphs, real subagents, "the orchestrator", model/reasoning
preferences, host slots and delegation flags do not authorize another coordinator.
When requested settings are unavailable in the receiving session, disclose that
specific limitation and resolve the setup/topology choice with the user before
using a separate coordinator.

A separate coordinator requires an explicit user mandate or authorized handoff.
Bind actual receiving/coordinating sessions, scope and the original instruction
in the existing plan and activation evidence. After transfer the former layer
only relays actual user corrections, factual status and genuine escalations by
default. It cannot independently direct pace, work ordering, implementation,
review scope, retries, interruptions or replacement workers. Silence, a long
turn or missing file writes does not justify steering, narrowing quality or
taking control. Diagnose an observed host/transport failure separately; factual
failure reporting grants no product direction or retry authority. Any technical
repair stays within actual host authority and preserves unknown outcomes.

Explicitly retained owner decisions remain scoped to their human mandate,
including resources and the frozen `deliveryPolicy`. A parent-created task or
role label cannot supply that mandate. Returning coordination requires an
authorized reassignment. Legitimate session recovery continues the same role
with one actual coordinator and retained history; it does not transfer delivery
to a subordinate or require a new human approval on every resume.

## Activate the actual coordinator

Use the product ledger's `orchestrate` operation before starting a Native
activity. Bind the delivery coordinator's actual session, capability/version and
current scope. Include upstream sessions that dispatch this delivery, with
activation evidence showing the instructions they actually received. An upstream
session's activation declares loaded context, not authority to steer after handoff.
The former layer keeps no second product ledger or repository profile.
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

For new assignments, supply `ownership` in `activate` using the existing ledger:

```json
{"receivingSession":"actual-receiving-session","kind":"receiving"}
```

`receiving` requires the coordinator to be the receiver. An explicit separate
coordinator uses `kind: "handoff"` and `mandate: {"path":".aim/handoff.json",
"sha256":"<actual digest>"}`. The mandate is a bounded JSON artifact (16 KiB):

```json
{
  "orchestrationHandoffVersion": 1,
  "deliveryId": "DI-CHECKOUT",
  "scopeSha256": "<approved delivery scope>",
  "receivingSession": "actual-receiving-session",
  "fromSession": "actual-receiving-session",
  "toSession": "actual-separate-coordinator",
  "residualRole": "relay",
  "previousActivationSha256": null,
  "originalMessage": "<actual human instruction authorizing this transfer>"
}
```

Optional `retainedDecisions` lists only explicitly retained scoped owner roles;
it grants no ledger control or new acceptance/resource authority. On later
handoffs `fromSession` is the current coordinator and `previousActivationSha256`
is the canonical JSON digest of that exact current activation (null only for the
initial handoff). It prevents replaying an older transfer after a round trip;
returning control also requires the actual reassignment mandate. Legitimate
recovery uses `kind: "recovery"`,
the unchanged original `receivingSession`, `previousCoordinatorSession` and fresh
activation evidence describing the actual continuation. Do not declare a transfer
to a subordinate as recovery. Recovery after a handoff retains that handoff in
activation history and consumes no new mandate. Only one current coordinator
may steer through supported activity/observe/decide paths once ownership is bound;
activated upstream relays cannot perform those operations.

Ownership cannot be dropped or its receiver renamed on subsequent activations.
Existing frozen plans and activations without this binding remain compatible;
do not retrofit historical authority or require fresh approval for old recovery.
The CLI checks declared bindings, scoped evidence and hashes, not human intent
or authenticated host identities. The Codex bridge separately verifies its actual
bound executing thread; it does not reliably know the original receiving session.
Where a host reliably supplies that receiver, compare it before dispatch and
reject an unmandated receiver/coordinator mismatch. Never treat a caller's IDs
as that host proof or claim these checks police arbitrary host messages.

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
uses its matching actual worker, activity and campaign attempt, completed source
bindings and raw proof. This lets the first working core establish a usable
checkpoint in an initially empty project. Later baselines retain high-water
results and counters; creating a checkpoint does not reset stagnation.
Other positive results also need a completed actual activity/worker attempt
and matching source snapshot;
old raw proof cannot be relabelled as a fresh result. For an activity serving
several outcomes, supply every receipt source owned by this outcome, with the
same hashes, and omit the other outcomes' sources. Reference order may differ;
the raw report still binds the exact supplied reference array. Positive proof
checks this outcome's sources, the completed receipt's evidence and its current
prerequisite receipts. It does not assert freshness of unrelated outcome files.

Concurrent activities can finish in either order. An observation keeps its
original campaign attempt, worker and activity; a newer start of a different
activity does not invalidate it. A newer attempt of the same activity, changed
sources, stale prerequisites or mismatching scope still prevent reuse. The
ledger retains arrival order. Assessments use launch-attempt order without
rewriting that journal, so delayed success cannot erase newer failure or work,
and a delayed falsifier cannot renew information gain already consumed by a
newer start. Current proof and checkpoint views select the newest logical
attempt rather than the last-arriving report. The normal quality and independent
review contracts still determine semantic validity.

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
owner decision, not a recycled plan approval. `status` returns an
`ownerDecisionContext` template. Fill its `decision` and `actionKey` from the
actual owner response, add `priority` when applicable, and retain that exact
JSON record as authority evidence. Include `targetOutcomeId` when the decision
request names one. It binds operation, delivery scope, outcome,
current campaign/shared-priority context and coordinating session. The `decide` request supplies
that authority reference with `kind: "user"` and the same scope for a human answer. Structural
validation does not authenticate the human response; the host must preserve its
provenance. Never generate an owner's answer from the template yourself.

### Route internal escalations to the actual owner

Freeze the actual delegated owner in `deliveryPolicy`, with the human mandate,
identity and session described in [User Stories](user-stories.md). An agent with
only `approve` or `accept` permission cannot renew resources. Bounded resource
delegation additionally names `orchestrate` in `owner.decisions` and a positive
`owner.maxAdditionalAttempts`. The human mandate must actually authorize that
allowance; the fields do not create authority. Its allowance is cumulative across
all campaigns and deliveries sharing that mandate in the ledger. Human resource
limits outside this ledger remain binding too.

At an exhausted checkpoint, Native `status` exposes `pendingDecisions`: a stable
request ID, current decision context, intended recipient, coordinator response
destination, remaining delegated attempts and `requiresHumanDecision`. A delegated
owner remains the recipient when it must bring a concrete outside-mandate choice
to the human. A human-owned plan retains a human recipient. Missing or stale
delegation must never be inferred from an upstream role label.

The delivery coordinator sends that bounded context to the named owner through
an available, actually authorized host message tool. Do this before opening a
human-facing process question. Retain the returned host message receipt; the
projection's `delivered: false` does not mean that a message has been sent. The
upstream owner watches the actual child task through the host's wait/status
capabilities, retrieves a pending decision when needed, and returns the scoped
answer to `responseDestination`. Before a handoff or ending a coordination turn,
check assigned children for unresolved escalations. Do not report that work is
advancing while an unhandled owner decision blocks it. Reconcile an uncertain
send before retrying; reuse the unchanged request ID instead of opening another
question. No new polling service or decision database is needed.

If the requested choice exceeds the delegation, the owner brings the human the
additional work, cost/unknown cost and consequence in ordinary language. Retain
the block until the actual necessary answer exists. If the host cannot deliver
or expose internal messages, report that concrete capability gap; do not claim
automatic notification or silently substitute a human process question.

For an authorized delegated renewal, fill the returned context from the actual
owner's response with `id`, `session` and positive `additionalAttempts`. Keep the
exact JSON as answer evidence and supply `authority.kind: "agent"`, the same
identity/session, current scope and its evidence reference to `decide`. Include
`additionalAttempts` in that request. The helper checks the frozen permission,
fresh mandate, upstream activation, current campaign context and remaining
allowance. Only `continue_bounded` or `change_baseline` is delegated by this
permission. Priority changes still require actual human authority.

The grant permits exactly its stated number of further work starts. Progress,
component passes, session changes and new deliveries cannot replenish that grant
or erase prior attempts/resources. Replayed or wrong-owner answers reject. A
human renewal can also specify `additionalAttempts`; existing human renewals
without that field retain their frozen checkpoint behavior. Resource delegation
does not grant product acceptance or Epic closure. Existing frozen plans are
not rewritten: establish new delegation in an appropriately approved new plan.

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

Before a normal host Dev dispatch, use the Story helper's read-only
`dispatch-check` with the exact proposed `activity` running request and current
`--expected-sha256`. It simulates the same start checks: actual delivery and
approval, scope, Native activation/coordinator, dependencies, capacity, ownership,
fresh evidence and cumulative campaign/resource policy. A ready Story or plan
file is insufficient. On success it returns `eligible: true`, `committed: false`,
the scope and prospective attempt. It neither reserves nor launches a worker.
Record the exact actual `activity` start under that unchanged CAS before host
dispatch; the mutation repeats the checks under the ledger lock. A stale check
cannot authorize a launch. Preserve the confirmed activity receipt in the Dev
handoff. On an unknown launch/result, reconcile before retrying.

Already executed unactivated Native work requires the explicit present-authorized
[reconciliation operation](user-stories.md#present-authorized-reconciliation-of-undelivered-native-work),
not fabricated past gates or a fresh normal plan implying earlier activation.

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

## Continue the same delivery after rework

A requested correction keeps the approved delivery and its original commitment.
Supported `rework` retains earlier activity receipts and campaign history, but
marks a new work round. The old completions remain historical; they cannot satisfy
the new implementation or its dependent review. Start a fresh bounded activity
before editing its source, then record current proof, independent review,
validation and the actual owner decision through the normal gates.

Rework never changes the frozen scope, owner mandate, attempt counters or resource
allowance. An exhausted campaign still needs its real scoped owner decision before
another work start. A late old worker result cannot finish the new round. Resolve
actual running workers before rework; a stale graph label does not mean a worker
has stopped. The one-active-delivery rule remains in force.

Reading or upgrading an older marker-free ledger does not rewrite or invalidate
it automatically. If an older supported rework is already stuck in `in_progress`
(including `blocked` from that phase), an explicit `rework` with a recovery reason
may reopen that same correction only when there is prior rework history, no new
round marker and no latest running activity. It appends truthful recovery history
and preserves the earlier rejection and block reason. It does not invent another
human rejection, accept a result or grant resources. Ordinary initial work and a
repeated recovery of an already marked round do not qualify for this exception.

The runtime binds new receipts to `activityReworkRevision` / `reworkRevision`.
These are lifecycle fences, not new plan identities or a second history store.
Manual candidates and human feedback stay attached to their actual source/build:
do not manufacture past Native starts or copy acceptance onto a newer build.

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

## Retire an obsolete approved commitment

An actual human owner can cancel or replace an unaccepted approved delivery
through the [Story disposition contract](user-stories.md#cancel-or-replace-approved-work).
Keep its frozen graph, activity attempts, negative proof and campaign/resource
history. Reconcile every raw running worker first. Retire the old outcome's
current dispatch priority explicitly; record before/after priority without
deleting its original campaign or granting more attempts. A replacement is a
new unapproved plan. Cancellation is terminal history, never Gate E acceptance.

## Historical input bindings and identical baseline copies

Bind early read/challenge inputs to preserved baselines before the approved
writer changes the live files. An early input assessment and the final review
of the delivered product have different freshness obligations. Planned writes
must not force an already-running implementation attempt to restart merely
because its early input receipt still points to a live path.

For an existing completed **read** activity, use trusted `aim_stories.py
relocate-bindings --expected-sha256 <current-store-digest> --compact` with:

```json
{
  "deliveryId": "DI-ACTIVE",
  "activityId": "early-layout-challenge",
  "attempt": 1,
  "receiptSha256": "<SHA-256 of the exact original completed receipt>",
  "coordinatorSession": "<actual activated coordinator session>",
  "mappings": [{
    "from": {"path": "src/Game.swift", "sha256": "<original reviewed SHA-256>"},
    "to": {"path": ".aim/baselines/before-edit/Game.swift", "sha256": "<same original SHA-256>"}
  }],
  "reason": "Preserve the reviewed original input after the approved live edit.",
  "evidence": [{"path": ".aim/analysis/early-layout-review.md", "sha256": "<existing proof SHA-256>"}]
}
```

The receipt fingerprint uses the helper's canonical JSON digest (sorted keys,
UTF-8, no insignificant spaces), as used by dependency `receiptSha256`.
Use the actual last confirmed store digest and an existing reviewed receipt;
never reconstruct a past activity or change its original fields. Reuse relevant
existing `.aim/` evidence; no extra agent, report or owner gate is required.

The coordinator may relocate only the latest completed read in the current
rework generation, during approved implementation or its preserved block.
Native requires the currently activated coordinator. The helper verifies each
contained, regular, non-symlink destination against the exact original source
hash, and verifies unchanged original read proof. The old live path may already
have changed or disappeared. A destination may be outside the original read
node's paths: this grants only evidence reading, never new write ownership.

The operation appends `bindingRelocations` with original receipt/scope/generation,
exact mappings, coordinator, reason, evidence and time. It changes no original
receipt, dependency digest, approval, phase/block, activity attempt, campaign or
resource record. Graph and Native dependency/priority checks resolve the saved
locations while retaining the original receipt identity and visible source refs.
An already-running downstream attempt can then complete as that same attempt.
The operation works at an exhausted work checkpoint, but cannot authorize a
new work attempt or renew resources. Preserve actual administrative cost in the
existing resource accounting when known; never invent zero tokens/time.

Multiple mappings commit atomically. Changed bytes, unsafe paths, wrong actor,
superseded attempts, stale CAS or changed proof reject without a partial update.
An identical retry with the current CAS returns its existing record without
changing revision/time. A later move can relocate an already saved location to
another identical copy; obsolete prior locations remain history. Current saved
bytes are still checked, and become stale if modified. Old journal entries
survive normal rework/new attempts but never apply to a different receipt or
generation.

This is not a new review assessment or a way to make historical output current.
Write outputs, final-review activities, `productBindings`, measurements and
product-progress observations cannot be relocated by this operation. Changed
current product/proof still requires the normal fresh review and quality path.
Accepted and cancelled deliveries cannot receive new relocations. If content
or meaning changed, use actual new work/review; do not manufacture equal hashes
or reset the campaign.

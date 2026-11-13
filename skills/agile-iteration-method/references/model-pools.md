<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/model-pools.md
-->

# Approved model pools for child agents

The receiving agent remains coordinator. When the owner explicitly delegates
model choice, freeze an optional `executionPlan.modelPool` in the normal Native
delivery plan. Its Gate B approval covers subsequent child choices within that
pool and resource allowance; no extra approval is required per child. A role,
profile, model name or available host slot supplies no authority by itself.

Model and reasoning effort are an approved **pair**, not two interchangeable
lists. Discover the actual host/account capabilities first. Do not infer model
quality, availability, prices or accepted effort levels from a model name.
Historical plans without a pool keep their original inherited behavior.

## Plan and configuration

For example, after the owner approves these exact settings and boundaries:

```json
{
  "modelPool": {
    "version": 1,
    "choices": [
      {"id":"focused","model":"gpt-6-luna","reasoningEffort":"xhigh"},
      {"id":"integration","model":"gpt-6.1-sol","reasoningEffort":"medium"},
      {"id":"demanding","model":"gpt-6-astra","reasoningEffort":"medium"}
    ],
    "budget": {"maxStarts": 6}
  }
}
```

These are illustrative choices, not mandatory models or a cost ranking. The
coordinator chooses from the approved pairs according to the actual task, risk,
known remaining resources and uncertainty. Explain the choice concretely. More
reasoning on one model is not a common capability scale across models. Preserve
independent review; no model choice grants acceptance or new scope.

For representative assignments, record judgments such as these, grounded in the
approved pool and current host evidence rather than a permanent model ranking:

| Assignment | Selection reasoning to record |
| --- | --- |
| Inspect two named parsing call sites | Choose the approved focused pair when the bounded read and clear expected output fit its observed capability; spend one start and return unresolved ambiguity. |
| Implement a state transition across ledger and adapter | Choose the approved integration pair when cross-file dependencies need broader reasoning; preserve a start for separate review and account for any required cost estimate. |
| Independently challenge replay/authorization boundaries | Choose the approved demanding pair when the consequential risk and independent counterexample justify it within remaining resources; otherwise escalate the resource constraint. |

These are examples of task/risk/budget rationale, not measured comparisons of
the example models. If the approved pair is unsuitable or unavailable, stop or
choose another explicitly approved suitable pair under the remaining mandate.

`aim.roles.yaml` may contain `orchestration.modelPolicy: approved-pool` with a
`modelPool` candidate in the same format. Configuration is reusable planning
input, never approval. Copy the intended candidate into the new plan and obtain
its normal scoped decision. Later profile edits cannot alter a frozen pool.
The default remains `inherit-supplier-default`; do not silently migrate projects.

## Choose and launch a child

Supply `modelSelection` on the existing `activity` start request:

```json
{"choiceId":"focused","task":"Inspect the two named parsing call sites","risk":"Read-only, bounded input mapping; report uncertainty before proposing changes","budgetReason":"One of the remaining approved child starts; monetary usage is unknown"}
```

Normal `dispatch-check` and the exact CAS `activity` start enforce the same
approved pair, rationale, dependencies, capacity and cumulative allowances. The
prospective/stored receipt contains the derived `requested` pair and
`spawnRequest`. For the native Codex collaboration adapter, pass that request's
actual `model`, `reasoning_effort` and `fork_turns: none` to `spawn_agent`, with
the bounded assignment and real host task identity. Omitting those fields can
inherit defaults and does not implement the selected choice. Full context forks
cannot be combined with per-child overrides on this adapter; pass the needed
assignment explicitly. Respect custom-agent pins and verify reported settings.

Preflight is not a launch or reservation. Record the exact actual work start
under the same CAS before dispatch, bind the returned host identity and reconcile
unknown launch outcomes before retrying. Where a host returns an identity only
after session initialization, initialize without product work, account its
setup/unknown usage, then bind and check the actual work start before assigning
product work. A work-start allowance does not police arbitrary host calls or
initialization billing. Never report a fabricated identity or gate.

Coordinator/self work keeps its existing model and cannot claim a child choice.
The pool cannot grant forbidden delegation. Unsupported settings must reject,
or lead to a new checked choice of an explicitly approved alternative within the
remaining allowance; never silently substitute or create another coordinator.
The current bound-thread Codex UI bridge cannot launch children or apply their
settings and explicitly rejects pooled work before queuing. Use the supported
native collaboration path; do not switch the parent's model as a workaround.

## Resource accounting

`maxStarts` counts all retained selected-child work attempts, including running,
failed, retried, reworked and reviewer attempts. Rework, replacement sessions and
lower observed costs do not refund starts or reservations. A new delivery needs
its own actual approval and cannot silently renew a project-wide resource cap.
Root, setup and other actual usage still belong to the existing cumulative user
resource mandate; the pool is not an unlimited allowance for untracked work.

An optional `budget.costLimit: {"unit":"credits","amount":10}` is an explicit
estimate/reservation allowance, not a provider billing guarantee or a price feed.
It requires `modelSelection.estimatedCost` in that same unit on each child start.
Use owner/host-supported estimates and disclose their provenance; no catalog is
invented. Without a priced allowance, actual cost remains unknown where telemetry
is missing, rather than free. Arithmetic preserves finite JSON numeric values
exactly without rounding away a boundary reservation.

New starts account for at least each original estimate and the maximum known
reported cost for that attempt. A known overrun blocks later starts while older
valid starts remain historical. Parallel work can reveal an overrun after other
valid starts; retain and report it without rewriting their dependency hashes.
Different cost units are not silently converted. Follow the actual resource
owner/escalation path when the remaining mandate cannot support the work.

## Observe the actual result honestly

Attach a hash-bound `modelObservation` JSON reference to a running observation
update or terminal activity request. The artifact contains:

```json
{"modelObservationVersion":1,"deliveryId":"DI-EXAMPLE","scopeSha256":"<approved scope>","activityId":"implement","session":"<actual child>","attempt":1,"source":"host","dispatchAccepted":true,"model":"gpt-6-luna","reasoningEffort":"xhigh","actualCost":null}
```

Sources are `host`, `worker` or `unknown`. Missing settings/cost use `null`;
dispatch acceptance is separately true, false or unknown. A successful host
request, worker self-report or copied requested pair is not host-confirmed
configuration. Evidence binds every reported field to the exact scope, child
and attempt; source labels remain declarations, not authenticated host identity.
Projection retains requested and observed settings separately.

For an existing running child, use `status: running`, its exact `session` and
`attempt`, the current `coordinatorSession` and the observation reference. This
updates evidence without starting work again, consuming another model start or
incrementing the Native campaign. Earlier running observations remain in bounded
history. Unknown/lower reports cannot erase known spend or a reported mismatch.
A known mismatch or rejected dispatch cannot become successful completion;
preserve it on the failed attempt before another checked choice.

Completed receipts remain immutable. This route does not ingest later invoices
by rewriting completed receipts. Report late unknown/actual usage through the
existing resource/owner mechanisms rather than claiming continuous billing
enforcement. Native test probes may verify explicit launch requests and returned
responses even when the host exposes no actual model/effort/cost telemetry;
those unavailable observations must stay unknown.

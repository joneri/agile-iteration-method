# Approved child model pools

## Purpose
Let the receiving coordinator choose each child's model/reasoning pair within
actual owner approval, task needs and cumulative resources.

## User experience
Approve exact pairs and resource limits in the normal delivery plan. The
coordinator then explains in-pool choices without asking for each child. Model
selection does not transfer coordination or final acceptance.

## How it works
The optional frozen `executionPlan.modelPool` supplies exact choices. Each child
start supplies `modelSelection` with task, risk and budget rationale. Native
preflight emits explicit launch settings; the host must actually receive them.
The current bound-thread UI bridge rejects pooled dispatch before queuing.
See the [canonical contract](../workflow/model-pools.md) for examples and launch steps.

## Inputs and outputs
- Inputs: approved pairs, cumulative starts and optional estimated-cost allowance;
  actual child identity, bounded assignment and typed observation evidence.
- Outputs: selected pair, explicit spawn parameters, retained start/history and
  requested versus reported/unknown settings and usage.

## Key decisions
Models and reasoning form atomic pairs. Optional profile candidates are reusable
planning input, never approval. Conservative reservations retain the original
estimate and maximum reported charge. Exact decimal arithmetic prevents a boundary
reservation from disappearing. Unknown usage is not zero or authenticated telemetry.

## Defaults and fallbacks
Pool-absent plans keep their inherited behavior. Unsupported settings require an
approved suitable alternative or owner escalation within remaining resources.
Coordinator work keeps its existing model. No automatic capability/cost ranking
or provider price service is introduced.

## Edge cases
Failed, retried, reworked and reviewer starts count cumulatively. Running
observations can block subsequent starts without creating a new work attempt.
Earlier mismatch/overrun reports cannot be erased by later unknown/lower reports.
Completed receipts remain immutable; later invoices need the existing owner route.

## Data correctness and trust
Typed evidence binds settings/cost to delivery scope, activity, child and attempt.
Hash checks establish bytes, not host identity. Provider billing is not capped by
estimated reservations. Host calls outside supported boundaries remain host-owned.

## Debugging
Run `python3 -m unittest discover -s tests -p 'test_aim_model_pool.py' -v`.
- Primary log: public helper preflight/receipts and bound observation artifacts.
- Good: exact approved pair reaches the child launcher, unknowns stay visible,
  root is unchanged, invalid or over-budget starts leave the ledger unchanged.
- Bad: inherited launch defaults, an unapproved pair, refunded history or a
  claimed actual model/cost copied from the request.

The release verification also covers official installed skill consumers, payload
refresh and the complete repository suite. Three authorized native microprobes
returned expected short responses for Luna/xhigh, Sol/medium and Astra/medium.
They prove distinct explicit launch requests and replies, not relative model
quality or host-confirmed model/effort/cost: that telemetry was unavailable.

## Related files
- `scripts/aim_quality/model_pool.py`
- `scripts/aim_quality/graph.py`
- `scripts/aim_stories.py`
- `tests/test_aim_model_pool.py`
- `docs/workflow/model-pools.md`

## Change log
- 2026-11-13: Introduced approval-bound child model selection in AIM 4.8.9.

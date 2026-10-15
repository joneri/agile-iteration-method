# AIM 4: User Stories from intent to acceptance

AIM 4 separates what people need from how the team delivers it. An intent can
produce several Epics. Each Epic contains independently prioritized User Stories
with persona, need, benefit and observable acceptance criteria. The product
backlog remains meaningful before any delivery has been planned.

PO owns requirements and priority. TDO refines Stories with PO and proposes a
coherent delivery selection. That selection may span Epics. A delivered increment
is a working product improvement; a Sprint, when used, is a timebox.

## Observable example

A customer needs to retry a failed payment. A support agent needs to find the
associated failure. An operator needs a weekly report. The first two Stories
can share a delivery across customer-recovery and support Epics. The reporting
Story stays in the backlog. Each selected Story retains its own criteria and
evidence. Accepting them leaves both Epics open until their outcomes are proven.

## Interface and persistence

The User Stories tab displays the requirements board (since 4.3, AIM UI opens
on the coherent Increment view). Each Story card displays its user perspective, value,
Epic, priority, state and acceptance criteria. Filters do not regroup delivery
selection or rewrite priorities. Status changes move the affected cards; an
unchanged refresh keeps the board stable.

`.aim/product-backlog.json` stores requirements and delivery relations, using
`scripts/aim_stories.py` and the public product-backlog schema. Chat and CLI use
the same lifecycle. The browser projects state and prepares ordinary chat
intents; it cannot accept a Story by moving a card.

## Acceptance and compatibility

A selection does not authorize implementation. Approved scope is frozen; review,
validation and acceptance must match it. Every selected Story criterion needs
current evidence. Accepted Stories do not close their Epics. Rework invalidates
earlier delivery evidence before another acceptance attempt.

Existing Epic workspaces and Portfolio Auto use their original contracts. Their
DI and INC identities remain delivery/planning history; no automatic migration
invents personas, requirements or acceptance for them. Delivery control and
history remain available beside the new Story board. New Stories use the
delivery-level lifecycle rather than the legacy per-Epic scheduler.

User Stories were introduced in AIM 4.0.0. The current product version is recorded in `VERSION`. Publication is separate from source
preparation. AIM UI remains Beta, and prior AIM 3 benchmark results remain
historical evidence.

See [the canonical contract](../workflow/user-stories.md),
[getting started](../product/getting-started.md) and [AIM UI](../product/aim-ui.md).

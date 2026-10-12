# EPIC-ONBOARD: A useful first session

Intent: INT-START — Help customers get started and recover from setup problems
Outcome class: Product
Owner: PO

## Outcome

A new customer can understand the product and obtain useful first-session value
without private setup knowledge. PO preserves this outcome while independently
prioritizing the Stories that contribute to it.

## User perspectives and Stories

- [US-SAMPLE](../user-stories/example-user-story.md): a new customer tries a sample
  workspace before entering real data.
- US-NEXT-STEP (draft): a returning customer understands which setup step remains.

A related support need belongs to EPIC-SUPPORT:
[US-DIAGNOSE](../user-stories/support-story.md). Stories from both Epics can share
a delivery selection. Do not treat that selection or an optional Sprint as the
requirement layer.

## Non-goals

- A full product redesign
- A new analytics initiative
- Multi-language support

## Epic acceptance criteria

- AC-1: A representative first-session journey reaches useful sample behavior
  without private instructions.
- AC-2: The customer can distinguish sample data from real data and remove the
  sample workspace safely.
- AC-3: Returning after an interruption exposes the next meaningful setup action.

## Closure evidence

Each in-scope Story has accepted criterion evidence. PO additionally verifies
the complete first-session and return journeys against these Epic criteria and
checks counterevidence. Finishing US-SAMPLE alone cannot close this Epic while
the return journey is unproven. Epic closure needs a separate scoped user decision.

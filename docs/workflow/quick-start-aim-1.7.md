> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick start AIM 1.7

Use this guide for the shortest correct path into the cost-saving AIM release.

## What 1.7 means

AIM 1.7 is the public release line that turns cost savings into the front-door promise.
It keeps the accepted AIM loop and runtime contract stable while making one thing much clearer:

- use AIM when you want to reduce wasted AI Credits, wasted tokens, and wasted agent loops
- especially in GitHub Copilot after the June 1, 2026 AI Credits transition

## Fast route

Choose one:

1. Start new work:

   ```text
   /aim start "EPIC: <desired user outcome>"
   Mode: Strict
   Cost profile: Cost Control
   ```

2. Continue existing work:

   ```text
   /aim continue
   ```

3. Check the setup:

   ```text
   /aim validate
   ```

## How AIM saves cost

- `Cost Control` keeps low-risk work narrow
- `Standard` avoids full rereads by loading context progressively
- `Deep` is reserved for pricing, trust, public behavior, migration, and other high-risk work
- one Done Increment at a time prevents expensive wandering
- the cost review checklist forces a quick spend decision before work starts and before an increment is accepted

## Fast cost check before you start

Ask these four questions:

1. Is this low-risk work, or could the billing facts or user trust be wrong?
2. Do we really need an expensive agentic surface for this task?
3. Is pricing research the real job, or is implementation the real job?
4. Can this be one narrow Done Increment without a long drifting session?

If the pricing facts themselves matter, start in `Deep`.
If the task is narrow and reversible, start in `Cost Control`.

## When to use Deep immediately

Start in `Deep` when:

- the Epic depends on current billing facts
- GitHub Copilot AI Credits are part of the problem
- you need to explain current spend across vendors
- getting the pricing story wrong would mislead the team

## Best follow-up docs

- [AIM cost review checklist](../features/aim-cost-review-checklist.md)
- [AIM GitHub Copilot cost reduction playbook](../features/aim-github-copilot-cost-reduction-playbook.md)
- [AIM cost-saving method](../features/aim-cost-saving-method.md)
- [AIM vendor cost baseline (June 2026)](../features/aim-vendor-cost-baseline-june-2026.md)
- [Quick start AIM 1.6 runtime guide](quick-start-aim-1.6.md)
- [AIM 1.7 document map](aim-1.7-doc-map.md)

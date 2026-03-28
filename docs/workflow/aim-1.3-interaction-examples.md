> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.3.x interaction examples

Use this document to see what the most important AIM checkpoints should feel like.

These are examples of interaction shape, not rigid copy-and-paste templates.
The required gate information is conceptual; the examples show how role-specific wording can satisfy it without forcing one visible section layout.

## 1. `PO` at Gate A

Purpose:
- frame the Epic and ask whether the Epic framing is correct

Good shape:
- `Role: PO`
- short Epic framing
- what is in and out of scope
- clear decision now:
  - approve Epic
  - request Epic changes
- clear next step if the Epic is approved

## 2. `TDO` before development

Purpose:
- propose the next single Done Increment

Good shape:
- `Role: TDO`
- why this increment is the right slice now
- how the increment can be demonstrated end to end
- clear decision now:
  - approve increment
  - adjust increment
- clear next step if the increment is approved

## 3. `Dev` implementation update

Purpose:
- report what changed and what was verified

Good shape:
- `Role: Dev`
- what changed
- verification already run
- blocker only if one exists

Bad shape:
- generic `approve or change` request when no decision is actually needed

## 4. `Reviewer` verification summary

Purpose:
- report findings, risk, and readiness

Good shape:
- `Role: Reviewer`
- no blocking findings or concrete findings
- what was verified already
- optional user test still worth doing

Bad shape:
- sounding like a second PO approval gate

## 5. Post-review `TDO`

Purpose:
- demo, test, and feedback checkpoint

Good shape:
- `Role: TDO`
- practical summary of the increment
- what was already verified
- how the user can test now
- feedback that is useful now
- clear decision now:
  - accept increment
  - request adjustment
- clear next step after either decision

## 6. `PO` after accepted increment

Purpose:
- Epic continuation or closure

Good shape:
- `Role: PO`
- what part of the Epic is now fulfilled
- what still remains, if anything
- clear decision now:
  - continue Epic
  - close Epic
  - capture new scope separately

## 7. Mode choice explanation

Good `Strict` explanation:
- pause at meaningful approval points

Good `Auto` explanation:
- continue through increments automatically unless escalation occurs
- still pause for final full review before Epic completion

## 8. Language reminders

Prefer:
- `the user`
- `PO`
- `TDO`
- `Dev`
- `Reviewer`
- `the next step`

Avoid:
- unclear `you`
- repeating the same section headers for every role when the step does not need them
- turning the conceptual gate minimums into a universal visible template

## Related documents
- `docs/features/aim-1.3-role-specific-interaction-model.md`
- `docs/workflow/quick-start-aim-1.3.md`
- `docs/workflow/aim-1.3-usage-guides.md`
- `docs/workflow/example-aim-1.3-reference-run.md`

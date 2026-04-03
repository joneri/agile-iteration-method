> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 interaction examples

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

Before:

```text
Role: Dev
Mode: Auto
Decision: implementation complete
What changed: updated the operational docs
Files: AGENTS.md, examples
Acceptance checks: docs read
Reply with approve or change.
Handoff: Reviewer should review the change.
```

After:

```text
Role: Dev
Mode: Auto
I removed the strongest legacy template traces from the operational contract and examples.

Verified:
- AGENTS.md now treats `approve` and `change:` as control inputs, not as the visible CTA model
- the examples now show role-specific before/after behavior for Dev, Reviewer, TDO post-review, and PO post-increment

Next step:
Reviewer checks whether any wording still makes the flow feel approval-shaped when no decision is actually needed.
```

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

Before:

```text
Role: Reviewer
Mode: Auto
Review result: ready
Files reviewed: AGENTS.md, examples
Reply approve to continue.
Handoff: TDO should prepare the next gate.
```

After:

```text
Role: Reviewer
Mode: Auto
No blocking findings in the selected operational files.

What I verified:
- Dev and Reviewer are described as informational by default
- visible `handoff` labels are no longer treated as mandatory everywhere
- the examples reinforce checkpoint-specific CTAs instead of one repeated approval rhythm

Optional user test:
- read the new Dev and Reviewer examples and check that they no longer sound like hidden approval gates

Next step:
TDO turns this into a practical demo, test, and feedback checkpoint.
```

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

Before:

```text
Role: TDO
Mode: Auto
Decision: increment ready
What changed: updated wording in operational docs
Files: AGENTS.md, workflow docs, examples
Acceptance checks: completed
Reply with approve or change.
Handoff: PO should decide.
```

After:

```text
Role: TDO
Mode: Auto
This increment changes how AIM sounds in real operation.
The main effect is that Dev and Reviewer now read like evidence checkpoints, while post-review TDO and post-increment PO use more natural checkpoint-specific language.

Already verified:
- core operational rules now treat `approve` and `change:` as transport shortcuts rather than universal visible CTAs
- the example guide now shows concrete before/after cleanup for the four highest-risk checkpoints

How to test now:
- read the before/after examples for Dev, Reviewer, post-review TDO, and post-increment PO
- check that each updated version sounds like a distinct role with a distinct purpose

Decision now:
- accept increment
- request adjustment

Next step after acceptance:
PO decides whether this Epic is complete or whether another cleanup increment is still needed.
```

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

Before:

```text
Role: PO
Mode: Auto
Decision needed: approve next step
What changed: interaction wording updated
Reply with approve or change.
Handoff: TDO should continue planning.
```

After:

```text
Role: PO
Mode: Auto
The most visible AIM 1.2-style template traces are now removed from the core operational contract and the example guide.
This Epic goal was to make lived AIM behavior match the role-specific AIM 1.4 interaction model, and this increment fulfills that outcome for the highest-impact files.

Epic decision now:
- continue Epic
- close Epic
- capture new scope separately

If the Epic continues:
TDO selects the next cleanup target that still feels mechanically template-shaped.
```

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
- `docs/features/aim-1.4-role-specific-interaction-model.md`
- `docs/workflow/quick-start-aim-1.4.md`
- `docs/workflow/aim-1.4-usage-guides.md`
- `docs/workflow/example-aim-1.4-reference-run.md`

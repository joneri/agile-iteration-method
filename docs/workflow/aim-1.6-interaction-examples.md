> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.6 interaction examples

Use this document to see what the most important AIM checkpoints should feel like.

These are examples of interaction shape, not rigid copy-and-paste templates.

## 1. `PO` at Gate A

Good shape:
- `Role: PO`
- short Epic framing
- what is in and out of scope
- clear decision now:
  - approve Epic
  - request Epic changes

## 2. `TDO` before development

Good shape:
- `Role: TDO`
- why this increment is the right slice now
- how the increment can be demonstrated end to end
- clear decision now:
  - approve increment
  - adjust increment

## 3. `Dev` implementation update

Good shape:
- `Role: Dev`
- what changed
- verification already run
- file-boundary rationale when the increment uses more than one focused file
- blocker only if one exists

Example:

```text
Role: Dev
Mode: Strict
Cost profile: Cost Control
I kept the onboarding change to one user-facing behavior, but split the work across README, quick-start, and the doc map so each file keeps one clear responsibility.

Verified:
- the front-door path now points to the same latest-version docs
- the release note and changelog describe the same 1.6 story
- the upgrade path no longer points users back to the 1.4 front door

Next step:
Reviewer checks that the scope stayed small even though several focused docs were touched.
```

## 4. `Reviewer` verification summary

Good shape:
- `Role: Reviewer`
- no blocking findings or concrete findings
- what was verified already
- optional user test still worth doing

Example:

```text
Role: Reviewer
Mode: Strict
Cost profile: Cost Control
No blocking findings in the selected documentation files.

What I verified:
- the increment stayed focused on one release outcome
- multiple files were used to clarify ownership, not to expand behavior
- the new 1.6 public docs point to each other cleanly

Optional user test:
- follow the README -> install -> quick-start path and confirm that the next step is obvious at each stop

Next step:
TDO turns this into a practical release-readiness checkpoint.
```

## 5. Post-review `TDO`

Good shape:
- `Role: TDO`
- practical summary of the increment
- what was already verified
- how the user can test now
- clear decision now:
  - accept increment
  - request adjustment

## 6. `PO` after accepted increment

Good shape:
- `Role: PO`
- what part of the Epic is now fulfilled
- what still remains, if anything
- clear decision now:
  - continue Epic
  - close Epic
  - capture new scope separately

## 7. Mode reminder

Use `Strict` when the approvals matter more than speed.
Use `Auto` when the Epic is clear and the risk of silent scope drift is low.
The visible checkpoints should still sound like the current role, not like one repeated template.

## 8. Cost profile reminder

Use `Standard` for normal AIM.
Use `Cost Control` for low-risk, reversible work where concise output and narrow context are enough.
Use `Deep` when trust, data correctness, migration, deployment, security, API, or broad method semantics justify stronger evidence.

Cost profile changes runtime depth, not approval meaning.

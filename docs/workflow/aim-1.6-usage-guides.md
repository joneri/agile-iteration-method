> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.6 usage guides

Use this guide when you already understand the basics and want the fastest correct pattern for common AIM work.

## 1. Start from a user-written Epic

Use when:
- the user already has a strong Epic candidate

Expected AIM behavior:
- `PO` validates the Epic candidate
- if it is already valid, `PO` may accept it with light normalization only
- if increment ideas are included, AIM preserves them as planning notes
- `TDO` still defines the next single Done Increment

## 2. Use focused files without expanding scope

Use when:
- one coherent user-facing increment is clearer in several focused files than in one overloaded file

AIM 1.6 rule:
- keep the behavior small
- split files only when each file owns a clearer responsibility
- do not use file count as the main measure of scope

Best reference:
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

## 3. Use Cost Control for low-risk work

Use when:
- the work is low-risk and reversible
- the change is documentation cleanup, narrow maintenance, or an obvious small fix
- trust, data correctness, migration, deployment, security, and public API behavior are not affected

AIM 1.6 rule:
- keep the normal roles, gates, and escalation rules
- reduce context loading, output length, subagent use, and review depth
- escalate to `Standard` or `Deep` if risk appears

Best reference:
- [AIM Cost Control Mode](../features/aim-cost-control-mode.md)

Example start:

```text
EPIC: Clean up stale documentation links so users see only current AIM docs.
Mode: Strict
Cost profile: Cost Control
```

## 4. Use Deep for high-risk work

Use when:
- the work affects trust, data correctness, public API behavior, deployment, migration, security, or broad method semantics

Expected AIM behavior:
- broader context loading is allowed
- review evidence should be stronger
- verification should match the blast radius
- scope still cannot expand without Gate B approval

## 5. Documentation written iteratively with AIM

Use when:
- the work is doc-first and behavior contracts matter more than runtime code

Recommended flow:
1. write the Epic in user-facing terms
2. let `TDO` choose one documentation slice that is understandable on its own
3. keep each Done Increment scoped to one coherent contract or operator concern
4. let `Dev` and `Reviewer` use informational checkpoints, not generic approval asks
5. use the post-review `TDO` checkpoint to invite practical doc review when useful

## 6. Resume from `.aim`

Use when:
- a previous Epic was interrupted

Expected AIM behavior:
- resume the incomplete Epic from the checkpoint
- do not silently create a second active Epic
- validate contradictions before continuing

## 7. Configure reviewer tooling

Use when:
- the repository needs explicit verification guidance

Set reviewer expectations through repo-aware policy, not hidden defaults.
The effective rule should be inspectable through:
- `AGENTS.md`
- `.github/agents/aim*.agent.md`
- `/aim config`

## 8. Upgrade to AIM 1.6

Use when:
- the repository already carries AIM 1.5 docs or helper packaging

Recommended path:
- `/aim upgrade 1.5-to-1.6`
- or [Migrate AIM 1.5 to AIM 1.6](migrate-aim-1.5-to-1.6.md)

Expected result:
- active public docs point to AIM 1.6
- cost control and file-boundary guidance are part of the visible release story
- adapter differences remain documented as adapter differences, not as method drift

## 9. Use controlled parallel subagents safely

Use when:
- the adapter exposes bounded parallel help
- repo policy allows it
- the work benefits from analysis, verification, or option generation in parallel

Allowed pattern:
- one main AIM thread owns `.aim/state.json`
- one main AIM thread owns gate progression and acceptance
- subagents produce scoped outputs only
- subagent outputs remain secondary to the synthesized main-thread decision

## 10. Discover commands quickly

If you are unsure where to begin:
- use [Quick start AIM 1.6](quick-start-aim-1.6.md)
- use `/aim help`
- inspect `.github/agents/aim.agent.md`

## 11. Know what to do at each checkpoint

Use this shorthand:
- `PO` first:
  - approve Epic or request Epic changes
- `TDO` before development:
  - approve increment or adjust increment
- `Dev`:
  - read the implementation update; no approval is normally needed
- `Reviewer`:
  - read the verification summary; no approval is normally needed
- `TDO` after review:
  - test now, accept increment, or request adjustment
- `PO` after accepted increment:
  - continue Epic, close Epic, or capture new scope separately

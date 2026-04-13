> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.5 usage guides

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

AIM 1.5 rule:
- keep the behavior small
- split files only when each file owns a clearer responsibility
- do not use file count as the main measure of scope

Best reference:
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

## 3. Documentation written iteratively with AIM

Use when:
- the work is doc-first and behavior contracts matter more than runtime code

Recommended flow:
1. write the Epic in user-facing terms
2. let `TDO` choose one documentation slice that is understandable on its own
3. keep each Done Increment scoped to one coherent contract or operator concern
4. let `Dev` and `Reviewer` use informational checkpoints, not generic approval asks
5. use the post-review `TDO` checkpoint to invite practical doc review when useful

## 4. Resume from `.aim`

Use when:
- a previous Epic was interrupted

Expected AIM behavior:
- resume the incomplete Epic from the checkpoint
- do not silently create a second active Epic
- validate contradictions before continuing

## 5. Configure reviewer tooling

Use when:
- the repository needs explicit verification guidance

Set reviewer expectations through repo-aware policy, not hidden defaults.
The effective rule should be inspectable through:
- `AGENTS.md`
- `.github/agents/aim*.agent.md`
- `/aim config`

## 6. Upgrade to AIM 1.5

Use when:
- the repository already carries AIM 1.4 docs or helper packaging

Recommended path:
- `/aim upgrade 1.4-to-1.5`
- or [Migrate AIM 1.4 to AIM 1.5](migrate-aim-1.4-to-1.5.md)

Expected result:
- active public docs point to AIM 1.5
- modularity and file-boundary guidance are part of the visible release story
- adapter differences remain documented as adapter differences, not as method drift

## 7. Use controlled parallel subagents safely

Use when:
- the adapter exposes bounded parallel help
- repo policy allows it
- the work benefits from analysis, verification, or option generation in parallel

Allowed pattern:
- one main AIM thread owns `.aim/state.json`
- one main AIM thread owns gate progression and acceptance
- subagents produce scoped outputs only
- subagent outputs remain secondary to the synthesized main-thread decision

## 8. Discover commands quickly

If you are unsure where to begin:
- use [Quick start AIM 1.5](quick-start-aim-1.5.md)
- use `/aim help`
- inspect `.github/agents/aim.agent.md`

## 9. Know what to do at each checkpoint

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

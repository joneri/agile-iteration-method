# AIM 2.0 Working-State Boundaries

## Purpose

Define what AIM 2.0 working state is, where it lives, and how it differs from reusable repo profile data.

This prevents AIM from mixing:

- active Epic and Done Increment state
- reusable repository intelligence
- reference docs
- adapter packaging

## User experience

Users should be able to answer:

- what work is currently active?
- what increment was last accepted?
- whether the Epic is still open
- where local state is stored
- what repo intelligence was reused
- what data is safe to share with the team

The user should not need to commit active AIM state just to use AIM personally.

## How it works

Working state is the temporary, resumable state for active AIM work.

It includes:

- active Epic id and status
- active Done Increment id
- current role
- last gate passed
- accepted increment history
- current assumptions
- concise decisions
- reviews for the current work
- branch-local notes needed to resume safely

It does not include durable repo knowledge that should be reused across unrelated work.
That belongs in the repo profile.

## Working state vs repo profile

| Concern | Working state | Repo profile |
| --- | --- | --- |
| Active Epic | yes | no |
| Active Done Increment | yes | no |
| Gate status | yes | no |
| PO acceptance | yes | no |
| Review findings for current increment | yes | no |
| Repo structure | no, except local assumption | yes |
| Build/test commands | only if run for current increment | yes |
| Risk zones | only if discovered for current increment | yes |
| Ownership boundaries | only if relevant to current increment | yes |
| Freshness triggers | no | yes |
| Cost/reuse hints | current run summary | reusable defaults |

The same fact may appear in both places with different meaning.
For example, a test command in working state means "this was run for this increment."
A test command in the repo profile means "this is a reusable validation path for this repo area."

## Personal AIM choices

Personal AIM may keep working state local or commit it when the solo user wants
audit, handoff, or visible process history.

Local option:

- working state is not committed
- repo profile may be local or adapter-managed
- docs come from AIM distribution or links
- branch-specific state stays tied to the local worktree or adapter session

Good local storage options include:

- ignored `.aim/` runtime workspace
- adapter-managed storage
- local user workspace outside the repository
- `.git/info/exclude` for local-only AIM paths

The key rule:

> Personal AIM can be repo-aware without committing active AIM state, but it
> does not forbid committing AIM state or other AIM-owned files.

## Team AIM defaults

Team AIM may share a tiny repo profile, but working state stays local by default.

Default behavior:

- shared profile or pointer is intentionally committed
- active Epic/increment state is not shared unless the team explicitly chooses that workflow
- each developer can resume their own AIM work locally
- shared profile facts help future AIM runs start cheaper

Teams may decide to share some state for pair work, handoff, or audit.
That is a team policy decision, not a requirement for Team AIM.

## Enterprise AIM direction

Enterprise AIM may later define approved state storage or audit export rules.

Until then:

- central policy may govern profiles
- active working state remains local unless an approved shared storage exists
- profile registries must not become hidden gate owners

Managed policy can constrain AIM.
It must not redefine AIM role order, gate meaning, or PO acceptance.

## Lifecycle rules

### Start

When starting a new Epic:

1. create working state for the active Epic
2. select adoption mode
3. load or create repo profile separately
4. enter Gate A

### Gate B

When planning the next Done Increment:

1. read active working state
2. reuse repo profile if fresh enough
3. load local context for the planned increment
4. write the Done Increment plan to working state

### Gate E

When an increment is accepted:

1. mark the Done Increment accepted
2. preserve the increment decision and review evidence
3. update accepted increment history
4. ask whether the Epic continues or closes

An accepted Done Increment does not automatically complete the Epic.
The Epic closes only when the PO accepts that the Epic outcome is fulfilled.

### Continue

When continuing:

1. resume from working state first
2. check repo profile freshness
3. avoid rebuilding context unless needed
4. continue with the next role/gate from state

### Branch switch

When branch changes:

1. keep current working state local to the branch/worktree
2. reuse repo profile only if freshness rules pass
3. revalidate the smallest affected locality when branch differences matter
4. escalate if state and branch reality conflict

### Archive

When an Epic is complete:

1. preserve enough state to understand accepted increments
2. archive or summarize old working artifacts
3. keep reusable repo facts in the repo profile only when they are stable beyond the Epic

## Inputs and outputs

- Inputs:
  - active Epic
  - current branch/worktree
  - selected adoption mode
  - existing working state
  - existing repo profile
  - current gate and role

- Outputs:
  - resumable working state
  - clear current role/gate
  - accepted increment history
  - profile freshness decision
  - concise cost/reuse summary

## Key decisions

- Working state is not the repo profile.
- Accepted increments do not automatically close an Epic.
- Personal AIM working-state sharing is the solo user's choice.
- Team AIM shares profile facts, not active state, by default.
- Enterprise AIM can govern state later without redefining AIM core.
- Reusable facts discovered during an increment should be promoted to the repo profile only when they are stable beyond the active work.

## Defaults and fallbacks

- Default working-state sharing: local-only.
- Default resume behavior: read working state before broad context.
- Default branch behavior: branch-local state, profile reuse only if fresh.
- Fallback if working state is missing but recoverable: reconstruct from accepted artifacts and report assumptions.
- Fallback if working state conflicts with repo profile: trust active working state for gate progression, then revalidate profile facts.
- Fallback if working state conflicts with user intent: escalate to PO.

## Edge cases

- Pairing or handoff may require intentionally shared working state.
- Audit-heavy teams may require exported summaries after Gate E.
- A stale repo profile can mislead startup; revalidate before reuse.
- A stale working state can misrepresent acceptance; stop and repair before continuing.
- Public commits must not include secrets, credentials, or proprietary local state.

## Data correctness and trust

The main AIM thread owns working-state mutation.

Only the main AIM thread may change:

- active Epic status
- active Done Increment id
- current role
- gate status
- acceptance state
- Epic completion state

Subagents and helper adapters may suggest updates, but they do not own state transitions.

## Debugging

The single best check is whether AIM can answer:

> Is the Epic still active, and which Done Increment is next?

- Primary log: runtime state summary before Gate B
- What "good" looks like:
  - AIM knows the active Epic id
  - AIM knows whether the last increment was accepted
  - AIM does not close the Epic without PO acceptance
  - AIM separates profile reuse from gate progression
  - AIM resumes without broad rereads when state is healthy
- What "bad" looks like:
  - AIM treats a model doc as the Epic
  - AIM treats one accepted increment as automatic Epic completion
  - AIM stores reusable repo facts only in transient review notes
  - AIM commits local active state unintentionally

## Validator support

`scripts/validate_aim_runtime.py` performs a narrow AIM 2.0 separation check.

If an optional repo profile artifact exists, the validator checks for active working-state markers such as:

- `epicStatus`
- `activeIncrementId`
- `currentRole`
- `lastGatePassed`
- acceptance or completion state

Finding those markers in a repo profile is recoverable, not an AIM core blocker.
The fix is to move active Epic, increment, gate, review, or acceptance state back into `.aim` working-state artifacts.

## Related files

- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/team-profile-artifact.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `docs/workflow/aim-adapter-guidance.md`
- `scripts/validate_aim_runtime.py`

## Change log

- 2026-06-05: Documented validator support for profile/state separation checks.
- 2026-06-05: Linked current migration classification checks.
- 2026-06-05: Initial AIM 2.0 working-state boundary model.

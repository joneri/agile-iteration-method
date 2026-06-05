# AIM 2.0 Personal Local Profile Storage

## Purpose

Define how one developer can reuse AIM repo intelligence without committing `aim.profile.yaml` or copying AIM docs into the repository.

Personal AIM should preserve the value of repo-aware startup while leaving no required repository footprint.

## User experience

A developer can use AIM personally in a large or protected repository and still get reusable repo awareness across sessions and branches.

Personal AIM stores the profile locally by default.
The repository does not need a committed AIM profile, docs package, adapter files, or working-state artifacts.

## Storage locations

Default local profile location:

```text
~/.aim/profiles/<repo-fingerprint>/profile.yaml
```

`<repo-fingerprint>` should be derived from the repository remote URL when available.
If no remote is available, use a stable hash of the absolute repository root path.

Adapter fallback location:

```text
.aim/profile.yaml
```

The fallback is repo-local but ignored by default.
Use it only when the adapter cannot use a user-level AIM profile store.

## What stays local

Personal AIM keeps these local by default:

- repo profile
- active working state
- branch-local assumptions
- startup summaries
- refresh notes
- local validation preferences

Personal AIM must not commit these by default.

## What does not belong in the local profile

The personal local profile must not contain:

- active Epic state
- active Done Increment state
- Gate approval state
- review findings for one branch
- secrets, credentials, or tokens
- proprietary details that the developer is not allowed to store locally
- copied AIM reference docs

## Reuse across sessions and branches

AIM may reuse the personal profile when:

- the repo fingerprint matches
- the profile owner is the current local user or adapter identity
- the current branch is within the same repo identity
- no freshness trigger has fired
- the active work is inside a known locality boundary
- the selected cost profile allows reuse

AIM should refresh the smallest affected locality when:

- the branch changes relevant package or service metadata
- validation commands changed
- ownership or risk docs changed
- lockfiles or build scripts changed
- the work crosses a risk or ownership boundary
- the user requests `Deep`

Branch switching should not force a cold start by default.
It should trigger a freshness check, then reuse or partially refresh the profile.

## Relationship to Team AIM

When both a personal local profile and root `aim.profile.yaml` exist, AIM should layer them this way:

1. `.aim/state.json` for active runtime state
2. personal local profile for the developer's local reuse hints
3. root `aim.profile.yaml` for shared team repo intelligence
4. directly affected files and nearest metadata
5. broader docs only when risk or missing evidence requires them

Team profile facts are the shared baseline.
Personal profile facts may narrow local startup, remember branch-local validation preferences, or cache user-local discovery.

Personal facts must not silently contradict Team AIM.
If personal and team profiles conflict on commands, ownership, risk, or policy, AIM should prefer the Team profile or current repository evidence and report the conflict as a refresh or escalation reason.

## Commit safety

Personal AIM avoids leaking into commits by default:

- the primary profile path is outside the repository
- the fallback `.aim/profile.yaml` path is covered by the existing `/.aim` ignore rule
- personal summaries and refresh notes stay in ignored/local working state
- a team must explicitly export or copy a tiny profile to root `aim.profile.yaml` to share it

Exporting from Personal AIM to Team AIM should be an intentional action, not an automatic side effect.

## Profile-source summary

When a personal profile is reused, the startup or Gate B summary should say so:

```text
Profile source: ~/.aim/profiles/<repo-fingerprint>/profile.yaml (personal, profile_ready)
Reused facts: commands, locality, freshness, avoid-by-default context
Selected locality: <area>
Avoided context: <docs/scans avoided>
Expansion reason: <none or reason>
Cheap validation first: <command>
```

When both personal and team profiles are used, name both sources and state whether the personal profile narrowed or refreshed the team baseline.

## Key decisions

- Personal AIM defaults to zero committed files.
- The user-level profile store is preferred over repo-local storage.
- `.aim/profile.yaml` is a fallback only, not the primary Personal AIM model.
- Team AIM remains the intentional sharing path.
- Profile reuse is allowed across branches, but freshness checks decide whether partial refresh is needed.

## Edge cases

- Some organizations may forbid local profile persistence; use session-only profile memory or Enterprise AIM policy.
- A repository without a remote should use a root-path fingerprint and refresh if the path changes.
- A developer may have multiple clones of the same repo; remote-based fingerprinting allows reuse, but local path differences should remain visible.
- Sensitive repos may require excluding risk or architecture details from the local profile.

## Debugging

The best check is whether AIM can answer:

> Which local profile did you reuse, and why was it safe for this branch?

What "good" looks like:

- profile source is outside the repo or under ignored `.aim/`
- branch freshness is checked
- Team profile conflicts are reported
- no active state appears in profile storage
- export to Team AIM is explicit

What "bad" looks like:

- a personal profile appears in `git status`
- local profile facts override team risk or ownership silently
- branch switching causes a full cold start without a freshness reason
- active Gate or Epic state is stored as repo profile data

## Related files

- `docs/features/aim-2-repo-profile-and-footprint-model.md`
- `docs/features/aim-2-profile-source-summary.md`
- `docs/features/aim-2-working-state-boundaries.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `scripts/validate_aim_runtime.py`

## Change log

- 2026-06-05: Initial Personal AIM local profile storage contract.

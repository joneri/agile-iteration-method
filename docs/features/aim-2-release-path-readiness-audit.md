# AIM 2.0 Release Path Readiness Audit

## Purpose

Identify the smallest real blocker between the current AIM 2.0 operating model and a genuine AIM 2.0 release path after AIM 1.7.

This is a narrow release-path audit, not another strategy document.

## Current release-path judgment

AIM 2.0 is materially closer to a releasable model, but it is not yet ready to replace AIM 1.7 as the public front door.

The operating model is now strong enough to prove the product direction:

- Personal AIM has a zero-footprint local profile path.
- Team AIM has a concrete root `aim.profile.yaml` artifact.
- The validator reports repo-profile readiness.
- Startup behavior is profile-first after state.
- The profile-source summary is generated from actual profile files.
- Working state, repo profile, docs, adapter helpers, and runtime are separated more clearly.

## Smallest blocker

The smallest release blocker is the missing AIM 2.0 front-door operating path.

Users can now inspect the pieces, but the public start/install surface still says AIM 2.0 is planning guidance under the AIM 1.7 release line.
That means AIM 2.0 is operational internally, but not yet usable as a coherent release model from the first user decision.

The gap is not another strategy gap.
The gap is product entry:

- a user cannot yet start with "Personal AIM" or "Team AIM" as the obvious first path
- the front door does not yet say when to choose local profile versus root `aim.profile.yaml`
- install/start docs still lead with AIM 1.7 and describe AIM 2.0 as future direction
- the generated profile-source summary exists, but the user-facing start path does not yet make it the normal feedback signal

## What is already strong enough

The following are strong enough for an AIM 2.0 release path:

- AIM core remains unchanged.
- Gate ownership and escalation remain intact.
- Personal and Team storage boundaries are concrete.
- Team reuse has a smallest committed artifact.
- Personal reuse has a zero-footprint local path.
- Profile readiness and profile-source summaries are validator-backed.
- Profile-first startup now changes actual AIM behavior.
- Cost reduction applies to startup, scanning, resume, branch switching, and profile reuse.

## What is not yet strong enough

The following still prevent release confidence:

- AIM 2.0 does not yet have a concise public quick-start path.
- Install guidance does not yet present Personal and Team AIM as first-class operating choices.
- README still sells AIM 1.7 as the current product and frames 2.0 as a future/planning direction.
- There is no compact "AIM 2.0 start here" surface that explains:
  - Personal AIM: no commits, local profile, local state
  - Team AIM: root `aim.profile.yaml`, shared profile, local state
  - Full embedded AIM: explicit repo-owner choice

## Single next product increment

The next Done Increment should create the AIM 2.0 front-door operating path.

Recommended scope:

- add `docs/workflow/quick-start-aim-2.0.md`
- explain Personal AIM and Team AIM as the first choices
- show where profile, state, docs, and runtime live
- show the profile-source summary as the expected startup feedback
- link from the AIM 1.7 install/doc-map pages without claiming final AIM 2.0 release completion

Acceptance target:

- a new user can read one short page and understand how to start with Personal AIM or Team AIM without copying the whole method into a repository
- the page makes the current 2.0 operating model usable while still being honest that the broader release switch is not complete

## Non-goals

This audit does not recommend:

- changing AIM core
- renaming the release in README immediately
- claiming AIM 2.0 is fully released
- adding managed enterprise governance
- adding a full CLI implementation before the front-door path is clear

## Related files

- `README.md`
- `docs/workflow/install-aim-1.7.md`
- `docs/workflow/aim-1.7-doc-map.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `docs/features/aim-2-repo-profile-and-footprint-model.md`
- `docs/features/aim-2-personal-local-profile-storage.md`
- `docs/features/aim-2-profile-source-summary.md`

## Change log

- 2026-06-05: Initial narrow AIM 2.0 release-path readiness audit.

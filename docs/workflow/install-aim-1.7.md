> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 1.7

Use this guide when you want the current cost-saving AIM front door in a repository.

AIM 1.7 is the current release line.
AIM 2.0 Personal AIM and Team AIM are now current operating install choices on this release surface.
The broader AIM 2.0 release transition is still incomplete, so AIM 1.7 remains the main release line.

## What 1.7 changes

AIM 1.7 does not replace the accepted runtime contract.
It changes the public release story:

- AIM should be easy to adopt specifically for reducing AI spend
- GitHub Copilot AI Credits are now a first-class operator concern
- the front door should explain how AIM saves money, not only that it has cost profiles

## Choose the adoption footprint

AIM 1.7's fully embedded install path is still valid, but it is not the only adoption model AIM is moving toward.

For new large repositories, protected enterprise repositories, or individual developers who do not own repo policy, start by choosing the smallest footprint that fits.

| Path | Repository mutation | Best for | Status |
| --- | --- | --- | --- |
| Personal AIM | none by default | one developer trying AIM or working in a protected repo | current AIM 2.0 operating install choice |
| Team AIM | root `aim.profile.yaml` profile or pointer | a team sharing commands, risk zones, and validation paths | current AIM 2.0 operating install choice |
| Full embedded AIM | full AIM docs and adapter files | templates, AIM itself, repos that intentionally want AIM committed | current AIM 1.7 install path |

Personal and Team AIM are explained in [AIM 2.0 low-footprint adoption](aim-2-low-footprint-adoption.md).
The reusable profile shape is defined in [AIM 2.0 repo profile and footprint model](../features/aim-2-repo-profile-and-footprint-model.md).
The smallest Team AIM artifact is root `aim.profile.yaml`; it can contain a tiny profile or point to managed/shared profile storage.

This page does not claim the full AIM 2.0 release transition is finished.
It defines the current install choices that make the AIM 2.0 operating path usable while the broader release surface continues to transition.

## Full embedded AIM 1.7 install

Use this path when the repository owner intentionally wants AIM committed into the repo.

You need the same canonical AIM runtime files:

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`

Then add the current front-door docs:

- `README.md`
- `docs/workflow/quick-start-aim-1.7.md`
- `docs/workflow/install-aim-1.7.md`
- `docs/workflow/aim-1.7-doc-map.md`

This is the highest-footprint path.
Do not treat it as required for every individual developer who wants to use AIM.

## AIM 2.0 low-footprint direction

The AIM 2.0 adoption model separates:

- AIM runtime: supplied by the tool, adapter, or local environment
- AIM repo profile: reusable repo intelligence
- AIM working state: local resumable state for the current work
- AIM docs: reference material

For Personal AIM, no committed AIM files are required by default.

For Team AIM, the intended shared footprint is a small repo profile or pointer, not the full AIM method package.
The default Team AIM file name is `aim.profile.yaml` at the repository root.

For Managed AIM, central policy and governed profile registries remain a later direction.

Command shapes in AIM 2.0 docs remain conceptual direction until the runtime and adapter surfaces are fully transitioned.

## Best next step

After installation:

- start with [Quick start AIM 1.7](quick-start-aim-1.7.md)
- start with [Quick start AIM 2.0](quick-start-aim-2.0.md) when you want the low-footprint Personal AIM or Team AIM operating path
- keep [Install AIM 1.6](install-aim-1.6.md) as the deeper runtime-family setup guide
- use [AIM 2.0 low-footprint adoption](aim-2-low-footprint-adoption.md) when repository mutation is the adoption blocker
- use [AIM 2.0 repo profile and footprint model](../features/aim-2-repo-profile-and-footprint-model.md) when designing a reusable repo profile
- use [AIM cost-saving method](../features/aim-cost-saving-method.md) when the team asks how AIM actually saves money

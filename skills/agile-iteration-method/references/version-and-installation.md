<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/version-and-installation.md
-->

## Resolved package metadata

- AIM product release: `3.0.3`
- Runtime contract: `2.0`
- Runtime-state schema: `1.0`
- Installer manifest: `1.0`
- Repo-profile schema: `0.2`
- Personal-hints schema: `0.1`
- Project-role schema: `0.1`
- Public skill package format: `11`

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM public Agent Skill distribution

## Purpose

Define the portable Agent Skill distribution of complete AIM through the open
skills ecosystem. This is one additional distribution surface for AIM, not a
second method, runtime, product edition, or reduced AIM Lite implementation.

The public package is generated at `skills/agile-iteration-method/` from AIM's
canonical workflow, adapter, installer-manifest, and schema sources. Files below
that generated directory are never edited as independent method truth.

## Public identity and installation

The public skill name is `agile-iteration-method`. The GitHub source is
`joneri/agile-iteration-method`.

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method
```

The skills CLI discovers `skills/agile-iteration-method/SKILL.md` and installs
the complete package directory, including its package-local references. It does
not publish or download a separate AIM npm package.

Target a supported agent explicitly when needed:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent codex --yes
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent github-copilot --yes
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent claude-code --yes
```

Installed skills can be refreshed through the standard CLI:

```bash
npx skills update agile-iteration-method --yes
```

When supported by the installed CLI, `npx skills use` may resolve the skill and
produce its complete entry prompt without a durable installation.

## Complete and self-contained behavior

The installed package must work when the AIM source repository is not present.
It includes the AIM core, command contract, adapter entry/bootstrap behavior,
repository calibration, project-agent configuration, operating modes, schemas,
installer-manifest contract, and resolved version metadata needed at runtime.

The package preserves:

- `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- PO outcome and acceptance ownership
- TDO Done Increment ownership and technical validation
- Dev implementation and independent Reviewer examination
- Gates A, B, and E plus reported Gates C and D
- Strict and Auto execution modes
- Standard, Cost Control, and Deep runtime-depth profiles
- repository calibration and durable repo-awareness boundaries
- project-specific role configuration through `aim.roles.yaml`
- explicit scope escalation
- one main AIM thread as the sole owner of `.aim/state.json` and gates
- sequential fallback with unchanged semantics when native specialists are
  unavailable

An active target repository may optionally provide `aim.profile.yaml`,
`aim.roles.yaml`, supplier-native specialists, and `.aim/` runtime state. Their
absence activates the documented calibration, configuration, or startup
fallback; it does not justify flattening AIM into generic task planning.

## Adaptive installer relationship

The public Agent Skill installs AIM's portable workflow entry point and the
dependency-free, package-local AIM UI payload used by `/aim ui`. The launcher
runs from the skill package and stores only bounded process metadata under the
user's AIM home; it does not place UI code or runtime state in target repos.
The adaptive installer remains a separate source-checkout workflow for a
reviewed repository footprint, native project specialists, and
supplier-specific configuration. Repo-writing footprints receive
`scripts/aim_ui_control.py`, `scripts/aim_ui.py`, and `aim-ui/`, while
zero-repo-write footprints place the same payload below
`~/.aim/installs/agile-iteration-method/`.

The portable skill must never download or execute a remote bootstrap, and it
must never execute installer or validator scripts discovered in a target
repository. It performs package-local validation directly from the bundled AIM
contracts. When broader adaptive setup is wanted, direct the user to the
maintained install guide so they can clone and inspect AIM's source, run a
no-write preview, and explicitly decide whether to apply it.

The public Agent Skill contains and may execute only its own package-local AIM
UI payload in response to explicit `/aim ui` intent. The UI binds to loopback,
remains read-only, and may observe a repo without creating `.aim`. This does not
authorize installer or validator execution from a target repository.

`/aim upgrade` updates a public skill through the standard skills CLI. A
separately reviewed AIM source checkout may use its own adaptive installer, but
the portable skill does not execute that checkout. Neither path may rewrite
active `.aim/` runtime state.

`/aim configure-agents` reads or creates `aim.roles.yaml` from the package-local
project-role schema, shows proposed supplier-native changes, preserves user
collisions, and updates only the selected adapters. Only the main AIM thread may
read active state for safety; configuration never advances or rewrites it.

## Version model

The generated package records these independent contracts:

- AIM product release from `VERSION`
- AIM runtime contract from the canonical release manifest
- runtime-state schema version from
  `schemas/aim-runtime-state.schema.json`
- adaptive installer manifest version from
  `install/aim-install-manifest.yaml`
- repo-profile, Personal-hints, and project-role schema versions
- public Agent Skill package-format version

The public package and Pages artifact include the Draft 2020-12 runtime-state
schema. Install, update, validation, and package generation may inspect or
normalize legacy state read-only, but never migrate or rewrite active `.aim`
artifacts automatically.

The package-format version changes only when the generated public package
structure or compatibility contract changes. It is not a second AIM product
version.

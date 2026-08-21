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

The public Agent Skill installs AIM's portable workflow entry point. The
adaptive installer remains a separate source-checkout workflow for a reviewed
repository footprint, native project specialists, and supplier-specific
configuration. It also packages the read-only AIM UI: repo-writing footprints
receive `scripts/aim_ui.py` and `aim-ui/`, while zero-repo-write footprints place
the same payload below `~/.aim/installs/agile-iteration-method/` and require an
explicit `--repo` target at launch.

The portable skill must never download or execute a remote bootstrap, and it
must never execute installer or validator scripts discovered in a target
repository. It performs package-local validation directly from the bundled AIM
contracts. When broader adaptive setup is wanted, direct the user to the
maintained install guide so they can clone and inspect AIM's source, run a
no-write preview, and explicitly decide whether to apply it.

The public Agent Skill does not contain or execute the UI server payload. This
keeps portable skill installation non-executable and prevents target-repository
writes; users who want AIM UI select the separately reviewed adaptive path.

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

## Generation and verification

```bash
python3 scripts/build_public_skill.py
python3 scripts/build_public_skill.py --check
```

Generation must be deterministic, validate YAML frontmatter and local package
references, record source provenance, and fail on missing or inconsistent
canonical inputs. Check mode is read-only and fails when canonical sources and
the committed public package differ.

Release readiness must run check mode. Canonical behavior, version, manifest,
schema, or public-package changes cannot pass release validation while the
generated package is stale.

## GitHub and skills.sh publication

There is no separate AIM upload API or manual skills.sh release. Publication is:

1. place a valid generated skill on the public GitHub default branch through the
   repository's normal protection and review workflow
2. perform a real installation from that public GitHub source with the official
   skills CLI
3. allow anonymous aggregate CLI installation telemetry to make the skill
   eligible for skills.sh discovery and ranking

Indexing may be asynchronous. Report the public commit, successful installation
command, expected skills.sh URL, and current HTTP or CLI evidence. Never claim a
separate upload, guarantee a ranking, or generate artificial installations to
manipulate telemetry.

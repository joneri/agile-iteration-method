# AIM 2.0 Repo-Profile Schema

## Purpose

Define the versioned machine-readable contracts for AIM repo-awareness profiles
and Personal hints.

The public schema files are:

```text
schemas/aim-repo-profile.schema.json
schemas/aim-personal-hints.schema.json
```

They are published at their declared stable IDs:

```text
https://joneri.github.io/agile-iteration-method/schemas/aim-repo-profile.schema.json
https://joneri.github.io/agile-iteration-method/schemas/aim-personal-hints.schema.json
```

Publication validation fails when source `$id` values, artifact paths, or the
canonical Pages origin drift.

They use JSON Schema Draft 2020-12 and validate YAML after it is decoded into
ordinary data values.

## Authority Boundary

The contract has three owners:

- Schema owns structure.
- Validator owns product rules.
- Documentation owns meaning and rationale.

JSON Schema defines required fields, primitive shapes, allowed structural
values, canonical category presence, stable entry IDs, and document loading
states. It does not decide workflow policy, profile precedence, safe operating
mode behavior, or whether a structurally valid value is coherent with AIM.

`scripts/validate_aim_runtime.py` owns executable product rules such as:

- supported schema-version decisions
- stable repo-awareness never living under `.aim/`
- durable repo-awareness never citing `.aim/reviews`, `.aim/increments`,
  `.aim/decisions`, `.aim/archive`, or other runtime artifacts as maintained
  knowledge sources
- `.aim/state.json` remaining valid for active resume/checkpoint behavior
- runtime state never leaking into profiles
- Personal hints never claiming shared policy authority
- installer seeds agreeing with documented product contracts

The repo-awareness documents explain what fields mean, why the boundaries
exist, and how users and tools should respond.

## Repo-Profile Version

The first machine-readable shared-profile contract is:

```yaml
aimRepoProfile:
  profileVersion: "0.2"
```

Version `0.2` requires:

- calibration status, source, confidence, and open uncertainties
- repository name and default branch
- adoption mode, footprint, sharing intent, and profile owner
- profile, Personal-hints, working-state, and documentation locations
- all ten canonical `repoKnowledge` categories

Every non-empty knowledge entry requires a stable `id`. Document entries also
require `path` and `loading`.

## Personal-Hints Version

The first machine-readable Personal-hints contract is:

```yaml
aimPersonalHints:
  hintsVersion: "0.1"
  repoFingerprint: example-repo
  profileOwner: local-user
  hints:
    commands: []
    localities: []
    docs: []
    habits: []
    avoidByDefault: []
    freshness: []
```

Personal hints are a user-level compatibility layer, not a second shared
profile. Their meaning and precedence are defined by
`docs/workflow/personal-local-profile-storage.md`; the validator rejects
attempts to place shared ownership, risk, security, migration, deployment, or
validation policy in this layer.

## Validation

Run:

```sh
python3 scripts/validate_aim_runtime.py .
```

The validator:

1. loads both public JSON Schema documents
2. decodes `aim.profile.yaml`
3. applies AIM's dependency-free JSON Schema subset
4. applies product rules separately
5. validates the standard installer seed and legacy migration seeds
6. validates the canonical empty Personal-hints seed

The dependency-free subset supports the schema keywords AIM publishes:

- local `$ref`
- `type`
- `required`
- `properties`
- `additionalProperties`
- `const`
- `enum`
- `items`
- `minItems`
- `minLength`
- `pattern`

External tooling may use any conforming Draft 2020-12 implementation.

## Migration Rules

Schema versions are explicit data-contract versions, not AIM release numbers.

For a compatible additive revision:

- keep the current version when old valid documents remain valid
- add only optional fields or broaden structurally accepted values
- update tests, installer seeds, validator support, and docs together

For a breaking revision:

- introduce a new `profileVersion` or `hintsVersion`
- add or publish the matching schema contract
- teach the validator to report the old version and available migration
- update installer seeds only after validator support exists
- provide a deterministic reviewed migration; never silently overwrite profile
  facts, ownership, confidence, or policy
- keep old-version handling explicit until the support window ends

A schema change is incomplete if only the schema file changes. Installer seeds,
validator behavior, fixtures, and semantic documentation must move in the same
reviewed increment.

## Related Files

- `schemas/aim-repo-profile.schema.json`
- `schemas/aim-personal-hints.schema.json`
- `docs/workflow/repo-awareness.md`
- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/personal-local-profile-storage.md`
- `scripts/aim_validator/profile_contract.py`
- `scripts/aim_validator/schema_subset.py`
- `scripts/validate_aim_runtime.py`
- `docs/workflow/release-publication-model.md`

## Change Log

- 2026-06-07: Published the first versioned repo-profile and Personal-hints
  structural contracts.

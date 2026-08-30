<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/product-coherence-validation.md
-->

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 Product-Coherence Validation

## Purpose

Define what AIM means when its validator reports `healthy`.

`healthy` is a product statement, not only a filesystem statement. It means the
required structures parse, representative behavior matches canonical contracts,
adapter promises have packaged evidence, and no release-blocking contradiction
is known.

## Validation tiers

### Structural

Checks that:

- required files and runtime paths exist
- structured files parse
- runtime state, profile storage, and ownership boundaries are valid
- required canonical surfaces are present

### Behavioral

Checks executable or generated evidence:

- the standard adaptive install and legacy compatibility plans can be generated
- all selected suppliers receive PO, TDO, Dev, and Reviewer native agents plus `aim.roles.yaml`
- installer plans preserve root-file exclusions and mode-specific behavior
- adapter packages contain required command and fallback capabilities
- upgrade behavior is actionable and collision-safe

### Product coherence

Compares claims with evidence:

- operating-mode docs against generated installer plans
- public native-support claims against Codex, Claude, and Copilot packages
- public `/aim upgrade` claims against canonical and adapter upgrade behavior
- canonical docs against conflicting statements in other product surfaces

A direct disagreement between authoritative claims and generated behavior is a
`Contradiction`, not a warning.

For completed Epics, product coherence also checks claim strength against the
declared outcome class and closure evidence. A POC, fixture, mock, internal
contract test, or implementation-assisted walkthrough cannot support a Product
or Pilot completion claim. `epic_complete` without a contained closure truth
audit is unverified legacy state or a contradiction for a new canonical
transition; a truth audit with partial criteria, unresolved counterevidence,
remaining gaps, contradictions, or a failed/non-representative black-box run is
`contradictory` and release-blocking.
Modern closure also requires a separate matching authority record and a digest
over every non-empty referenced evidence file. Changed referenced bytes,
partial state bindings, prose-only black-box assertions, or Portfolio terminal
claims without verified closure are contradictions. Historical unbound closure
is preserved and visibly classified as unverified rather than silently upgraded.

### Release readiness

Summarizes whether public claims are sufficiently supported:

- `PASS`: no errors, warnings, or contradictions with release impact
- `CONDITIONAL`: no release-blocking issue, but explicit warnings remain
- `FAIL`: a critical error, broken contract, or contradiction remains

Release readiness does not approve a release. It provides validator evidence for
the human release decision.

## Finding model

Every finding includes:

- validation tier
- report category: Error, Warning, or Contradiction
- affected artifact or cross-surface pair
- failed rule
- supporting evidence when available
- release impact
- recommended action

Recommendations are printed separately so the report distinguishes observed
facts from proposed remediation.

## Result compatibility

The existing runtime result classes remain:

- `healthy`
- `recoverable`
- `blocked`
- `contradictory`

Their meaning is strengthened:

- `healthy` requires all coherence-critical checks to pass
- `recoverable` maps to warnings and normally yields release `CONDITIONAL`
- `blocked` maps to errors and yields release `FAIL`
- `contradictory` means authoritative product or runtime evidence disagrees and
  yields release `FAIL`

The CLI exit codes remain compatible with the existing result classes.

## Required simulations

The validator generates representative default plans with all supported
adapters:

| Mode | Expected default evidence |
| --- | --- |
| Personal | `adapters`; selected repo adapters; no forced shared profile or embedded docs |
| Team | `adapters`; shared profile, ignore policy, and selected adapters; no embedded docs |
| Enterprise | `external`; zero repository actions and a home-scope AIM distribution |

The simulation validates actual planner output. Marker presence alone cannot
satisfy this tier.

## Adapter evidence

Native-support coherence requires:

- all 13 canonical command intents in Codex and Copilot surfaces
- native Claude command coverage
- explicit fallback behavior
- actionable `/aim upgrade` behavior
- no AIM 1.x state examples in AIM 2.0 adapter surfaces

## Publication evidence

Release readiness also verifies:

- reusable release workflow is independently runnable
- Pages depends on that release gate
- public canonical, Open Graph, robots, and sitemap origins agree
- schema `$id` values match assembled public paths
- the Pages artifact contains schemas and license metadata
- adapter closure and installer package tests participate in the release gate
- the packaged runtime closure helper rejects synthetic Product evidence,
  assisted black-box runs, partial acceptance mappings, unresolved
  counterevidence, remaining gaps, contradictions, stale state, and uncontained
  or changed referenced evidence

## Reporting contract

Text output must show, near the top:

- overall result
- release readiness
- all four validation tiers
- representative behavioral evidence

It must then separate:

- Errors
- Warnings
- Contradictions
- Recommendations

The validator remains read-only.

For clean CI checkouts, `--release` keeps all product and release-readiness
checks but makes the intentionally untracked local `.aim/` runtime workspace
optional. Normal mode continues to validate runtime resume integrity.

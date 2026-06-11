# AIM 2.0 Repo-Awareness Calibration

## Purpose

Define how AIM cheaply bootstraps, verifies, refines, persists, remembers, forgets, and reports repository knowledge.

`/aim calibrate-repo` and an AIM Epic whose outcome is to verify and refine repo-awareness use this same contract.

## Storage

Shared repository knowledge:

```text
aim.profile.yaml
```

Personal hints:

```text
~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
```

The shared profile is authoritative for team facts.
Personal hints may narrow local behavior but may not override shared ownership, risk, security, deployment, migration, or validation policy.

`.aim/` is runtime state only.
No stable profile, hint, remembered rule, or calibration result may be stored under `.aim/`.
`.aim/` may be read to resume or audit an active AIM loop, but it must not be
cited as durable repo-awareness. Runtime artifacts such as `.aim/reviews`,
`.aim/increments`, `.aim/decisions`, `.aim/archive`, and `.aim/logs` are trace
history, not maintained knowledge sources.

## Readiness

Calibration reports exactly one state:

- `ready`: required knowledge is verified and no blocking uncertainty remains
- `partially_ready`: useful knowledge exists, but one or more non-blocking uncertainties remain
- `needs_calibration`: no trustworthy reusable profile exists or required knowledge is missing

Installer bootstrap normally creates `needs_calibration` or `partially_ready`.
Only calibration may promote a profile to `ready`.

## Cheap-first flow

1. Read active runtime state only to avoid conflicting with an active AIM run.
2. Read `aim.profile.yaml` when present.
3. Apply compatible user-level hints when present.
4. Inspect the repository root and directly named primary areas.
5. Identify package/build metadata, likely technologies, test tooling, validation commands, and UI-test signals.
6. Read only short authoritative docs named by the profile.
7. Compare inferred facts with current files and commands.
8. Ask for confirmation when confidence is low or the fact affects trust, deployment, migration, security, or user-visible meaning.
9. Persist verified shared facts to `aim.profile.yaml`.
10. Persist personal preferences only to the user-level hints file.
11. Expand the scan only for conflicting evidence, unresolved risk, low confidence, or explicit user direction.

Calibration must propose a compact change summary before persisting trust-sensitive shared facts.

## Structured knowledge

The shared profile supports these categories:

- `technologies`
- `commands`
- `validation`
- `uiTesting`
- `docs`
- `localities`
- `riskZones`
- `habits`
- `avoidByDefault`
- `freshness`

Remembered rules must be entries in one of those categories.
Loose prose memory blobs are invalid.

Repo-awareness uses the two-layer model in `docs/workflow/repo-awareness-two-layer-model.md`.
Calibration stores atomic, compressed facts in the profile and moves procedural,
exception-heavy, or larger memory content into static docs such as
`docs/features/`, `docs/workflow/`, `docs/architecture/`, or another
repo-configured stable docs path.
The profile retains a short summary plus a structured load-on-demand pointer.

## Document loading states

Every remembered document rule uses one state:

- `authoritative`: commonly needed and trusted for its stated area
- `load_when_relevant`: load only for matching work, role, risk, or command
- `avoid_by_default`: do not load without an expansion reason
- `stale_or_uncertain`: verify before relying on it

## Confidence and evidence

Persisted facts use:

- `confidence`: `high`, `medium`, or `low`
- `source`: repository path, command output, installer bootstrap, or user confirmation
- `verified`: `true` or `false`

Low-confidence or unverified trust-sensitive facts keep the profile at `partially_ready` or `needs_calibration`.

## Remember and forget

Canonical intents:

```text
/aim remember-repo <category> "<rule>"
/aim forget-repo <category> "<rule-id>"
```

Natural language such as “Remember that we run rsync before every Gate E” or “Forget that old validation command” maps to the same operations.

Product-context example:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. User-facing language should be nuanced, calm, and empathetic toward both the cats and future owners."
```

Use remembered context for stable facts that should guide future AIM work, not
for temporary Epic state. Tone and product-positioning rules belong in
repo-awareness only when they are expected to stay true across multiple Epics.

Behavior:

1. resolve shared versus personal scope
2. map the request to a valid category
3. generate or locate a stable rule ID
4. show the proposed structured change
5. persist it to `aim.profile.yaml` or the user-level hints file
6. update freshness and calibration status
7. never write stable memory into `.aim/`

Before persistence, classify the rule:

- short atomic fact: update the profile
- procedure, policy, evidence contract, blockers, edge cases, debugging, product context, architecture notes, or larger memory: update a static memory document and its profile pointer

If scope is ambiguous, default to personal for preferences and ask before changing shared team policy.

## Human-visible summary

Calibration ends with:

```text
Repo-awareness: <ready | partially_ready | needs_calibration>
Technologies: <verified summary>
Commands: <verified summary>
Selected localities: <areas>
Docs by need: <authoritative/load-on-demand/avoided/stale summary>
Remembered rules: <rule IDs and short labels>
Open uncertainties: <items or none>
Next calibration action: <action or none>
```

## Installer relationship

The installer may create a schema-valid bootstrap profile from cheap evidence.
It must mark bootstrap provenance and must not claim `ready` without calibration evidence.

The installer and chat calibration share:

- the same profile schema
- the same readiness states
- the same confidence model
- the same structured categories
- the same target paths

## Failure rules

- conflicting shared profile and current evidence: current evidence wins temporarily; mark stale and recalibrate
- conflicting personal and shared facts: shared fact wins; report the personal hint conflict
- unknown memory category: reject and show valid categories
- `.aim/` profile or hint path: reject as a runtime-boundary violation
- durable repo-awareness reference to `.aim/reviews`, `.aim/increments`,
  `.aim/decisions`, `.aim/archive`, or other runtime artifacts: reject as a
  runtime-boundary violation
- trust-sensitive low-confidence inference: ask before persisting

## Related files

- `aim.profile.yaml`
- `docs/workflow/repo-awareness.md`
- `docs/workflow/personal-local-profile-storage.md`
- `install/aim-install-manifest.yaml`
- `scripts/validate_aim_runtime.py`

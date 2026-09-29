# AIM 2.0 Repo-Awareness Calibration

## Purpose

Define how AIM cheaply bootstraps, verifies, refines, persists, remembers, forgets, and reports repository knowledge.

`/aim calibrate-repo` and an AIM Epic whose outcome is to verify and refine repo-awareness use this same contract.

For a new empty project, calibration can be completed provisionally during
startup from the supplied requirements, goal, Epic or PRD. Do not block on an
interview about nonexistent code. Seed every role's bundled engineering skill,
label inferred capabilities and commands as unverified, and verify the affected
facts after the first implementation. Existing authorization still applies.
See [Engineering delivery](engineering-delivery.md) for skill inference and
source-bound freshness checks. Native agent files load current profiles rather
than copying their transient implementation status.

## Storage

Shared repository knowledge for Team or explicit repo opt-in:

```text
aim.profile.yaml
```

Enterprise external memory:

```text
~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml
~/.aim/repo-awareness/<repo-fingerprint>/docs/
```

Personal hints:

```text
~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
```

The shared profile is authoritative for team facts when repo sharing is
selected. Enterprise external memory is authoritative for Enterprise facts when
the default external footprint is selected.
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
2. Read Enterprise external memory when Enterprise external mode is active.
3. Read `aim.profile.yaml` when present.
4. Apply compatible user-level hints when present.
5. Inspect the repository root and directly named primary areas.
6. Identify package/build metadata, likely technologies, test tooling, validation commands, and UI-test signals.
7. Read only short authoritative docs named by the active memory/profile.
8. Compare inferred facts with current files and commands.
9. Verify uncertain facts against the relevant source. Keep unresolved facts provisional. Ask only when missing user intent or authority actually blocks the work; existing authorization applies to trust-sensitive facts too.
10. Persist verified shared facts to `aim.profile.yaml` for Team/repo opt-in or external memory for Enterprise external mode.
11. Persist personal preferences only to the user-level hints file.
12. Expand the scan only for conflicting evidence, unresolved risk, low confidence, or explicit user direction.

Calibration must propose a compact change summary before persisting trust-sensitive shared facts.

Reuse verified facts while their relevant sources and assumptions remain
unchanged. Recalibrate the affected command, locality, risk or document pointer
when evidence changes; a new Epic alone does not require a full rescan. Fix or
retire contradicted active facts rather than appending a competing snapshot.
Store the applicability and re-verification trigger with a reusable fact when
its scope would otherwise be ambiguous. A profile marked `ready` is not an
exemption from checking a source that has changed.

## Consumer checks and targeted locality refresh

After creating or updating a shared repo profile, run the shipped consumer:
`python3 <aim-package>/scripts/aim_engineering.py --repo <project> profiles --only repo`.
Use `--only roles` for standalone role configuration, or the default `profiles`
when both profiles are in scope. Missing unrelated profiles must not force a
second configuration workflow. Passing checks establish syntax, schema and
available role-skill bindings; they do not establish the truth of claims.

Use block YAML lists (one `- value` per line); the dependency-free reader does
not support nonempty inline flow lists. Localities can carry literal repository-relative `paths`, `tests`, and
`dependsOn` (other locality IDs). Record actual responsibility and relevant
caller/consumer boundaries in their short summaries. A directory label alone
is not a sufficient change plan. For the selected areas, run
`python3 <aim-package>/scripts/aim_engineering.py --repo <project> localities --locality <id>`;
repeat `--locality` for cross-boundary work. It inspects declared dependencies,
reports missing paths and unsafe references, and exposes shared/nested paths
as overlaps rather than declaring them ownership conflicts. Cycles are allowed.
No file contents or commands are executed by this metadata check. Legacy
prose references and globs need manual inspection or conversion to literal
pointers; the helper does not silently treat them as verified.

Inspect relevant imports/callers and behavior after the path check. Existing
paths, matching hashes and valid dependency IDs do not establish semantic
freshness. On moves/deletions, repair affected pointers and test links; on a
changed invariant, update or retire the claim and its discovery pointer. Keep
unrelated verified knowledge. The checker follows only selected dependency
closures, and returns a diagnostic instead of an unbounded scan on oversized
profiles. Reflection should update this stable discovery path, not create a
second active snapshot in proposals or runtime history.

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
5. persist it to `aim.profile.yaml`, Enterprise external memory, or the user-level hints file
6. update freshness and calibration status
7. never write stable memory into `.aim/`

Before persistence, classify the rule:

- short atomic fact: update the active profile or external memory index
- procedure, policy, evidence contract, blockers, edge cases, debugging, product context, architecture notes, or larger memory: update a static memory document and its profile or external memory pointer

In Enterprise external mode, the active durable store is
`~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml`, with larger memory under
`~/.aim/repo-awareness/<repo-fingerprint>/docs/`. Do not create
`aim.profile.yaml`, repo docs, symlinks, adapter files, or `.gitignore` entries
unless a broader repo-writing footprint or explicit organization policy is
selected.

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
- mode-specific target paths

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
- `docs/workflow/repo-profile-and-footprint-model.md`
- `install/aim-install-manifest.yaml`
- `scripts/validate_aim_runtime.py`

## Declare calibration coverage

When writing or refreshing calibration, record what was inspected. Optional
`calibration.scope` is `kind: repository` only for an actual repository-wide
assessment; scoped work uses `kind: localities` with a block-list `localityIds`
containing existing locality IDs. `ready` means ready within that declared scope.
Do not declare repository coverage from a successful check of one subsystem.
Legacy missing scope is unspecified, not implicitly repository-wide. Empty
bootstrap knowledge is not a completed calibration. The UI must show the scope;
a configured scoped profile can proceed with discussion/work without repeating
an irrelevant onboarding interview.

Use the packaged `profiles --only repo` consumer, which shares the product
contract as well as schema validation. For facts requiring measured reuse, see
`engineering-delivery.md` scoped knowledge consumption. Metadata validity, scope
and existing paths never certify the meaning of a claim.

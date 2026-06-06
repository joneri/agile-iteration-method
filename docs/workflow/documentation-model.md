# AIM 2.0 Documentation Model

## Purpose

Define the canonical documentation model and source-of-truth hierarchy for AIM 2.0.

This model makes `docs/workflow/` the central AIM-owned behavior documentation surface.

It separates:

- public product narrative
- AIM core truth
- mode and safety models
- workflow and onboarding docs
- repo-aware optional guidance
- user-created feature or workflow support
- maintainer reference
- runtime state
- shipped product surface

## Source-of-truth hierarchy

| Layer | Role | Source-of-truth status | Examples |
| --- | --- | --- | --- |
| Public product docs | explain what AIM is, why it exists, and how to begin | product narrative constrained by canonical behavior | `README.md`, `docs/product/` |
| AIM core truth | canonical method behavior | canonical | `docs/workflow/agile-iteration-method.md` |
| AIM behavior models | canonical AIM-owned behavior, install, mode, cost, context, classification, and documentation models | canonical for their model area | `docs/workflow/operating-modes.md`, `docs/workflow/repository-surface-classification.md`, `docs/workflow/cost-control-mode.md`, this document |
| Install and onboarding docs | user-facing application of canonical models | canonical for install/onboarding behavior | `docs/workflow/install-aim-2.0.md`, `docs/workflow/quick-start-aim-2.0.md`, `docs/workflow/troubleshoot-aim-2.0.md` |
| Validator and safety behavior | executable safety checks | canonical for what the validator enforces | `scripts/validate_aim_runtime.py` |
| Adapter docs and helpers | platform-specific entry and packaging behavior | adapter-specific, secondary to core | `docs/workflow/aim-adapter-guidance.md`, `adapters/`, `.github/agents/`, `.github/prompts/`, `.claude/` |
| Repo-aware policy | reusable target repository guidance | repo-owned, non-core | `aim.profile.yaml`, optional Personal profile |
| User-created support docs | repo-local feature or workflow notes | non-core by default | repo-created files under `docs/features/` or other local docs |
| Maintainer reference | AIM repo contribution and release support | maintainer-facing, non-core | `CONTRIBUTING.md`, `CHANGELOG.md`, `CONTRIBUTORS.md` |
| Runtime state | active work state and trace artifacts | runtime-owned, not documentation truth | `.aim/` |

## Canonical source-of-truth list

| Concern | Canonical source |
| --- | --- |
| AIM core behavior | `docs/workflow/agile-iteration-method.md` |
| Role order, gates, Done Increment discipline, escalation, ownership | `docs/workflow/agile-iteration-method.md` |
| Operating modes | `docs/workflow/operating-modes.md` |
| File-surface and installation boundary model | `docs/workflow/repository-surface-classification.md` |
| Documentation source-of-truth model | `docs/workflow/documentation-model.md` |
| Install behavior | `docs/workflow/install-aim-2.0.md`, constrained by the canonical mode and surface models |
| Runtime validation behavior | `scripts/validate_aim_runtime.py` |
| Repo profile and footprint behavior | `docs/workflow/repo-profile-and-footprint-model.md` |
| Repo-awareness calibration and persistent memory | `docs/workflow/repo-awareness-calibration.md` |
| Structured profile and repo operational-doc boundary | `docs/workflow/repo-awareness-two-layer-model.md` |
| Working-state boundaries | `docs/workflow/working-state-boundaries.md` |
| Personal profile storage | `docs/workflow/personal-local-profile-storage.md` |
| Profile-source reporting | `docs/workflow/profile-source-summary.md` |
| Team profile artifact | `docs/workflow/team-profile-artifact.md` |
| Codex skill onboarding | `docs/workflow/codex-skill-onboarding.md` |
| Front-door routing | `docs/workflow/light-front-door.md` |
| Adapter command intents and upgrade behavior | `docs/workflow/adapter-command-contract.md` |
| Validator tiers, coherence findings, and release readiness | `docs/workflow/product-coherence-validation.md` |
| Cost profile behavior | `docs/workflow/cost-control-mode.md` |
| Cost review behavior | `docs/workflow/cost-review-checklist.md` |
| Cost-saving and escalation behavior | `docs/workflow/cost-saving-method.md` |
| Modularity and context efficiency | `docs/workflow/modularity-context-efficiency.md` |

If two canonical AIM-owned docs conflict, treat the conflict as a documentation bug and escalate instead of guessing.
If public product docs conflict with canonical workflow docs, correct the public explanation; public narrative does not redefine AIM behavior.

## `docs/product/` role

`docs/product/` is the public-facing explanation and onboarding layer.

It is for:

- newcomers evaluating AIM
- users choosing an adoption mode or platform
- first-time installation and first-Epic journeys
- future GitHub Pages, tutorials, launch content, and demos

It should explain benefits, boundaries, and the user journey in plain language.
It must not become a second source of truth for gates, runtime state, installer safety, mode semantics, or adapter behavior.
Those rules remain canonical under `docs/workflow/`.

Public product docs should link deeper only when the reader needs operational or reference detail.

## Root-file rule

Generic root files are not AIM core truth.

| Surface | Status | Rule |
| --- | --- | --- |
| `AGENTS.md` | generic repository instruction file | outside AIM architecture; AIM does not require, create, modify, or load it as a control surface |
| `CLAUDE.md` | generic Claude repository instruction file | outside AIM architecture; Claude AIM entrypoints live under `.claude/` |
| `CONTRIBUTING.md` | AIM source-repository maintainer policy | source-repository-only; AIM must never copy, create, modify, require, or read it in a target repository |
| `aim.profile.yaml` | primary shared repo-awareness source | reusable repo intelligence, not runtime state or core truth |
| `.gitignore` | repo configuration | safety/support surface, not method truth |

AIM adapters may respect host-provided repository instructions as environment constraints, but AIM product behavior and repo-awareness must not depend on generic root files.

## `docs/workflow/` role

`docs/workflow/` is the central AIM-owned behavior documentation surface.

Behavior-defining AIM documents belong here when they define:

- AIM behavior
- install behavior
- mode behavior
- cost behavior
- context behavior
- classification behavior
- documentation truth

Moving a behavior-defining document into `docs/workflow/` is a promotion into canonical AIM product documentation, not a cosmetic rename.

## `docs/features/` role

`docs/features/` is a support/reference area by default.

It may contain three kinds of documents:

| Kind | Meaning | Canonical? | Shipping rule |
| --- | --- | --- | --- |
| Shipped advanced reference docs | explain background, examples, comparisons, or support material | reference, not canonical behavior | selectively shipped |
| Maintainer/build-memory docs | record why AIM evolved a certain way | non-core | maintainer/internal unless promoted |
| User-created or repo-local feature docs | support a target repo or project | non-core | local unless explicitly adopted into AIM product |

Do not place behavior-defining AIM docs in `docs/features/`.
If a support/reference doc starts defining AIM behavior, install behavior, mode behavior, cost behavior, context behavior, classification behavior, or documentation truth, promote it into `docs/workflow/`.

Current AIM-repo support/reference docs:

- `docs/features/aim-cost-comparison.md`: non-canonical reference comparison
- `docs/features/aim-github-copilot-cost-reduction-playbook.md`: vendor-specific onboarding playbook
- `docs/features/aim-vendor-cost-baseline-june-2026.md`: date-stamped vendor reference
- `docs/features/_template.md`: template for future non-canonical support/reference docs

## Runtime is not documentation truth

`.aim/` stores active AIM runtime state and trace artifacts.

It answers:

- which Epic is active
- which Done Increment is active
- which role owns the next step
- which gate was last passed
- which reviews and decisions belong to the active run

It does not define AIM core behavior, mode rules, install rules, or documentation truth.

Runtime artifacts may be useful evidence, but they are not product documentation.

## Product, repo-local, and internal docs

Shipped AIM product docs:

- public product narrative under `README.md` and `docs/product/`
- canonical core and behavior model docs under `docs/workflow/`
- install and onboarding docs
- selected support/reference docs
- adapter docs and packages selected for the footprint

Repo-local support docs:

- repo-specific feature explanations
- repo-specific workflow notes
- local assumptions and debugging notes
- private or team-specific profile guidance

Internal maintainer/build-memory docs:

- release planning notes
- historical analysis
- AIM build traces
- stale or exploratory feature docs not promoted into canonical product reference

## Cleanup-ready recommendations

| Surface | Recommendation |
| --- | --- |
| `README.md` | concise public product front door |
| `docs/product/` | public narrative and newcomer onboarding, constrained by canonical workflow docs |
| `docs/workflow/agile-iteration-method.md` | canonical AIM core truth |
| `docs/workflow/operating-modes.md` | canonical mode model |
| `docs/workflow/repository-surface-classification.md` | canonical file-surface/install-boundary model |
| `docs/workflow/documentation-model.md` | canonical documentation model |
| `docs/workflow/cost-control-mode.md` | canonical cost profile behavior |
| `docs/workflow/cost-review-checklist.md` | canonical cost review behavior |
| `docs/workflow/cost-saving-method.md` | canonical cost-saving and escalation behavior |
| `docs/workflow/modularity-context-efficiency.md` | canonical file-boundary and context-efficiency behavior |
| `docs/workflow/install-aim-2.0.md` | canonical install guidance constrained by model docs |
| `docs/features/` as a folder | support/reference by default; promote behavior-defining docs to `docs/workflow/` |
| `AGENTS.md` | outside AIM architecture; remove from AIM product surfaces |
| `CLAUDE.md` | outside AIM architecture; use optional `.claude/` packaging |
| `CONTRIBUTING.md` | keep only in the AIM source repository; explicitly exclude from every installer manifest and target package |
| `.aim/` | runtime state, never documentation truth |

## Validator behavior

The validator should:

- confirm the public product front door and required `docs/product/` journey exist
- confirm this documentation model exists
- check for required source-of-truth markers
- check that promoted behavior docs exist under `docs/workflow/`
- check that promoted behavior docs no longer exist under `docs/features/`
- report the canonical documentation model in validator output
- keep runtime checks separate from documentation truth checks

## Related files

- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/adapter-command-contract.md`
- `docs/workflow/product-coherence-validation.md`
- `docs/product/README.md`
- `docs/features/README.md`
- `docs/workflow/operating-modes.md`
- `docs/workflow/repository-surface-classification.md`
- `docs/workflow/cost-control-mode.md`
- `docs/workflow/modularity-context-efficiency.md`
- `docs/workflow/install-aim-2.0.md`
- `scripts/validate_aim_runtime.py`

## Change log

- 2026-06-05: Added canonical AIM 2.0 documentation model and source-of-truth hierarchy.
- 2026-06-05: Promoted behavior-defining AIM docs into `docs/workflow/` and made `docs/features/` support/reference by default.
- 2026-06-06: Added `docs/product/` as the public narrative and newcomer layer without changing canonical workflow authority.

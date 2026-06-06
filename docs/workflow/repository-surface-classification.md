# AIM 2.0 Repository Surface Classification

## Purpose

Define the operational file-surface boundary model for AIM 2.0.

This is canonical AIM file-surface and installation-boundary behavior.

The model lets maintainers and future installers answer, for each important file or folder:

- what is this?
- who owns it?
- is it static or repo-aware?
- is it runtime or reusable?
- is it local, shared, or shipped?
- may installation create it?
- may installation modify it?
- may installation overwrite it?
- must installation never touch it?

## How it works

AIM 2.0 separates repository surfaces by responsibility instead of treating every AIM-related file as installable product.

| Dimension | Values | Meaning |
| --- | --- | --- |
| Category | static product, repo-aware, repo-specific, runtime, build memory, tooling, metadata, examples | What kind of surface this is |
| Ownership | AIM-owned, repo-owned, mixed/layered, runtime-owned, generated | Who controls the source of truth |
| Awareness | static, repo-aware, repo-specific, local | Whether the file should vary by target repository |
| Lifecycle | runtime, reusable, reference, maintainer, generated | Whether the file is active state, reusable knowledge, or reference material |
| Distribution | shipped, optional ship, internal, local-only, generated | Whether the file belongs in the AIM product surface |
| Install safety | installer-safe, opt-in, collision-prone, never-touch | How an installer may treat the surface |

## Surface matrix

| Surface | Category | Ownership | Awareness | Lifecycle | Distribution | Install safety | Create | Modify | Overwrite | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | public release surface | AIM-owned | static | reference | shipped | installer-safe in AIM package only | yes for AIM package | yes in AIM repo | yes only inside AIM distribution | keep as product front door |
| `AGENTS.md` | generic repo instruction surface | repo-owned | repo-specific | external repository policy | not AIM product | never-touch | no | no | never | remove from AIM product; installer and AIM core ignore it |
| `CLAUDE.md` | generic Claude repo instruction surface | repo-owned | repo-specific | external repository policy | not AIM product | never-touch | no | no | never | remove from AIM product; use `.claude/` for optional AIM packaging |
| `CONTRIBUTING.md` | AIM source maintainer policy | AIM source-repo maintainers | source-repository-only | maintainer reference | never in target packages | excluded/never-touch | no | no | never | keep only in AIM source repo; exclude from all installer manifests and exports |
| `aim.profile.yaml` | Team AIM repo profile | repo-owned | repo-aware | reusable repo intelligence | shareable tiny Team profile | collision-prone | only by explicit Team AIM choice | merge/update with owner review | never blind overwrite | keep as this repo's Team profile and example |
| Personal hints `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml` | Personal AIM hints | local user-owned | repo-aware local | reusable local preferences | local-only | never-touch by repo installer | no | no | never | keep outside the repository |
| `.aim/` | AIM runtime workspace | runtime-owned | local | runtime/working state | local-only | never-touch as product | runtime may create on start | runtime may mutate active state | installer must never overwrite | keep ignored; never ship as product |
| `.github/agents/` | Copilot-native AIM agents | AIM-owned with repo impact | adapter-specific | reusable adapter policy | optional adapter package | opt-in with collision checks | yes if selected and absent | replace only AIM-owned files after diff review | never overwrite unrelated files | keep optional; installer must target known AIM files only |
| `.github/prompts/` | Copilot prompt helpers | AIM-owned optional helpers | repo-aware adapter layer | reusable prompts | optional ship | opt-in with collision checks | yes if Copilot prompts selected | update known AIM prompt files after review | never overwrite unrelated prompts | keep optional |
| `.claude/` | Claude helper commands/agents | AIM-owned optional helpers | repo-aware adapter layer | reusable prompts/commands | optional ship | opt-in with collision checks | yes if Claude helpers selected | update known AIM helper files after review | never overwrite unrelated Claude files | keep optional |
| `docs/workflow/` | canonical AIM behavior, workflow, runtime, adapter, install docs | AIM-owned | static with adapter notes | canonical/reference | shipped | installer-safe as docs package | yes for full embedded AIM | yes in AIM repo | yes only inside AIM-owned docs package | keep as central canonical AIM behavior surface |
| `docs/features/` | support/reference and repo-local feature docs | mixed/repo-owned by default | support/reference | support and maintainer memory | selective/reference only | opt-in/selective | yes only for support docs | yes in AIM repo | yes only for AIM-owned support docs | keep non-canonical by default; promote behavior docs to `docs/workflow/` |
| `adapters/` | adapter packages | AIM-owned | static adapter packaging | reusable tooling/docs | shipped by adapter selection | installer-safe inside adapter target | yes when selected | yes for AIM-owned adapter package | yes only inside adapter install target | keep as copyable adapter packages |
| `scripts/` | validation and support tooling | AIM-owned | static tooling | reusable tooling | shipped when validation selected | installer-safe with review | yes when selected | yes for AIM-owned scripts | yes only inside AIM-owned script path | keep validator; expose classification summary |
| `install/aim-install-manifest.yaml` | installer boundary manifest | AIM-owned | static | reusable installation contract | shipped | installer-safe | yes with installer package | yes in AIM source repo | yes only as AIM-owned manifest | keep canonical; explicitly exclude source-only and runtime surfaces |
| `examples/` | examples | AIM-owned | static examples | reference | optional ship | installer-safe optional | yes when examples selected | yes in AIM repo | yes only inside examples package | keep out of minimal install |
| `.gitignore` | target repo configuration | repo-owned | repo-specific | repository config | not AIM product | collision-prone | no by default | suggest fragment only | never blind overwrite | provide `/.aim` fragment, not whole-file install |
| `CHANGELOG.md` | release history | AIM-owned | static | maintainer/release reference | shipped for AIM repo | installer-safe in AIM package only | yes for AIM package | yes in AIM repo | yes only inside AIM distribution | keep current and avoid stale legacy claims |
| `CONTRIBUTORS.md` | project metadata | AIM-owned | static | metadata | shipped | installer-safe in AIM package only | yes for AIM package | yes in AIM repo | yes only inside AIM distribution | keep |
| `LICENSE` and `docs/LICENSE-DOCS` | license metadata | AIM-owned | static | metadata | shipped | installer-safe in AIM package only | yes for AIM package | yes in AIM repo | yes only inside AIM distribution | keep |
| `.DS_Store` | local OS artifact | local/generated | local | generated clutter | local-only | never-touch as product | no | no | never | ignore/remove from exports |

## Installer boundary rules

Use these rules for future installer work.

| Surface class | May create | May modify | May overwrite | Must never touch |
| --- | --- | --- | --- | --- |
| AIM-owned static product files | yes inside the selected AIM package | yes in AIM repo or selected package target | yes only when target path is known AIM-owned and user selected replacement | unrelated repo files |
| Generic root instruction files | no | no | never | always |
| Repo-specific configuration | only by explicit repo owner choice | only with owner review | never blindly | target repo policy files |
| Runtime/working state | runtime may create `.aim/` during AIM start | runtime may mutate active state | installer never overwrites | existing `.aim/state.json`, active Epic, reviews, decisions |
| Personal local profile | no repo installer action | no repo installer action | never | user-level profile storage |
| Team profile | only by explicit Team AIM choice | only with reviewed merge/update | never blindly | active working-state fields in profile |
| Adapter helpers | yes when the adapter is selected | yes for known AIM helper files after review | never over unrelated helper files | unrelated `.github/`, `.claude/`, or prompt content |
| Internal build memory | no by default | no by default | never | maintainer notes unless explicitly exporting them |

## Mode behavior

The canonical operating modes are defined in [AIM 2.0 operating modes](operating-modes.md).
Surface handling must follow that mode model.

| Surface | Personal | Team | Enterprise |
| --- | --- | --- | --- |
| `.aim/` | may stay local or be committed if the user wants | private by default; shared only by team choice | ignored by default; do not commit unless explicitly approved |
| `aim.profile.yaml` | optional | default tiny shared repo-awareness surface | create or modify only by explicit repo-owner approval |
| Personal profile storage | allowed and preferred for local reuse | allowed as local hint under Team baseline | allowed as private/local hint |
| `docs/features/` support/reference docs | may be kept or committed freely | shared when the team wants common support material | local/private by default unless explicitly approved |
| `AGENTS.md` and `CLAUDE.md` | outside AIM architecture | outside AIM architecture | outside AIM architecture |
| Generated markdown/process artifacts | may be kept or committed | commit only when the team wants audit/process history | ignored by default unless promoted to product docs |
| Product output | commit normally when part of the work | commit normally when part of the work | commit normally when part of the work |

## Collision rules

`AGENTS.md` and `CLAUDE.md` are first-class never-touch surfaces.

Rules:

- AIM installation must not create, modify, merge into, or overwrite either file
- AIM core, repo-awareness, and adapter startup must not require either file
- repository-owned content remains untouched
- optional adapter helpers live in AIM-owned `.github/`, `.claude/`, or adapter package paths

Other collision-prone root surfaces:

- `.gitignore`
- `aim.profile.yaml`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`

For `.gitignore`, installers should suggest the `/.aim` fragment instead of replacing the file.

## Local, shared, and shipped model

Local-only:

- `.aim/`
- Personal AIM hint storage under `~/.aim/repo-awareness/`
- adapter-local caches
- generated OS files such as `.DS_Store`

Shared team repo state:

- `aim.profile.yaml` when Team AIM is intentionally adopted
- repo-specific instruction files owned by the target repo
- reviewed adapter helper files when the team chooses them

Shipped AIM product:

- `README.md`
- `docs/workflow/`
- canonical behavior docs under `docs/workflow/`
- selected `docs/features/` support/reference docs
- `adapters/`
- selected `.github/agents/aim*.agent.md`
- optional `.github/prompts/`
- optional `.claude/`
- `scripts/validate_aim_runtime.py`
- `install/aim-install-manifest.yaml`
- examples when the install footprint includes examples

Internal build-memory:

- active `.aim/` artifacts
- historical analysis, reviews, and decisions
- support docs that record how AIM was built rather than stable user-facing behavior

## `CONTRIBUTING.md` role

`CONTRIBUTING.md` is a maintainer-facing policy only for the AIM source repository.

Installer rule:

- never copy, create, modify, require, or read a target repo's `CONTRIBUTING.md`
- explicitly exclude `CONTRIBUTING.md` from every installer manifest, package definition, and export boundary
- do not make exceptions for templates, forks, or full embedded footprints
- if product installation guidance grows inside `CONTRIBUTING.md`, split that guidance into `docs/workflow/` instead of making `CONTRIBUTING.md` an install payload

## Repo-aware profile rules

`aim.profile.yaml` is reusable repo intelligence, not runtime state.

Team AIM:

- may commit a tiny root `aim.profile.yaml`
- may include commands, locality, risk zones, ownership, freshness, and cost hints
- must not include active Epic, Done Increment, gate, role, review, or acceptance state

Personal AIM:

- may store reusable local hints at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- may create and commit `aim.profile.yaml`, adapter surfaces, docs, and runtime
  artifacts when the solo user chooses
- must never store stable repo-awareness under `.aim/`
- has no required repository footprint, but repository mutation is allowed

Runtime state:

- lives in `.aim/`
- is created and mutated by the AIM runtime
- must not be treated as product, profile, or installer payload

## Cleanup-ready recommendations

| Surface | Recommendation |
| --- | --- |
| `README.md` | keep as product front door |
| `AGENTS.md` | remove from AIM product surfaces; installer must never touch |
| `CLAUDE.md` | remove from AIM product surfaces; use optional `.claude/` package |
| `CONTRIBUTING.md` | keep only as AIM source-repo maintainer guidance; exclude from every target install |
| `aim.profile.yaml` | keep as Team profile example and shared repo intelligence |
| `.aim/` | keep ignored; never ship |
| `.github/agents/` | keep as optional Copilot-native package with collision checks |
| `.github/prompts/` | keep optional |
| `.claude/` | keep optional |
| `docs/workflow/` | keep as central canonical AIM behavior docs |
| `docs/features/` | keep as support/reference by default; promote behavior-defining docs to `docs/workflow/` |
| `adapters/` | keep as adapter package surface |
| `scripts/` | keep validator and make structural checks explicit |
| `examples/` | keep optional, not minimal install |
| `.gitignore` | do not install wholesale; suggest `/.aim` fragment |
| `.DS_Store` | ignore/remove from exports |

## Key decisions

- Repo-aware is not the same as static.
- Runtime is not product.
- `AGENTS.md` and `CLAUDE.md` are repo-owned generic files outside AIM architecture.
- `CONTRIBUTING.md` belongs only to the AIM source-repo maintainer surface and is forbidden from target installation.
- `aim.profile.yaml` is a Team profile surface, not working state.
- Installation safety takes priority over convenience.

## Debugging

The best check is whether the validator and this matrix agree about major surface classes:

```sh
python3 scripts/validate_aim_runtime.py .
```

What good looks like:

- `.aim/` reports as working state
- `aim.profile.yaml` reports as repo profile
- `AGENTS.md` and `CLAUDE.md` are absent from AIM product surfaces and treated as never-touch
- shipped docs and adapter helpers are separated from runtime artifacts

What bad looks like:

- an installer proposes to create, modify, merge into, or overwrite `AGENTS.md` or `CLAUDE.md`
- `.aim/` is included in shipped product files
- `aim.profile.yaml` contains active Epic or gate state
- `CONTRIBUTING.md` is present in any target-repo manifest, package, read set, or write set

## Related files

- `README.md`
- `CONTRIBUTING.md`
- `aim.profile.yaml`
- `.aim/`
- `.github/`
- `.claude/`
- `adapters/`
- `docs/workflow/`
- `docs/features/`
- `scripts/validate_aim_runtime.py`
- `examples/`
- `docs/workflow/documentation-model.md`

## Change log

- 2026-06-05: Initial repository surface classification model and major-surface inventory.
- 2026-06-05: Tightened AIM 2.0 cleanup rule so user-facing 1.x docs must be absorbed into AIM 2.0, retained only for a concrete short-term migration bridge, or deleted.
- 2026-06-05: Expanded the model into an operational installer-boundary matrix with ownership, lifecycle, distribution, collision, and overwrite rules.

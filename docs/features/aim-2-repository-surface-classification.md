# AIM 2.0 Repository Surface Classification

## Purpose

Define the operational file-surface boundary model for AIM 2.0.

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
| `AGENTS.md` | repo instruction surface | mixed/layered | repo-aware | reusable policy | optional template/reference | collision-prone | only if absent and explicitly requested | merge or append only with review | never blind overwrite | keep; install as merge target or template |
| `CLAUDE.md` | Claude bridge instruction surface | mixed/layered | repo-aware | adapter policy | optional adapter helper | collision-prone | only if absent and Claude support requested | merge only with review | never blind overwrite | keep; install as opt-in Claude bridge |
| `CONTRIBUTING.md` | maintainer contribution policy | repo-owned for target repos, AIM-owned in AIM repo | repo-specific | maintainer reference | shipped for AIM repo, not default install | collision-prone outside AIM repo | no by default | no by default | never in target repos | keep as AIM maintainer file; split later only if product install guidance grows |
| `aim.profile.yaml` | Team AIM repo profile | repo-owned | repo-aware | reusable repo intelligence | shareable tiny Team profile | collision-prone | only by explicit Team AIM choice | merge/update with owner review | never blind overwrite | keep as this repo's Team profile and example |
| Personal profile `~/.aim/profiles/<repo-fingerprint>/profile.yaml` | Personal AIM profile | local user-owned | repo-aware local | reusable local intelligence | local-only | never-touch by repo installer | no | no | never | document as preferred Personal AIM storage |
| `.aim/` | AIM runtime workspace | runtime-owned | local | runtime/working state | local-only | never-touch as product | runtime may create on start | runtime may mutate active state | installer must never overwrite | keep ignored; never ship as product |
| `.github/agents/` | AIM instruction layer and Copilot agents | AIM-owned with repo impact | repo-aware adapter layer | reusable adapter policy | shipped/optional adapter package | opt-in with collision checks | yes if selected and absent | replace only AIM-owned files after diff review | never overwrite unrelated files | keep; installer must target known AIM files only |
| `.github/prompts/` | Copilot prompt helpers | AIM-owned optional helpers | repo-aware adapter layer | reusable prompts | optional ship | opt-in with collision checks | yes if Copilot prompts selected | update known AIM prompt files after review | never overwrite unrelated prompts | keep optional |
| `.claude/` | Claude helper commands/agents | AIM-owned optional helpers | repo-aware adapter layer | reusable prompts/commands | optional ship | opt-in with collision checks | yes if Claude helpers selected | update known AIM helper files after review | never overwrite unrelated Claude files | keep optional |
| `docs/workflow/` | method, runtime, adapter, install docs | AIM-owned | static with adapter notes | reference | shipped | installer-safe as docs package | yes for full embedded AIM | yes in AIM repo | yes only inside AIM-owned docs package | keep as canonical docs surface |
| `docs/features/` | feature contracts and some build-memory docs | mixed | mixed static/build-memory | reusable contracts and maintainer memory | selected ship | opt-in/selective | yes for AIM repo/docs package | yes in AIM repo | yes only for AIM-owned docs | split shipped contracts from build memory later |
| `adapters/` | adapter packages | AIM-owned | static adapter packaging | reusable tooling/docs | shipped by adapter selection | installer-safe inside adapter target | yes when selected | yes for AIM-owned adapter package | yes only inside adapter install target | keep as copyable adapter packages |
| `scripts/` | validation and support tooling | AIM-owned | static tooling | reusable tooling | shipped when validation selected | installer-safe with review | yes when selected | yes for AIM-owned scripts | yes only inside AIM-owned script path | keep validator; expose classification summary |
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
| Repo-aware instruction files | only if absent and explicitly selected | only through merge, append, or generated patch with review | never blindly | existing repo-owned instructions |
| Repo-specific configuration | only by explicit repo owner choice | only with owner review | never blindly | target repo policy files |
| Runtime/working state | runtime may create `.aim/` during AIM start | runtime may mutate active state | installer never overwrites | existing `.aim/state.json`, active Epic, reviews, decisions |
| Personal local profile | no repo installer action | no repo installer action | never | user-level profile storage |
| Team profile | only by explicit Team AIM choice | only with reviewed merge/update | never blindly | active working-state fields in profile |
| Adapter helpers | yes when the adapter is selected | yes for known AIM helper files after review | never over unrelated helper files | unrelated `.github/`, `.claude/`, or prompt content |
| Internal build memory | no by default | no by default | never | maintainer notes unless explicitly exporting them |

## Collision rules

`AGENTS.md` and `CLAUDE.md` are first-class collision surfaces.

Rules:

- an installer must inspect whether the target file exists before proposing changes
- if the target file exists, installation must produce a merge plan, patch, or side-by-side template
- blind overwrite is forbidden
- repo-specific rules in an existing file remain authoritative unless the repo owner approves a change
- AIM core may be referenced from these files, but these files must not become hidden runtime state
- adapter helpers may explain AIM behavior but must not redefine role order, gate meaning, ownership, or escalation

Other collision-prone root surfaces:

- `.gitignore`
- `aim.profile.yaml`
- `CONTRIBUTING.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`

For `.gitignore`, installers should suggest the `/.aim` fragment instead of replacing the file.

## Local, shared, and shipped model

Local-only:

- `.aim/`
- Personal AIM profile storage under `~/.aim/profiles/`
- adapter-local caches
- generated OS files such as `.DS_Store`

Shared team repo state:

- `aim.profile.yaml` when Team AIM is intentionally adopted
- repo-specific instruction files owned by the target repo
- reviewed adapter helper files when the team chooses them

Shipped AIM product:

- `README.md`
- `docs/workflow/`
- selected current `docs/features/` contracts
- `adapters/`
- selected `.github/agents/aim*.agent.md`
- optional `.github/prompts/`
- optional `.claude/`
- `scripts/validate_aim_runtime.py`
- examples when the install footprint includes examples

Internal build-memory:

- active `.aim/` artifacts
- historical analysis, reviews, and decisions
- feature docs that record how AIM was built rather than stable user-facing behavior

## `CONTRIBUTING.md` role

`CONTRIBUTING.md` is a maintainer-facing policy for the AIM repository.

It is not a default shipped install surface for target repositories because most target repos already own their contribution process.

Installer rule:

- do not create, modify, or overwrite a target repo's `CONTRIBUTING.md` by default
- link to AIM contribution guidance only when installing AIM into an AIM-related template or maintained fork
- if product installation guidance grows inside `CONTRIBUTING.md`, split that guidance into `docs/workflow/` instead of making `CONTRIBUTING.md` an install payload

## Repo-aware profile rules

`aim.profile.yaml` is reusable repo intelligence, not runtime state.

Team AIM:

- may commit a tiny root `aim.profile.yaml`
- may include commands, locality, risk zones, ownership, freshness, and cost hints
- must not include active Epic, Done Increment, gate, role, review, or acceptance state

Personal AIM:

- should store reusable local profile facts at `~/.aim/profiles/<repo-fingerprint>/profile.yaml`
- may use ignored `.aim/profile.yaml` only as an adapter fallback
- must not require repository mutation

Runtime state:

- lives in `.aim/`
- is created and mutated by the AIM runtime
- must not be treated as product, profile, or installer payload

## Cleanup-ready recommendations

| Surface | Recommendation |
| --- | --- |
| `README.md` | keep as product front door |
| `AGENTS.md` | keep as repo-aware contract; install only by merge/template |
| `CLAUDE.md` | keep as opt-in Claude bridge; install only by merge/template |
| `CONTRIBUTING.md` | keep as AIM maintainer file; never default-install into target repos |
| `aim.profile.yaml` | keep as Team profile example and shared repo intelligence |
| `.aim/` | keep ignored; never ship |
| `.github/agents/` | keep as AIM instruction layer and Copilot package with collision checks |
| `.github/prompts/` | keep optional |
| `.claude/` | keep optional |
| `docs/workflow/` | keep as shipped reference docs |
| `docs/features/` | split shipped contracts from internal build-memory later |
| `adapters/` | keep as adapter package surface |
| `scripts/` | keep validator and make structural checks explicit |
| `examples/` | keep optional, not minimal install |
| `.gitignore` | do not install wholesale; suggest `/.aim` fragment |
| `.DS_Store` | ignore/remove from exports |

## Key decisions

- Repo-aware is not the same as static.
- Runtime is not product.
- `AGENTS.md` and `CLAUDE.md` are collision-prone instruction surfaces, not safe overwrite targets.
- `CONTRIBUTING.md` belongs to the AIM repo maintainer surface, not target repo installation.
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
- `AGENTS.md` and `CLAUDE.md` are treated as collision-prone
- shipped docs and adapter helpers are separated from runtime artifacts

What bad looks like:

- an installer proposes to overwrite `AGENTS.md` or `CLAUDE.md`
- `.aim/` is included in shipped product files
- `aim.profile.yaml` contains active Epic or gate state
- `CONTRIBUTING.md` is treated as a default target-repo payload

## Related files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
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

## Change log

- 2026-06-05: Initial repository surface classification model and major-surface inventory.
- 2026-06-05: Tightened AIM 2.0 cleanup rule so user-facing 1.x docs must be absorbed into AIM 2.0, retained only for a concrete short-term migration bridge, or deleted.
- 2026-06-05: Expanded the model into an operational installer-boundary matrix with ownership, lifecycle, distribution, collision, and overwrite rules.

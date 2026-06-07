> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 2.0

## Guided installer

Run:

```bash
python3 scripts/aim_install.py
```

In a terminal, the installer asks only for required information that was not supplied by flags:

- target repository supports filesystem Tab completion
- mode uses Up/Down and Enter, with Personal highlighted by default
- footprint uses Up/Down and Enter, with the selected mode's suggested
  footprint highlighted
- adapters use Up/Down, Space to toggle, and Enter to confirm

Flags such as `--target`, `--mode`, `--footprint`, and `--adapter` are used directly and are not asked again.

The default text view is compact: it shows the target, selected mode, footprint and adapters, action counts, blockers, and files that need a decision.
Use `--verbose` (or `--raw`) for the complete file-by-file plan and `--format json` for machine-readable output.
JSON and `--non-interactive` runs never prompt.

The compact preview and reviewed apply are one guided session.
After preview and any collision decisions, the final confirmation can apply immediately without restarting with `--apply`.
Declining leaves the target unchanged.

For an explicit preview-only guided run, use:

```bash
python3 scripts/aim_install.py --dry-run
```

In an interactive terminal, each collision uses:

- `y`: overwrite this file
- `n`: keep the existing file
- `a`: overwrite this file and all remaining AIM-owned collisions
- `q`: quit before applying

Enter defaults to `n`.
After all collision decisions, the guided flow asks `Apply this plan now? [y/N]`.
No files are written unless the user answers `y`.

The prompt flow is a concise sequential terminal interaction.
It keeps the active question visually clear by avoiding the old raw plan dump, but it is not a sticky prompt fixed to the bottom of the terminal.
For automation, unresolved collisions fail; `--force` remains the explicit non-interactive overwrite mechanism.
Color is automatic on supported terminals and can be controlled with `--color always|never`.

Use this guide when repository setup is still missing and you want a current AIM 2.0 installation path.

This guide is about repository setup.
Use [Quick start AIM 2.0](quick-start-aim-2.0.md) for the first run after setup.

## Choose the operating mode

- Personal AIM:
  - freedom mode for one developer
  - repo mutation and committed AIM files are allowed
  - docs, repo-awareness, profiles, adapters, and runtime state may live locally
    or in the repo as the user chooses
- Team AIM:
  - shared AIM understanding by agreement
  - share a small root `aim.profile.yaml` or approved shared profile pointer
  - share selected features/docs when the team wants common behavior
  - private runtime state may still stay local
- Enterprise AIM:
  - safe and isolated by default
  - share product output, not AIM internals
  - keep AIM runtime and generated process artifacts ignored unless explicitly approved
  - do not assume the repo root is empty or instruction files can be overwritten

These are the canonical AIM 2.0 operating modes.
Full embedded AIM remains a footprint choice when the repo owner intentionally wants AIM product docs and adapter helpers in the repository.

For the canonical mode model, see [AIM 2.0 operating modes](operating-modes.md).

## Choose the installation footprint

Mode and footprint are separate:

- mode defines who is using AIM and the default sharing/safety posture
- footprint defines which files are installed

Available footprints:

| Footprint | Repository effect |
| --- | --- |
| `local` | no target-repository mutation; home-scope packages such as Codex may be installed |
| `profile` | repo profile and runtime ignore policy, without repo adapters or embedded docs |
| `adapters` | selected adapter surfaces plus their required canonical contract subset; Team also receives the shared profile |
| `full` | selected adapters, repo profile, runtime ignore, and embedded workflow docs |

Suggested defaults:

- Personal: `adapters`, as a useful solo setup; all four footprints remain
  unrestricted user choices
- Team: `adapters`, with intentional shared repo-awareness
- Enterprise: `local`; every repo-writing footprint is an explicit override

Selecting Personal never applies Team review ownership or Enterprise isolation
rules. Selecting Enterprise never broadens repository mutation silently.

### Adapter package closure

The `adapters` footprint is smaller than `full`, but it is not an incomplete
adapter-only copy:

- Codex receives required contracts inside its home-scoped skill package under
  `references/`; this does not mutate the target repository.
- Claude and Copilot receive only the canonical workflow documents directly
  required by their installed instructions.
- `full` remains the only footprint that embeds the complete canonical workflow
  library, schemas, and distribution license metadata.

Required adapter references are release-blocking. Optional links inside copied
canonical documents remain further reading and do not expand the closure payload
recursively.

The full footprint includes `docs/aim/LICENSE` and
`docs/aim/LICENSE-DOCS` so copied AIM documentation retains its attribution and
CC BY 4.0 context without colliding with the target repository's root license.

## Installation boundary model

Before copying files, classify the target surface.

Use [AIM 2.0 repository surface classification](repository-surface-classification.md) as the operational boundary model.

Installer actions must follow these defaults:

| Surface class | Default action |
| --- | --- |
| Static AIM product docs and adapter packages | may be copied into an AIM-owned package path selected by the user |
| Shared repo-awareness | Team and Enterprise require deliberate shared choice; Personal may create or update it by solo choice |
| Runtime state | never install as product; AIM creates `.aim/` at runtime |
| Team profile | create or update only by explicit Team AIM choice |
| Personal profile | local hints are available, but a repo profile is also allowed by user choice |
| Generic root files | never create, modify, or overwrite for AIM |
| Internal build-memory | do not install by default |

Mode-specific defaults:

| Mode | Installer default |
| --- | --- |
| Personal | suggest a practical adapter setup while allowing local, profile, adapters, or full without Team/Enterprise restrictions |
| Team | create or update shared repo-awareness only through small reviewed surfaces such as `aim.profile.yaml` |
| Enterprise | verify ignore safety before creating repo-local AIM internals; require explicit approval for any shared AIM surface |

Enterprise safety and collision protection matter more than convenience.
Personal remains permissive; choosing a repo-writing footprint is itself the
solo user's reviewed choice.
Generic root files may still exist for repository purposes, but AIM installation ignores them.

### Root-file independence

These generic root files are outside the AIM architecture:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`

An AIM installer must not create, modify, merge into, or overwrite them.
Repository-owned content in those files remains untouched and is not needed for AIM core, repo-awareness, or adapter startup.

`CONTRIBUTING.md` is a source-repository-only maintainer file.
In a target repository, AIM must never copy, create, modify, require, or read it.
Every installer manifest, package definition, and export boundary must explicitly exclude `CONTRIBUTING.md`.
The canonical machine-readable boundary is `install/aim-install-manifest.yaml`.

These repo-owned configuration surfaces still require collision handling:

- `aim.profile.yaml`
- `.gitignore`

Rules:

- inspect before writing
- create only when absent and explicitly requested
- modify only through a reviewed merge or patch
- never blind overwrite
- never store active Epic, gate, role, review, or acceptance state in repo profiles or instruction files

For `.gitignore`, suggest this fragment instead of replacing the target file:

```gitignore
/.aim
/.aim-local
/aim.local.*
/*.aim.local.md
/*.aim.process.md
```

## Minimum setup for full embedded AIM

Required in the repository:

- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-awareness.md`
- `aim.profile.yaml` when shared repo-awareness is wanted
- `.aim/` created automatically when AIM starts if missing

Important:

- full embedded is a footprint choice, not a separate operating mode
- adapter packages are selected independently and remain secondary to canonical workflow docs
- `.aim/` is runtime state, not an install payload
- `CONTRIBUTING.md` is excluded from every target-repository installation footprint

Optional Copilot prompt helpers:

- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim.prompt.md`

Optional Claude Code package:

- `.claude/agents/aim.md`
- the complete native AIM command family under `.claude/commands/`, as defined
  by [AIM 2.0 adapter command contract](adapter-command-contract.md)
- `.claude/commands/install-aim.md` as the additional install/onboarding helper

## Updating an existing AIM install

Use this path when AIM is already present in the repository, but AIM 2.0 instruction files, helper prompts, or adapter packages changed and the repository should start following the newer behavior.

Recommended flow:

1. Run the installer again:

```bash
python3 scripts/aim_install.py
```

2. Refresh repo-awareness:

```text
/aim calibrate-repo
```

3. Start a fresh adapter session when the active platform uses installed helper files, such as:
  - Copilot agents or prompt helpers
  - Claude command files
  - Codex local skill packaging

4. If an Epic was already active, resume it with:

```text
/aim continue
```

Use `/aim upgrade` as the normal user-facing command for this flow when the active adapter supports packaged AIM command entrypoints.

Important:

- upgrade refreshes installed AIM surfaces
- calibration refreshes repo-awareness
- active `.aim/` runtime state is not silently replaced by upgrade

## Adapter packaging

### Codex

Use the shipped skill when you want the `/aim` command surface and Codex bootstrap help.

Required for `/aim` in Codex:

- `adapters/codex/agile-iteration-method/SKILL.md`

If the local skill is missing or stale, install the repo-bundled skill before relying on `/aim` command routing:

```sh
python3 scripts/aim_install.py --target . --mode personal \
  --footprint local --adapter codex --dry-run
```

Review the plan, then rerun with `--apply`. The installer includes package
metadata and required canonical contracts under `references/`; copying the
source adapter directory alone does not produce a closed package.

### Copilot

1. Install the selected `.github/agents/aim*.agent.md` files as the native Copilot entrypoint package.
2. Add `.github/prompts/` when you want packaged Copilot prompt entrypoints.
3. Start with `/aim start "EPIC: ..."` or `Start working according to AIM`.

### Claude Code

1. Ensure canonical AIM workflow docs are available from the selected product footprint.
2. Install the selected `.claude/agents/` and `.claude/commands/` files.
3. Start with the shipped Claude starter command or the explicit `EPIC: <desired outcome>` fallback.

No adapter requires a generic root instruction file.

## Repo-awareness bootstrap

Installation and calibration are two stages of one model.

The installer may:

- create a schema-valid `aim.profile.yaml` from cheap, obvious repository evidence
- declare `needs_calibration` when required knowledge is absent
- declare `partially_ready` when useful facts exist with unresolved uncertainty
- point Personal hints to `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`

The installer must not claim `ready`.
Run `/aim calibrate-repo`, or start an AIM Epic to verify and refine repo-awareness, to confirm facts and promote readiness.

After installation, report:

- repo-awareness readiness
- bootstrap evidence used
- unresolved uncertainties
- the `/aim calibrate-repo` next action when readiness is not `ready`

## First-run checks

After setup, a user should be able to:

- start AIM
- resume AIM
- inspect status with `/aim status`
- inspect config with `/aim config`
- validate runtime state with `/aim validate`
- read help with `/aim help`
- select runtime depth with `/aim cost standard|control|deep`
- calibrate repository knowledge with `/aim calibrate-repo`
- remember and forget structured repository rules

## If setup is incomplete

- if the user starts AIM in recognizable language, treat it as a start intent
- if a helper prompt is missing, explain the equivalent manual command
- if `.aim` is missing, create it before continuing
- if repo policy is contradictory, stop and escalate instead of guessing

## Next documents

- [Quick start AIM 2.0](quick-start-aim-2.0.md)
- [Troubleshoot AIM 2.0](troubleshoot-aim-2.0.md)
- [AIM 2.0 low-footprint adoption](aim-2-low-footprint-adoption.md)
- [AIM adapter guidance](aim-adapter-guidance.md)

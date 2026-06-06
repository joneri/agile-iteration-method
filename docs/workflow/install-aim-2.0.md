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
- adapters use Up/Down, Space to toggle, and Enter to confirm

Flags such as `--target`, `--mode`, and `--adapter` are used directly and are not asked again.

The default text view is compact: it shows the target, selected mode and adapters, action counts, blockers, and files that need a decision.
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
  - flexible and permissive
  - no committed AIM files are required by default, but the user may commit AIM files if they want
  - repo-awareness may live locally or in the repo
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

## Installation boundary model

Before copying files, classify the target surface.

Use [AIM 2.0 repository surface classification](repository-surface-classification.md) as the operational boundary model.

Installer actions must follow these defaults:

| Surface class | Default action |
| --- | --- |
| Static AIM product docs and adapter packages | may be copied into an AIM-owned package path selected by the user |
| Shared repo-awareness | create or update root `aim.profile.yaml` only by explicit Team or Enterprise choice |
| Runtime state | never install as product; AIM creates `.aim/` at runtime |
| Team profile | create or update only by explicit Team AIM choice |
| Personal profile | store outside the repository by default |
| Generic root files | never create, modify, or overwrite for AIM |
| Internal build-memory | do not install by default |

Mode-specific defaults:

| Mode | Installer default |
| --- | --- |
| Personal | offer local-only setup first; allow repo mutation when the user chooses it |
| Team | create or update shared repo-awareness only through small reviewed surfaces such as `aim.profile.yaml` |
| Enterprise | verify ignore safety before creating repo-local AIM internals; require explicit approval for any shared AIM surface |

Installation safety matters more than convenience.
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

Optional Claude Code package:

- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`

## Adapter packaging

### Codex

Use the shipped skill when you want the `/aim` command surface and Codex bootstrap help.

Required for `/aim` in Codex:

- `adapters/codex/agile-iteration-method/SKILL.md`

If the local skill is missing or stale, install the repo-bundled skill before relying on `/aim` command routing:

```sh
mkdir -p ~/.codex/skills/agile-iteration-method
cp -R adapters/codex/agile-iteration-method/. ~/.codex/skills/agile-iteration-method/
```

Copy the whole directory, not just `SKILL.md`.

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

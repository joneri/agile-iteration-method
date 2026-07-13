# Agile Iteration Method (AIM) 2.2

![AIM 2.2 - Agile Iteration Method](github-pages/assets/images/aim-2-hero-dark.png)

AIM is a delivery method for AI-assisted software work. You describe the
outcome. AIM plans one useful increment, builds it, reviews it, validates it,
and asks for the decisions that still belong to you.

It works with Codex, Claude Code, and GitHub Copilot.

## Install

```bash
curl -fsSL https://joneri.github.io/agile-iteration-method/install.sh | bash
```

The installer asks for a repository and the adapters you use. It shows every
write and collision before applying anything.

Already using AIM? Run:

```text
/aim upgrade
```

## Start

First verify the repository knowledge AIM will reuse:

```text
/aim calibrate-repo
```

Record a durable project rule when AIM should remember it on later runs:

```text
/aim remember-repo habits "Keep user-facing language direct and calm."
```

Then start with an outcome, not a task list:

```text
/aim start "EPIC: Make checkout recovery clear and reliable when payment confirmation is delayed"
```

Use `/aim help` when you want the next useful action. The same command family
also covers continue, status, validation, configuration, upgrade, memory,
execution mode, cost depth, and replanning.

## How AIM works

```text
PO -> TDO -> Dev -> Reviewer -> TDO -> PO
```

- **PO** owns the outcome and acceptance.
- **TDO** chooses the next end-to-end Done Increment and validates delivery.
- **Dev** implements the approved increment.
- **Reviewer** looks for correctness problems, regressions, and risk.

Gate A approves the Epic. Gate B approves the next increment. Gate E accepts
the result. Review and technical validation happen before acceptance.

`Strict` pauses at every hard gate. `Auto` continues while the approved
direction remains clear, but still stops for risk, scope changes, and final Epic
acceptance.

## Repository-aware, not repository-heavy

AIM keeps four things separate:

| Surface | Purpose |
| --- | --- |
| `docs/workflow/agile-iteration-method.md` | canonical AIM method |
| `aim.profile.yaml` | reusable repository knowledge |
| `aim.roles.yaml` | project-specific PO, TDO, Dev, and Reviewer expertise |
| `.aim/` | active local runtime state and review evidence |

The standard installation adds the selected supplier skills and native project
specialists. It never needs to create `AGENTS.md` or `CLAUDE.md`.

## Native adapters

| Platform | AIM skill | Project specialists |
| --- | --- | --- |
| Codex | `~/.agents/skills/agile-iteration-method/` | `.codex/agents/aim-*.toml` |
| Claude Code | `.claude/skills/aim/` | `.claude/agents/aim-*.md` |
| GitHub Copilot | `.github/skills/aim/` | `.github/agents/aim-*.agent.md` |

All adapters use the same AIM roles, gates, state ownership, and `/aim` command
semantics. Supplier-specific files define how each project specialist works.

## What is new in v2.2.0

- one adaptive installation instead of Personal, Team, and Enterprise editions
- project-specific native role specialists generated from `aim.roles.yaml`
- supplier-native skills for the full `/aim` command family
- adapter readiness receipts after install and upgrade
- current Codex skill discovery through `$HOME/.agents/skills`
- shorter product documentation and stronger release/documentation checks

The AIM runtime contract remains 2.0. Product release, runtime contract,
installer manifest, and profile schema versions are tracked separately.

## Safety

- one main AIM thread owns `.aim/state.json` and gate transitions
- native specialists never accept work or create parallel AIM runtimes
- existing files are collision-protected
- apply is rollback-protected and idempotent
- unavailable native delegation falls back to the same sequential role loop
- tags, releases, deploys, and other external changes still need explicit scope

## Documentation

- [Feature guide](docs/product/features.md)
- [First-time journey](docs/product/getting-started.md)
- [Platforms and project specialists](docs/product/platforms-and-adoption.md)
- [Install and upgrade](docs/workflow/install-aim-2.0.md)
- [Canonical AIM method](docs/workflow/agile-iteration-method.md)
- [Troubleshooting](docs/workflow/troubleshoot-aim-2.0.md)
- [Release and publication](docs/workflow/release-publication-model.md)

Current product release: **v2.2.0**. See [CHANGELOG.md](CHANGELOG.md).

Documentation is licensed under [CC BY 4.0](LICENSE).

# Agile Iteration Method (AIM) 3.2

![AIM 3.2.0 - Agile Iteration Method](github-pages/assets/images/aim-2-hero-dark.png)

AIM is a delivery method for AI-assisted software work. You describe the outcome. AIM plans one useful increment, builds it, reviews it, validates it, and asks for the decisions that still belong to you. **Same model. Stronger software:** in our Enigma pair, GPT-6 Luna (high) with AIM 3.2 scored **93.5/100 versus 49.8/100** with the same PRD and predefined KPI weights. [See the case and public evidence](docs/features/aim-3.2-enigma-case.md).

Switch between Codex, Claude Code, and GitHub Copilot while keeping your project knowledge and saved AIM work. Discuss ideas with your repository before starting implementation. Each tool needs AIM and access to the same current repository and saved state.

## Install

Install the complete, self-contained AIM Agent Skill through the open skills ecosystem:

[![skills.sh](https://skills.sh/b/joneri/agile-iteration-method)](https://skills.sh/joneri/agile-iteration-method)

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method
```

This is full AIM, not AIM Lite. The package is generated from the same canonical workflow, adapter, installer, and schema sources as the adaptive AIM distribution. It does not require a separate AIM npm publication.

Target one supported agent explicitly when needed:

```bash
# Codex
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent codex --yes

# GitHub Copilot
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent github-copilot --yes

# Claude Code
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method --agent claude-code --yes
```

Update an installed public skill with:

```bash
npx skills update agile-iteration-method --yes
```

The adaptive AIM installer remains available when you want reviewed repository calibration, native project specialists, or a broader supplier-specific footprint. Clone the public source so you can inspect exactly what will run:

```bash
git clone --depth 1 https://github.com/joneri/agile-iteration-method.git aim-source
cd aim-source
python3 scripts/aim_install.py --dry-run
```

Review the source and preview, then rerun with `--apply` only when the plan is correct. The installer asks for a repository and the adapters you use. Native project specialists can also be refreshed later through `/aim configure-agents` from `aim.roles.yaml`.

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

Turn completed AIM work into reviewable knowledge candidates:

```text
/aim reflect
/aim reflect-all
```

Reflect verifies historical lessons against current repository evidence, preserves provenance and contradictions, and keeps promotion under your control. It finishes by saying whether action is recommended and gives one concrete next step—or states that nothing needs to be remembered or forgotten. `reflect-all` previews its local project inventory before analyzing the selected set and never modifies discovered repositories.

Then start with an outcome, not a task list:

```text
/aim start "EPIC: Make checkout recovery clear and reliable when payment confirmation is delayed"
```

Use `/aim help` when you want the next useful action. The same command family also covers continue, status, validation, configuration, upgrade, memory, execution mode, cost depth, and replanning.

## From product direction to a moving Portfolio

After calibration, launch `/aim ui` from the authoritative Codex task. The Control room displays its exact AIM launch release and shows whether Connected Codex control or View-only mode is active. Then follow one visible route:
```text
/aim calibrate-repo -> /aim ui -> /aim discuss [question]
-> /aim to-backlog -> review Roadmap -> /aim start "PORTFOLIO" mode:auto
-> approve one bounded mandate -> monitor the run—or step away
```

Discuss uses relevant durable repository knowledge and delivery evidence but does not create work. `/aim to-backlog` is the explicit promotion into planned Roadmap candidates. After mandate approval, AIM runs every included Epic through its complete role loop and returns control when the approved boundary no longer covers the next decision.

## How AIM works

```text
PO -> TDO -> Dev -> Reviewer -> TDO -> PO
```

- **PO** owns the outcome and acceptance.
- **TDO** chooses the next end-to-end Done Increment and validates delivery.
- **Dev** implements the approved increment.
- **Reviewer** looks for correctness problems, regressions, and risk.

Gate A approves the Epic. Gate B approves the next increment. Gate E accepts the result. Review and technical validation happen before acceptance.

`Strict` asks for direction and first-plan approval together, then delivery acceptance with a prepared Epic disposition. `Auto` continues while the approved direction remains clear, but still stops for risk, scope changes, and final Epic acceptance.

## Repository-aware, not repository-heavy

AIM keeps four things separate:

| Surface | Purpose |
| --- | --- |
| `docs/workflow/agile-iteration-method.md` | canonical AIM method |
| `aim.profile.yaml` | reusable repository knowledge |
| `aim.roles.yaml` | project-specific PO, TDO, Dev, and Reviewer expertise |
| `.aim/` | active local runtime state and review evidence |

The standard installation adds the selected supplier skills and native project specialists. It never needs to create `AGENTS.md` or `CLAUDE.md`.

## Native adapters

| Platform | AIM skill | Project specialists |
| --- | --- | --- |
| Codex | `~/.agents/skills/agile-iteration-method/` | `.codex/agents/aim-*.toml` |
| Claude Code | `.claude/skills/aim/` | `.claude/agents/aim-*.md` |
| GitHub Copilot | `.github/skills/aim/` | `.github/agents/aim-*.agent.md` |

All adapters use the same AIM roles, gates, state ownership, and `/aim` command semantics. Supplier-specific files define how each project specialist works.

## Smarter output from the start

AIM applies **audience-context integrity** to everything it generates: write the intended current meaning for the reader, and keep private conversations, rejected drafts, prompts, AI mistakes, and review feedback out of product copy, UI, code comments, and documentation. Changelogs and other intentionally historical artifacts keep the history their audience actually needs.

## What is new in v3.2.0

**Fewer approvals. Clearer next steps. AIM 3.2 brings the decisions together so you can focus on the work.** In a straightforward Strict Epic with one Increment, approve the direction and plan together, then accept the verified delivery and Epic closure together.

- **One clear start:** see the Epic goal, first Increment, remaining work and risks before approving both direction and plan.
- **One clear finish:** accept the Increment and a verified Epic closure together, or accept only the Increment and keep the Epic open.
- **AIM finds the next step:** when work remains, accepted continuation leads to planning the next Increment. Strict still asks before implementing that plan.
- **Predictable Continue:** chat, CLI and UI share the next-step resolver. A saved pause or blocker takes precedence over a change request; an approved scope split stays approved.
- **Reliable registration:** interrupted or repeated approval calls preserve committed acceptance without duplicate decisions. Earlier gate approvals retain their original meaning.

Project-specific skills, adaptive agent allocation, review tied to current code and reusable repository knowledge remain part of AIM. Review and whole-Epic verification still apply. See [combined decisions](docs/workflow/streamlined-decisions.md). Full agent-runtime savings have not yet been measured.

**A convincing win in the completed Enigma pair:** Luna + AIM 3.2 passed **123/123 independent Py-Enigma vectors versus 1/123** and found valid candidates in **9/9 new positive search cases versus 0/9**. The AIM app also had stronger visual finish and code structure. Two specific complete searches ran **40.9× and 14.5× faster**; these are application-runtime results. Luna alone built sooner (14:52 versus 52:59). [Case, method and evidence](docs/features/aim-3.2-enigma-case.md) · [Earlier resource-efficiency results](docs/features/aim-3.1-evaluation.md).

![AIM UI Beta control room](github-pages/assets/images/aim-ui-beta-control-room.png)

See the [AIM UI Beta guide](docs/product/aim-ui.md), or launch it with `/aim ui`.
AIM Reflect still **goes beyond memory cleanup for repository work** through verified provenance and user-owned promotion. The AIM runtime contract remains 2.0; product, runtime, installer, and schema versions stay separate.

## Safety

- one main AIM thread owns `.aim/state.json` and gate transitions
- native specialists never accept work or create parallel AIM runtimes
- existing files are collision-protected
- apply is rollback-protected and idempotent
- unavailable native delegation falls back to the same sequential role loop
- tags, releases, deploys, and other external changes still need explicit scope

## Documentation

- [Engineering delivery and role skills](docs/workflow/engineering-delivery.md) · [Enigma comparison analysis and measured improvements](docs/features/engineering-reset-analysis.md)
- [Feature guide](docs/product/features.md) · [AIM UI control room](docs/product/aim-ui.md) · [First-time journey](docs/product/getting-started.md)
- [Platforms and project specialists](docs/product/platforms-and-adoption.md) · [Install and upgrade](docs/workflow/install-aim-2.0.md) · [Canonical AIM method](docs/workflow/agile-iteration-method.md)
- [AIM Reflect](docs/workflow/reflection.md) · [Troubleshooting](docs/workflow/troubleshoot-aim-2.0.md) · [Release and publication](docs/workflow/release-publication-model.md) · [Public Agent Skill distribution](docs/workflow/version-and-installation.md)

Current product version: **v3.2.0**. See [CHANGELOG.md](CHANGELOG.md). Documentation is licensed under [CC BY 4.0](LICENSE).

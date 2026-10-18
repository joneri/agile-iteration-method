# Agile Iteration Method (AIM)

![AIM - Agile Iteration Method](github-pages/assets/images/aim-2-hero-dark.png)

AIM helps your AI agent turn an idea into working software. It plans the work,
checks the result through independent review and real product verification, and
keeps acceptance with you. Use it with Codex, Claude Code or GitHub Copilot.

You describe the outcome. AIM keeps the requirements, approved work, measurements
and remaining problems together so another session can continue from current facts.

## Install

Install the complete, self-contained AIM Agent Skill through the open skills ecosystem:

[![skills.sh](https://skills.sh/b/joneri/agile-iteration-method)](https://skills.sh/joneri/agile-iteration-method)

```bash
npx skills add joneri/agile-iteration-method --skill agile-iteration-method
```

Select your agent and project in the installer. Then tell the agent what you want:

```text
/aim start "Make checkout recovery clear when payment confirmation is delayed"
```

AIM discovers the relevant repository context and identifies the next useful step.
The complete skill works without keeping this source checkout. Node.js/npm runs
the installer; Python 3 runs AIM's local helpers. You can also copy [the short
agent setup instructions](github-pages/assets/aim-install-agent.txt) into your agent.

Target one supported agent explicitly when needed:

```bash
# Codex
npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent codex --yes

# GitHub Copilot
npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent github-copilot --yes

# Claude Code
npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent claude-code --yes
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

Learning is part of ordinary delivery: AIM recalls bounded shared advice while planning, reviewing and diagnosing failures, and shares evidence-linked reusable lessons. No manual reflection command, repository inventory or mandatory report is required. The old `reflect` and `reflect-all` names are retired compatibility aliases. A concrete stale fact, contradiction or suspected missing lesson can justify a targeted authorized source audit. Maintained project knowledge keeps its own sources and reviewed change path.

Use `/aim help` when you want the next useful action. The same command family also covers continue, status, validation, configuration, upgrade, memory, execution mode, cost depth, and replanning.

## From intent to accepted User Stories

```text
Intent → Epics → User Stories → delivery selection → working increment
```

Describe what you want to achieve, or provide detailed requirements. PO owns Epic outcomes and product priority. TDO creates and owns Stories and criteria, then plans a coherent increment that can include Stories from different Epics.

Run `/aim ui` to follow **User Stories as moving cards**, with Epic context and individual evidence. A Sprint is an optional timebox. An increment is the working result of delivered Stories.

Use `/aim graph` or the UI's **Graph** tab to see what can start, what blocks the delivery,
and which proof needs updating. [How AIM Graph works](docs/workflow/adaptive-execution.md#aim-graph).

Existing Epic/Increment work keeps its original state and approvals in Delivery control. Nothing is automatically migrated or relabelled. See [the requirements model](docs/workflow/user-stories.md).

## How AIM works

```text
PO → TDO → Dev → Reviewer → TDO → PO
```

- **PO** owns intent, Epic outcomes and product priority.
- **TDO** owns Stories and criteria, plans the coherent increment and validates delivery.
- **Dev** implements the approved selection.
- **Reviewer** checks current behavior, regressions and Story evidence.

Gate A confirms direction and requirements. Gate B approves the selection and plan. Gate E accepts verified Stories. Epic closure is a separate decision supported by whole-outcome evidence.

`Strict` asks for plan approval and acceptance. `Auto` progresses within existing authority, returning for changed scope, risk or final acceptance.

## Repository-aware, not repository-heavy

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

## What is new

- **Quality goals guide the next action.** Plan relevant checks before implementation,
  measure the first working core, and address failed or stale results before readiness.
- **Review starts where mistakes are expensive.** A separate reviewer can challenge
  an unproved core reference early and checks the integrated delivery later.
- **Results stay tied to their source.** Retain raw evidence, original failures and
  the actual build. Optional JSON observations derive values from that evidence.
- **Product knowledge can be reused.** Keep a small map of user routes and a runnable
  verification recipe where Dev and Reviewer can find and maintain it.
- **Learning happens during ordinary work.** Recall relevant local shared lessons and
  contribute generalized verified corrections without manual reflection reports.
- **Continue with less repeated setup.** Reuse compact confirmed receipts, unchanged
  evidence and relevant repository knowledge instead of routinely rereading everything.

These are supported method capabilities. Their practical effect still depends on
agents using them and on the repository's verification coverage. See the [feature
guide](docs/product/features.md) and [changelog](CHANGELOG.md).

## What the Enigma results show

The latest completed product assessment scored **96.5/100**, against the historical
reference's **93.5/100**. The simulator passed **123/123** reference vectors, all
**9/9** positive search cases passed, and all **114/114** returned candidates were
independently validated. This is one assisted run with GPT-6 Luna High; the actual
tested build and every retained earlier result are identified in the [Enigma
evaluation](docs/features/aim-enigma-evaluation.md).

The product score does not establish general superiority, lower cost or completion
of all method goals. The run missed one internal latency target and did not finish
its native delivery. Both whole-workflow administration reduction targets remain
unproved. The [historical paired study](docs/features/aim-3.2-enigma-case.md) remains
available with its original evidence.

## Versions and compatibility

See [VERSION](VERSION) for the current release and [CHANGELOG.md](CHANGELOG.md) for changes.
Product versions and runtime/schema contracts are separate. Upgrades preserve active work and accepted evidence.

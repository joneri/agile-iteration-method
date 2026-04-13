# Agile Iteration Method (AIM) v1.5

AIM is a way to run agentic software delivery without losing the thread.

It gives AI work a clear Agile loop instead of a prompt spiral.

One loop:

`PO -> TDO -> Dev -> Reviewer -> TDO -> PO`

That means:
- the Epic is owned by `PO`
- the next single Done Increment is owned by `TDO`
- implementation stays scoped
- review happens before acceptance
- the work is always judged as end-to-end user value, not random partial progress

If you want AI work to stay scoped and reviewable, that is the point.

## Why AIM

Without a method, agentic development usually breaks in predictable ways:
- the agent jumps between theories without proving anything
- scope expands silently
- "progress" becomes a pile of partial edits instead of a shippable slice
- no one knows what the next approval actually means

AIM fixes that with clear roles, gates and ownership.

## What's new in v1.5

AIM 1.5 keeps the accepted core loop and runtime model and makes the latest delivery guidance visible in the public product story.

- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume and gate tracking
- small Done Increments are defined by behavioral scope, not by artificially few files
- focused file boundaries are treated as part of product quality and future context efficiency
- Codex, Copilot and Claude Code still share one conceptual runtime contract
- the front-door docs now expose the latest adapter and onboarding story as one clear release path

## Why teams use it

This release is easier to trust, explain and adopt:
- you can resume real work instead of re-explaining context every session
- you can inspect runtime state instead of guessing what the agent thinks is happening
- you can use Codex, Copilot and Claude Code with one shared conceptual model
- you can use more focused files without pretending that fewer files always means smaller scope
- you can delegate bounded work without losing ownership of gates or acceptance
- you can install AIM into a real repo without turning the repo into an experiment
- the public docs make the latest version easier to start, inspect, and explain

## What changed in 1.5

- AIM 1.5 keeps the accepted `core + runtime + repo-aware policy + platform adapters` model.
- file-boundary discipline is now part of the visible release story, not just internal guidance.
- the newest install, quick-start, doc-map, troubleshoot, and upgrade docs now point to one latest-version surface.

## From prompt pattern to runtime

Before AIM 1.3, the method was there but the runtime story was too loose.

With AIM 1.4, the runtime became inspectable and adapter-aware.

With AIM 1.5:
- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume and gate tracking
- small scope is defined by behavior and user value, not by lowest possible file count
- the public onboarding path makes the latest guidance obvious to new users
- adapter guidance, packaging, and upgrade docs now read as one current release surface

That is the main upgrade: AIM 1.5 makes the accepted runtime easier to use, review, and explain in real delivery work.

## Start Here

Use the front-door path that matches your goal:

- Evaluate AIM:
  - [Quick start AIM 1.5](docs/workflow/quick-start-aim-1.5.md)
  - [AIM 1.5 interaction examples](docs/workflow/aim-1.5-interaction-examples.md)
  - [AIM 1.5 document map](docs/workflow/aim-1.5-doc-map.md)
- Install AIM in a repository:
  - [Install AIM 1.5](docs/workflow/install-aim-1.5.md)
  - [Quick start AIM 1.5](docs/workflow/quick-start-aim-1.5.md)
  - [Troubleshoot AIM 1.5](docs/workflow/troubleshoot-aim-1.5.md)
- Upgrade an AIM 1.4 repository:
  - [Migrate AIM 1.4 to AIM 1.5](docs/workflow/migrate-aim-1.4-to-1.5.md)
  - [Quick start AIM 1.5](docs/workflow/quick-start-aim-1.5.md)
  - [AIM 1.5 document map](docs/workflow/aim-1.5-doc-map.md)

What each front-door doc is for:
- `README.md` explains the product and helps you choose a path.
- `install-aim-1.5.md` is for repository setup and adapter packaging.
- `quick-start-aim-1.5.md` is for the first Epic and the first visible AIM loop.
- `aim-1.5-doc-map.md` is for finding the next document without dropping into the reference/spec layer too early.

## Choose Your Adapter

- Codex:
  the repo is the AIM contract. The Codex skill adds the `/aim` launcher plus bootstrap help.
- Copilot:
  use the packaged `aim` agent in `.github/agents/` and add `.github/prompts/` when you want Copilot-style command helpers.
- Claude Code:
  use `CLAUDE.md` plus the shipped starter files in `.claude/commands/` and `.claude/agents/`.

This repo now ships a small Claude starter layer so Claude Code users can start from real files instead of abstract directory guidance.

Important installation rule:
- `.github/agents/aim*.agent.md` are part of the AIM instruction layer, not just Copilot decoration.
- `.github/prompts/` are optional Copilot prompt helpers.

## Codex model

- The repository is the canonical AIM contract.
- The Codex skill is a bootstrap and convenience layer.
- `/aim` is the normal Codex start path when the AIM skill is installed and enabled.
- A fully AIM-aware repo can still be used in Codex without the skill if you start with explicit AIM intent in plain language.
- The skill is still useful in a prepared repo because it gives you the clean `/aim` entrypoint plus status, help, config, validate and upgrade helpers.

| Adapter | Canonical contract | Convenience layer | Normal start path | Required for best experience |
| --- | --- | --- | --- | --- |
| Codex | `AGENTS.md` + `docs/workflow/agile-iteration-method.md` + `.github/agents/aim*.agent.md` | Codex AIM skill | `/aim start "EPIC: ..."` | Skill enabled for `/aim`; repo alone can still work with explicit AIM intent |
| Copilot | `AGENTS.md` + `docs/workflow/agile-iteration-method.md` + `.github/agents/aim*.agent.md` | `.github/prompts/` | select `aim` and run `/aim start "EPIC: ..."` | `.github/agents/aim*.agent.md`; prompts optional |
| Claude Code | `AGENTS.md` + `docs/workflow/agile-iteration-method.md` + `.github/agents/aim*.agent.md` + `CLAUDE.md` | `.claude/commands/` and `.claude/agents/` | repo Claude command or explicit `EPIC: ...` | `CLAUDE.md`; `.claude/` helpers recommended |

## Starting A New Repo With AIM v1.5

Use this path when the repository does not exist yet or when you want to bootstrap a new repo around AIM from day one.

### 1. Copy the AIM files into the new repo

Required for AIM:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`

Recommended:
- `docs/workflow/quick-start-aim-1.5.md`
- `docs/workflow/install-aim-1.5.md`
- `docs/workflow/migrate-aim-1.4-to-1.5.md`
- `docs/workflow/troubleshoot-aim-1.5.md`
- `examples/epics/example-epic.md`

Optional GitHub Copilot prompt files:
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.4-to-1.5.prompt.md`

If you want Claude Code support too, also copy:
- `CLAUDE.md`
- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`

What each file is for:
- `AGENTS.md` defines the canonical repo-aware AIM behavior.
- `.github/agents/aim*.agent.md` are part of the AIM instruction layer and affect behavior in both Codex and Copilot.
- in Copilot, those same files also act as native custom-agent files.
- `.github/prompts/` are optional prompt-entry helpers, mainly useful for Copilot-style command flows.
- Claude Code uses `CLAUDE.md` and `.claude/` as its adapter layer but does not replace `AGENTS.md`.

### 2. Ignore live AIM runtime state

Add this to `.gitignore` if it is not already there:

```gitignore
/.aim
```

`.aim/` is runtime state, not release material. AIM creates it automatically on first valid start.

### 3. Add your repository-specific rules to `AGENTS.md`

Before the first run, make sure your repo profile is real, not generic. At minimum, define:
- stack and runtime assumptions
- verification and testing strategy
- deployment and migration constraints
- role-specific constraints for `PO`, `TDO`, `Dev` and `Reviewer`

This is what makes AIM behave like your repo instead of a generic chatbot.

### 4. Start your first Epic

In Codex:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
```

`/aim` is the normal Codex start path when the AIM skill is installed and enabled.
If the repo already contains the AIM contract but the skill is not available, start with:

```text
EPIC: <desired user outcome>
Mode: Strict
```

In Copilot:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
```

In Claude Code:

```text
EPIC: <desired user outcome>
Mode: Strict
```

This repository also ships a small Claude starter layer:
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`
- `.claude/agents/aim.md`

If Claude Code exposes repo command files directly in your environment, use the shipped start command. Otherwise use the explicit start prompt above.

If you want automatic continuation between increments, use `Mode: Auto` instead of `Mode: Strict`.

## Installing AIM On An Existing Repo

Use this path when the product, codebase, tests and CI already exist and you want AIM to become the operating model on top of that repo.

### 1. Keep your product code. Add AIM around it.

You do not need to restructure the application first.

Add the core AIM files:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`

Add optional Copilot prompt files if you want packaged Copilot entrypoints too:
- `.github/prompts/`

Add Claude Code packaging too if needed:
- `CLAUDE.md`
- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`

Important:
`.github/agents/aim*.agent.md` are not Copilot-only.
In AIM, they are part of the repository instruction layer and should be installed for proper AIM behavior in both Codex and Copilot.

### 2. Make `AGENTS.md` repo-aware

For an existing repo, this is the most important step.

Update `AGENTS.md` so it reflects reality:
- what stack the repo uses
- how verification should be done
- what commands are safe
- what must never be done without escalation
- whether parallel or delegated work is allowed

If these rules stay vague, AIM will stay vague.

### 3. Preserve your existing engineering standards

AIM does not replace your tests, CI, review standards or release process.

It adds:
- role discipline
- increment discipline
- runtime state and resume behavior
- better approval semantics

### 4. Start with a real Epic, not a task list

Bad start:

```text
Fix file X, then maybe refactor Y, then add tests
```

Good start:

```text
EPIC: Make the onboarding flow understandable for first-time users without breaking existing signup behavior
Mode: Strict
```

`PO` owns the outcome. `TDO` owns the next single Done Increment.

## The Fastest Way To Get Agentic Value

If someone lands on this repo and wants the shortest possible path, this is it:

1. Copy `AGENTS.md` and `docs/workflow/agile-iteration-method.md` into the target repo.
2. Copy `.github/agents/aim*.agent.md` into the target repo.
3. Add `/.aim` to `.gitignore`.
4. Optionally copy `.github/prompts/` if you want packaged Copilot prompt entrypoints too.
5. Optionally add `CLAUDE.md` and `.claude/` if you want Claude Code support too.
6. Open the repo in Codex, Copilot or Claude Code.
7. Start with `/aim start "EPIC: <desired outcome>"` when the Codex skill or another slash-command adapter surface is available. Otherwise start with `EPIC: <desired outcome>` and `Mode: Strict` or `Mode: Auto`.

## Why AIM Feels Different

Most AI coding workflows chase speed of output.

AIM aims for:
- correctness you can explain
- scope you can control
- increments you can actually ship
- approvals that mean something
- runtime state you can inspect

That is why AIM works better on real software delivery than "just ask the model again."

## What AIM Creates At Runtime

On first valid start, AIM creates `.aim/` if it does not already exist.

Important runtime artifacts:
- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

The main AIM thread owns gate progression and `.aim/state.json`.
Subagents, when allowed, must stay bounded and must not take over shared state or acceptance decisions.

## What The User Experience Looks Like

For each Done Increment, AIM runs this sequence:

1. `PO` frames the Epic
2. `TDO` proposes the next single Done Increment
3. `Dev` implements that increment
4. `Reviewer` checks correctness, risk and readiness
5. `TDO` presents the increment as a demo/test checkpoint
6. `PO` decides whether the Epic continues or closes

The meaningful approval points are:
- Gate A: Epic framing
- Gate B: next Done Increment
- Gate E: accept the increment or request adjustment

## Strict vs Auto

- `Mode: Strict`
  Pauses at the meaningful hard gates.
- `Mode: Auto`
  Continues through increments automatically unless an escalation condition is hit.

Use `Strict` by default for new teams or high-trust-sensitive work.
Use `Auto` when the Epic is clear and you want faster throughput with the same gate logic.

## Platform Adapters

AIM 1.5 explicitly separates:
- AIM core
- AIM runtime
- repo-aware policy
- platform adapters

That matters because Codex, Copilot and Claude Code do not always expose the same runtime capabilities.

The rule is simple:
- same method where parity is possible
- explicit fallback where parity is not possible
- no silent redefinition of gates, ownership or acceptance

### Instruction layering in practice

AIM uses layered repository instructions:

1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`

This means `.github/agents/` files are part of AIM behavior in practice, not just optional Copilot decoration.

In Copilot, they also act as native custom-agent files.
In Codex, AIM reads and uses them as part of the repository instruction layer.

Claude Code uses a separate adapter bridge:
- `CLAUDE.md`
- `.claude/agents/`
- `.claude/commands/`

These files extend the Claude adapter surface but they do not replace `AGENTS.md` as the canonical AIM contract.

## Recommended Reading Order

If you want to use AIM:
1. [README.md](README.md)
2. [Install AIM 1.5](docs/workflow/install-aim-1.5.md) when you need repo setup
3. [Quick start AIM 1.5](docs/workflow/quick-start-aim-1.5.md) for the first run
4. [AIM 1.5 document map](docs/workflow/aim-1.5-doc-map.md) for the rest of the public path

If you want to upgrade an existing AIM repo:
1. [Migrate AIM 1.4 to AIM 1.5](docs/workflow/migrate-aim-1.4-to-1.5.md)
2. [Quick start AIM 1.5](docs/workflow/quick-start-aim-1.5.md)
3. [Troubleshoot AIM 1.5](docs/workflow/troubleshoot-aim-1.5.md)

If you are implementing AIM itself:
1. [AGENTS.md](AGENTS.md)
2. [Agile iteration method](docs/workflow/agile-iteration-method.md)
3. [AIM adapter guidance](docs/workflow/aim-adapter-guidance.md)

Do not start with `AGENTS.md` when the goal is just to install or run AIM in a repository.

## Repository Map

- `AGENTS.md`
  Canonical repository AIM contract across adapters.
- `CLAUDE.md`
  Claude Code bridge layer that maps AIM onto Claude Code without changing the shared runtime contract.
- `docs/workflow/agile-iteration-method.md`
  The method and runtime explanation.
- `docs/workflow/quick-start-aim-1.5.md`
  The shortest correct start path.
- `docs/workflow/install-aim-1.5.md`
  Minimum viable installation guidance.
- `docs/workflow/aim-1.5-doc-map.md`
  Route map for the public docs and the correct next read.
- `docs/workflow/copilot-layer.md`
  Optional GitHub Copilot packaging and workflow layer.
- `docs/workflow/release-aim-1.5.md`
  Release note and publish checklist for the current version.
- `docs/workflow/migrate-aim-1.4-to-1.5.md`
  Upgrade guidance for existing AIM repos.
- `docs/workflow/troubleshoot-aim-1.5.md`
  Startup, resume, validator and fallback troubleshooting.
- `docs/workflow/example-aim-1.5-reference-run.md`
  Concrete example of an AIM 1.5 run.
- `examples/epics/example-epic.md`
  Example Epic input.

## Contributing

Use AIM to improve AIM.

See `CONTRIBUTING.md` for consistency rules, scope rules and documentation expectations.

## License

Documentation in this repository is licensed under [CC BY 4.0](LICENSE).

## Credits

Created by Jonas Eriksson.

Contributors:
- [@liamwears](https://github.com/liamwears)

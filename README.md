# Agile Iteration Method (AIM) v1.3

AIM is a release-ready operating system for agentic software delivery.

It gives AI work a real Agile shape instead of a chaotic prompt spiral.

One explicit loop:

`PO -> TDO -> Dev -> Reviewer -> TDO -> PO`

That means:
- the Epic is owned by `PO`
- the next single Done Increment is owned by `TDO`
- implementation stays scoped
- review happens before acceptance
- the work is always judged as end-to-end user value, not random partial progress

If you want agentic magic without agentic chaos, this is the point.

## Why AIM exists

Without a method, agentic development usually breaks in predictable ways:
- the agent jumps between theories without proving anything
- scope expands silently
- "progress" becomes a pile of partial edits instead of a shippable slice
- no one knows what the next approval actually means

AIM fixes that with explicit roles, explicit gates, and explicit ownership.

## What is new in v1.3

AIM 1.3 is the release where AIM stops feeling like a clever prompt pattern and starts feeling like a real operating model.

The core loop stays stable. The runtime becomes explicit.

- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume, and gate tracking
- Codex and Copilot can share one conceptual runtime contract
- adapter limitations are treated as limitations, not silent method drift
- Controlled parallelism lets AIM use bounded subagents for faster analysis, discovery and verification when the runtime and repo policy allow it, while keeping shared state, gate progression and acceptance centrally owned.

## Why teams care now

This release makes AIM much easier to trust, explain, and adopt:
- you can resume real work instead of re-explaining context every session
- you can inspect runtime state instead of guessing what the agent thinks is happening
- you can use Codex and Copilot with one shared conceptual model
- you can delegate bounded work without losing ownership of gates or acceptance
- you can install AIM into a real repo without turning the repo into an experiment
- Faster where it helps:
  AIM can use bounded subagents for analysis, discovery and verification in complex repos, while still keeping one central runtime state and one clear decision path.

## From Prompt Pattern To Runtime Model

Before AIM 1.3, the method was strong but the runtime story was too implicit.

With AIM 1.3:
- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume, and gate tracking
- startup, resume, validation, and fallback behavior are documented
- repo-aware policy is a first-class part of the method
- platform adapters are explicit instead of hidden

That is the big upgrade: AIM 1.3 makes agentic delivery operational, not mystical.

## Start Here

Choose the path that matches your situation:

1. Starting a new repository with AIM
2. Installing AIM into an existing repository

## Starting A New Repo With AIM v1.3

Use this path when the repository does not exist yet, or when you want to bootstrap a new repo around AIM from day one.

### 1. Copy the AIM files into the new repo

Required:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`

Recommended:
- `docs/workflow/quick-start-aim-1.3.md`
- `docs/workflow/install-aim-1.3.md`
- `docs/workflow/migrate-aim-1.2-to-1.3.md`
- `docs/workflow/troubleshoot-aim-1.3.md`
- `examples/epics/example-epic.md`

If you want GitHub Copilot support too, also copy:
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.2-to-1.3.prompt.md`

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
- role-specific constraints for `PO`, `TDO`, `Dev`, and `Reviewer`

This is what makes AIM behave like your repo instead of a generic chatbot.

### 4. Start your first Epic

In Codex:

```text
[$agile-iteration-method](...) Start new AIM loop with:
EPIC: <desired user outcome>
Mode: Strict
```

In Copilot:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
```

If you want automatic continuation between increments, use `Mode: Auto` instead of `Mode: Strict`.

## Installing AIM On An Existing Repo

Use this path when the product, codebase, tests, and CI already exist and you want AIM to become the operating model on top of that repo.

### 1. Keep your product code. Add AIM around it.

You do not need to restructure the application first.

Add the AIM files:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`

Add Copilot packaging too if needed:
- `.github/agents/`
- `.github/prompts/`

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

AIM does not replace your tests, CI, review standards, or release process.

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
2. Add `/.aim` to `.gitignore`.
3. If using Copilot, copy `.github/agents/` and `.github/prompts/`.
4. Open the repo in Codex or Copilot.
5. Start with `EPIC: <desired outcome>` and `Mode: Strict` or `Mode: Auto`.

## Why This Feels Different From Normal AI Coding

Most AI coding workflows optimize for speed of output.

AIM optimizes for:
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
4. `Reviewer` checks correctness, risk, and readiness
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

## Codex And Copilot

AIM 1.3 explicitly separates:
- AIM core
- AIM runtime
- repo-aware policy
- platform adapters

That matters because Codex and Copilot do not always expose the same runtime capabilities.

The rule is simple:
- same method where parity is possible
- explicit fallback where parity is not possible
- no silent redefinition of gates, ownership, or acceptance

## Recommended Reading Order

If you are evaluating AIM:
1. `README.md`
2. `docs/workflow/quick-start-aim-1.3.md`
3. `docs/workflow/agile-iteration-method.md`
4. `docs/workflow/install-aim-1.3.md`

If you are installing AIM in a repo:
1. `docs/workflow/install-aim-1.3.md`
2. `AGENTS.md`
3. `docs/workflow/quick-start-aim-1.3.md`
4. `docs/workflow/troubleshoot-aim-1.3.md`

If you are upgrading from an older AIM version:
1. `docs/workflow/migrate-aim-1.2-to-1.3.md`
2. `docs/workflow/release-aim-1.3.md`

## Repository Map

- `AGENTS.md`
  Operational AIM rules for Codex-style execution.
- `docs/workflow/agile-iteration-method.md`
  The method and runtime explanation.
- `docs/workflow/quick-start-aim-1.3.md`
  The shortest correct start path.
- `docs/workflow/install-aim-1.3.md`
  Minimum viable installation guidance.
- `docs/workflow/copilot-layer.md`
  Optional GitHub Copilot packaging and workflow layer.
- `docs/workflow/migrate-aim-1.2-to-1.3.md`
  Upgrade guidance for existing AIM repos.
- `docs/workflow/troubleshoot-aim-1.3.md`
  Startup, resume, validator, and fallback troubleshooting.
- `docs/workflow/example-aim-1.3-reference-run.md`
  Concrete example of an AIM 1.3 run.
- `examples/epics/example-epic.md`
  Example Epic input.

## Contributing

Use AIM to improve AIM.

See `CONTRIBUTING.md` for consistency rules, scope rules, and documentation expectations.

## License

Documentation in this repository is licensed under [CC BY 4.0](LICENSE).

## Credits

Created by Jonas Eriksson.

Contributors:
- [@liamwears](https://github.com/liamwears)

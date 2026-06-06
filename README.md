# Agile Iteration Method (AIM) v2.0

AIM 2.0 is the low-footprint adoption release for GitHub Copilot, Codex, Claude Code, and other coding-agent platforms.

It gives AI work a clear Agile loop instead of a prompt spiral, and it makes that loop easier to start personally, share with a team, and reuse across sessions without committing a broad AIM package into every repository.

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

## What's new in v2.0

AIM 2.0 keeps the accepted core loop and stable runtime contract, but changes the adoption model.

- Personal AIM lets one developer use AIM without required committed AIM files
- Team AIM lets a team share repo adaptation through a tiny `aim.profile.yaml` profile or pointer
- AIM runtime, repo profile, working state and docs are treated as separate things
- profile-first startup reuses repo intelligence before broad scans
- branch and session reuse become part of the normal operating model
- Cost profiles are now explicit: `Standard`, `Cost Control`, and `Deep`
- `Cost Control` keeps AIM gates and escalation rules while reducing context, output, and verification depth for low-risk work
- `Standard` AIM now uses progressive context loading by default instead of rereading every method document
- `Deep` is available for high-risk work where broader inspection and stronger review are worth the spend
- GitHub Copilot AI Credits are treated as a first-class operator concern after the June 1, 2026 billing change
- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume and gate tracking
- small Done Increments are defined by behavioral scope, not by artificially few files
- focused file boundaries are treated as part of product quality and future context efficiency
- context hogs are treated as a real delivery problem, not as proof that scope stayed small
- Codex, Copilot and Claude Code still share one conceptual runtime contract
- the front door is lighter: start, continue, or validate first; read deeper only when needed

## Why teams use it

Teams use AIM 2.0 because it makes disciplined agentic work easier to adopt without turning the repository into a method package:
- you can resume real work instead of re-explaining context every session
- you can inspect runtime state instead of guessing what the agent thinks is happening
- you can use Codex, Copilot and Claude Code with one shared conceptual model
- you can use more focused files when that avoids context hogs and keeps boundaries cohesive
- you can delegate bounded work without losing ownership of gates or acceptance
- you can start personally with no required committed AIM files
- you can share team repo knowledge through a tiny profile instead of copying full AIM docs
- you still get strong cost discipline without weakening trust or review

## Why 2.0

AIM 2.0 is a release identity change, not a method break.

- the core loop is still `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- the accepted runtime contract and `.aim` ownership model stay intact
- the big change is adoption: Personal AIM, Team AIM, and Enterprise AIM are clear operating modes

The method stays stable. The install footprint gets smaller and reuse gets stronger.

## How AIM saves money

AIM 2.0 keeps cost discipline and extends it to adoption, startup and reuse:

- it prevents uncontrolled retries by forcing one approved Done Increment at a time
- it keeps low-risk work in `Cost Control` instead of burning `Deep`-style context and review everywhere
- it makes normal work cheaper through progressive context loading instead of full-method rereads
- it limits waste from oversized sessions, bloated prompts, and accidental scope creep
- it separates pricing investigations from implementation work so teams do not pay premium agent costs just to rediscover billing facts
- it tells teams when to stop guessing and check official vendor billing behavior first

That matters even more after GitHub Copilot moved to AI-credit billing on June 1, 2026.
For the concrete comparison against undisciplined vibe coding and oversized agent sessions, see [AIM cost comparison](docs/features/aim-cost-comparison.md).

In practice, AIM should spend attention only where risk justifies it.
Low-risk cleanup can run in Cost Control, while trust-sensitive product work can stay Standard or move to Deep.

## From prompt pattern to runtime

With AIM 2.0:
- `.aim/` is the official repo-local AIM workspace
- `.aim/state.json` is the durable checkpoint for start, resume and gate tracking
- `aim.profile.yaml` is the default tiny Team AIM profile when a team chooses to share repo intelligence
- Personal AIM can keep reusable repo knowledge outside the repository by default
- small scope is defined by behavior and user value, not by lowest possible file count
- runtime depth is explicit through cost profiles
- normal AIM loads context progressively instead of treating every run as a full reread
- the public onboarding path makes the latest guidance obvious to new users
- the front door starts with three simple choices instead of the full method
- Codex users can see and install the repo-bundled AIM skill from the first AIM command
- adapter guidance and packaging now read as one current release surface

That is the main upgrade: AIM 2.0 makes the accepted runtime easier to adopt, reuse and afford without weakening ownership, gates or escalation.

## Start Here

Choose one:

1. [Start AIM 2.0 in Personal, Team, or Enterprise mode](docs/workflow/quick-start-aim-2.0.md)
2. [Continue or troubleshoot AIM](docs/workflow/troubleshoot-aim-2.0.md)
3. [Install AIM](docs/workflow/install-aim-2.0.md)

The AIM 2.0 path is the current adoption path:

- Personal AIM: start AIM without required committed AIM files
- Team AIM: share a tiny repo profile through `aim.profile.yaml`
- Enterprise AIM: keep AIM internals isolated by default and share repo-awareness only by explicit approval

Full embedded AIM remains available as a footprint choice when the repository owner intentionally wants AIM product docs and adapter helpers in the repo.

Fast start:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
Cost profile: Cost Control
```

Use `Cost Control` for ordinary low-risk work. Use `Deep` when the work touches trust, data correctness, deployment, migration, security, or public APIs.

Calibrate persistent repository knowledge after installation:

```text
/aim calibrate-repo
```

Teach or remove structured repository habits later:

```text
/aim remember-repo habits "Run rsync before every Gate E"
/aim forget-repo validation "old-validation-command"
```

Shared knowledge lives in `aim.profile.yaml`.
Personal hints live at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
`.aim/` remains runtime-only.

Keep startup knowledge compressed in `aim.profile.yaml`. For complex repo-specific procedures, the profile points to AIM-owned `docs/workflow/repo-<area>.md` operational docs that load only when their work, role/gate, risk, command, or calibration trigger matches.

## Choose Your Adapter

- Codex:
  install the shipped skill at `adapters/codex/agile-iteration-method/SKILL.md` for the `/aim` launcher, or start with explicit AIM intent.
- Copilot:
  use the packaged `aim` agent in `.github/agents/`; `.github/prompts/` adds optional command helpers.
- Claude Code:
  use `.claude/commands/` and `.claude/agents/`, or start with explicit AIM intent.

Important installation rule:
- canonical AIM behavior lives under `docs/workflow/`
- shared repo-awareness comes from root `aim.profile.yaml`
- generic root files are not AIM control surfaces
- adapter packages are optional and secondary

## Codex model

- Canonical workflow docs are the AIM contract.
- The shipped Codex skill in `adapters/codex/agile-iteration-method/SKILL.md` is a bootstrap and convenience layer.
- `/aim` is the normal Codex start path when the AIM skill is installed and enabled.
- A fully AIM-aware repo can still be used in Codex without the skill if you start with explicit AIM intent in plain language.
- The skill is still useful in a prepared repo because it gives you the clean `/aim` entrypoint plus status, help, config, validate and upgrade helpers.
- On the first AIM command in Codex, AIM should make the bundled skill path and local install target visible.

60-second local Codex skill install:

```sh
mkdir -p ~/.codex/skills/agile-iteration-method
cp -R adapters/codex/agile-iteration-method/. ~/.codex/skills/agile-iteration-method/
```

Local Codex skill target:

```text
~/.codex/skills/agile-iteration-method/SKILL.md
```

Codex may show the skill picker name and short description from `~/.codex/skills/agile-iteration-method/agents/openai.yaml`, so copy the full directory. If the picker still shows an older AIM version after reinstalling, restart or refresh Codex.

The skill is copyable adapter packaging. It must point back to canonical workflow docs instead of becoming a second method definition.

| Adapter | Canonical contract | Convenience layer | Normal start path | Required for best experience |
| --- | --- | --- | --- | --- |
| Codex | canonical workflow docs + `aim.profile.yaml` | `adapters/codex/agile-iteration-method/` | `/aim start "EPIC: ..."` | installed skill for `/aim`; explicit AIM intent remains valid |
| Copilot | canonical workflow docs + `aim.profile.yaml` | `.github/agents/` and optional `.github/prompts/` | select `aim` and run `/aim start "EPIC: ..."` | selected AIM agent package |
| Claude Code | canonical workflow docs + `aim.profile.yaml` | optional `.claude/commands/` and `.claude/agents/` | shipped command or explicit `EPIC: ...` | selected Claude package or explicit AIM intent |

## Starting A New Repo With Full Embedded AIM

Use this path when the repository owner intentionally wants the full embedded AIM package in a new repository from day one.

### 1. Copy the AIM files into the new repo

Required for AIM:
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-awareness.md`
- `aim.profile.yaml` when shared repo-awareness is wanted

Recommended:
- `README.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/install-aim-2.0.md`
- `docs/workflow/troubleshoot-aim-2.0.md`
- `examples/epics/example-epic.md`

Optional GitHub Copilot prompt files:
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`

Optional Codex skill packaging:
- `adapters/codex/agile-iteration-method/SKILL.md`

For Claude Code, select the `.claude/agents/` and `.claude/commands/` package you need.

What each file is for:
- `docs/workflow/agile-iteration-method.md` defines AIM core behavior.
- `docs/workflow/repo-awareness.md` defines how repo guidance is found and layered.
- `aim.profile.yaml` is the primary shared repo-awareness source.
- `.github/agents/aim*.agent.md` are native Copilot AIM entrypoints.
- `.github/prompts/` are optional prompt-entry helpers, mainly useful for Copilot-style command flows.
- `adapters/codex/agile-iteration-method/SKILL.md` is the copyable Codex launcher/runtime guide for `/aim`.
- `.claude/` contains optional Claude-native AIM entrypoints.

### 2. Ignore live AIM runtime state

Add this to `.gitignore` if it is not already there:

```gitignore
/.aim
```

`.aim/` is runtime state, not release material. AIM creates it automatically on first valid start.

### 3. Add reusable repository knowledge to `aim.profile.yaml`

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
Cost profile: Standard
```

`/aim` is the normal Codex start path when the AIM skill is installed and enabled.
If the repo already contains the AIM contract but the skill is not available, start with:

```text
EPIC: <desired user outcome>
Mode: Strict
Cost profile: Cost Control
```

In Copilot:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
Cost profile: Standard
```

In Claude Code:

```text
EPIC: <desired user outcome>
Mode: Strict
Cost profile: Standard
```

Add `.claude/commands/` or `.claude/agents/` in target repositories only when Claude-specific command packaging is wanted.
Otherwise use the explicit start prompt above.

If you want automatic continuation between increments, use `Mode: Auto` instead of `Mode: Strict`.

## Installing AIM On An Existing Repo

Use this path when the product, codebase, tests and CI already exist and you want AIM to become the operating model on top of that repo.

### 1. Keep your product code. Add AIM around it.

You do not need to restructure the application first.

Add the core AIM files:
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-awareness.md`
- `aim.profile.yaml` when shared repo-awareness is wanted

Add only the adapter package you need:
- Codex: install `adapters/codex/agile-iteration-method/` locally
- Copilot: select `.github/agents/` and optional `.github/prompts/`
- Claude Code: select `.claude/agents/` and `.claude/commands/`

### 2. Make `aim.profile.yaml` repo-aware

For an existing repo, this is the most important step.

Keep the profile small and factual:
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
Cost profile: Standard
```

`PO` owns the outcome. `TDO` owns the next single Done Increment.

## The Fastest Way To Get Agentic Value

If someone wants the shortest path, this is it:

1. Run `python3 scripts/aim_install.py` and follow the guided prompt.
2. Review the compact preview and choose whether to apply in the same session.
3. Open the repo in Codex, Copilot or Claude Code.
4. Start with `/aim start "EPIC: <desired outcome>"`.
5. If slash commands are unavailable, start with `EPIC: <desired outcome>`, `Mode: Strict`, and `Cost profile: Cost Control`.

Target paths support Tab completion; mode and adapters use keyboard selection menus.
Flags prefill the installer and are not asked again.
Use `--verbose` for the complete plan or `--format json --non-interactive` for automation.

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

## Cost Profiles

Cost profile controls runtime depth, not approval flow.

- `Cost profile: Standard`
  Normal AIM, now cheaper through progressive context loading and compact gates.
- `Cost profile: Cost Control`
  Use for low-risk, reversible cleanup or narrow documentation and adapter maintenance. Gates and escalation rules still apply.
- `Cost profile: Deep`
  Use for trust-sensitive, data correctness, deployment, migration, security, public API, or broad method changes.

Cost Control is not weaker AIM. It is AIM with a smaller runtime budget and a clear rule to escalate when risk appears.

## Platform Adapters

AIM explicitly separates:
- AIM core
- AIM runtime
- repo-aware policy
- platform adapters

That matters because Codex, Copilot and Claude Code do not always expose the same runtime capabilities.

The rule is simple:
- same method where parity is possible
- explicit fallback where parity is not possible
- no silent redefinition of gates, ownership or acceptance

### Loading in practice

1. Resume `.aim/state.json`.
2. Read root `aim.profile.yaml` when present.
3. Apply compatible Personal profile hints.
4. Inspect directly affected repository evidence.
5. Load deeper workflow docs or active adapter policy only when needed.

Generic root instruction files are outside the AIM architecture.

## Recommended Reading Order

If you want to use AIM:
1. [README.md](README.md)
2. [Quick start AIM 2.0](docs/workflow/quick-start-aim-2.0.md) for the first run
3. [Install AIM 2.0](docs/workflow/install-aim-2.0.md) when setup is missing
4. [Troubleshoot AIM 2.0](docs/workflow/troubleshoot-aim-2.0.md) when startup, resume, validation, or adapter behavior is wrong

If you are implementing AIM itself:
1. [Agile iteration method](docs/workflow/agile-iteration-method.md)
2. [Repo-awareness](docs/workflow/repo-awareness.md)
3. [AIM adapter guidance](docs/workflow/aim-adapter-guidance.md)

## Repository Map

- `docs/workflow/agile-iteration-method.md`
  The thin AIM core contract.
- `docs/workflow/repo-awareness.md`
  The primary repo-awareness and progressive-loading model.
- `docs/features/aim-cost-comparison.md`
  Cost comparison against undisciplined vibe coding and oversized agent sessions.
- `docs/workflow/copilot-layer.md`
  Optional GitHub Copilot packaging and workflow layer.
- `adapters/codex/agile-iteration-method/SKILL.md`
  Copyable Codex skill that exposes `/aim` as a launcher/runtime guide.
- `docs/workflow/quick-start-aim-2.0.md`
  Current quick start.
- `docs/workflow/install-aim-2.0.md`
  Current installation front door.
- `docs/workflow/troubleshoot-aim-2.0.md`
  Startup, resume, validator and fallback troubleshooting.
- `examples/epics/example-epic.md`
  Example Epic input.

## Contributing

Use AIM to improve AIM.

When contributing to the AIM source repository, see `CONTRIBUTING.md` for consistency rules, scope rules and documentation expectations.
It is not an AIM installation surface.

## License

Documentation in this repository is licensed under [CC BY 4.0](LICENSE).

## Credits

Created by Jonas Eriksson.

Contributors:
- [@liamwears](https://github.com/liamwears)

<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/project-agent-configuration.md
-->

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM project-agent configuration

## Product rule

AIM is installed through one adaptive path. The user chooses the suppliers they
already uses; AIM then installs each supplier's native AIM skill and
project-agent surface.
Personal, Team, and Enterprise are not separate AIM products or installer
editions. Repository sharing, write footprint, and protected-repository needs
remain explicit policy settings and compatibility inputs.

One canonical role profile carries project intent:

```text
aim.roles.yaml
```

Supplier files are native execution surfaces, not competing sources of truth:

| Supplier | Project-native specialists |
| --- | --- |
| Codex | `.codex/agents/aim-*.toml` |
| Claude | `.claude/agents/aim-*.md` |
| GitHub Copilot | `.github/agents/aim-*.agent.md` |

## Role profile

`aim.roles.yaml` is human-editable and project-specific. It records:

- observable technologies and validation commands
- PO, TDO, Dev, and Reviewer missions
- role-specific expertise and write boundaries
- delegation depth, parallel policy, and model policy
- when the profile should be refreshed

The structural contract is `schemas/aim-project-roles.schema.json`.

The installer may seed conservative facts from files such as `package.json`,
`pyproject.toml`, `Package.swift`, `Cargo.toml`, and `go.mod`. Detected facts are
marked `needs_calibration`; inference is never presented as verified mastery.
`/aim calibrate-repo` verifies repository facts. `/aim configure-agents`
inspects those facts, proposes role expertise, and regenerates only AIM-owned
native files after showing collisions or user edits.

## Native orchestration

The supplier-native AIM skill is the workflow orchestrator. It recognizes the
complete command family, loads AIM core plus project configuration, and delegates
bounded role work to the native specialists below. The skill does not flatten
those specialists into generic prompts: `aim.roles.yaml` continues to define
their project-specific expertise, tools, validation, and boundaries.

Every adapter should use the strongest stable native mechanism available:

- Codex loads project custom agents and may spawn them when the user or
  applicable AIM/project policy explicitly allows delegation.
- Claude loads project subagents and may delegate automatically or explicitly
  from the command-led AIM session.
- Copilot loads repository custom agents and may infer them or receive explicit
  delegation from the AIM orchestrator.

Native capability does not require identical behavior. An adapter may run a
specialist sequentially, in parallel, or not at all when capability, policy,
cost, or task shape makes delegation inappropriate.

## Ownership boundary

The main AIM thread always owns:

- `.aim/state.json`
- role and gate transitions
- scope escalation
- increment and Epic acceptance
- final synthesis

Native specialists produce bounded analysis, implementation, or verification.
They must not advance gates, accept work, or create a parallel AIM runtime.
`aim.roles.yaml` must keep `mainThreadOwnsRuntime: true`.

## Models, tools, and mastery

Default agent files inherit the supplier or organization model. AIM must not
assume that a named paid model is available. Users may pin a model, reasoning
level, tools, skills, MCP servers, permissions, or hooks in the supplier-native
file when their supplier and policy support it.

Project mastery should come from verified, maintainable specificity:

- framework architecture and idioms
- real build, lint, test, browser, and release commands
- ownership and risk zones
- narrowly useful skills or MCP tools
- explicit read/write and validation boundaries

Do not add fashionable tools or broad prompts without repository evidence.

## Safe update behavior

`/aim configure-agents` must:

1. read `.aim/state.json` only for active-run safety; never store configuration
   there
2. read `aim.roles.yaml`, then `aim.profile.yaml`
3. inspect only freshness-triggered project evidence
4. show proposed role-profile and native-file changes
5. preserve hand-written native overrides unless the user approves replacement
6. update all selected suppliers from the same role intent
7. validate native file presence and main-thread ownership language

If native agents are unavailable, AIM reports the limitation and runs the same
role loop sequentially in the main thread. Gates and quality do not weaken.

## Migration

Existing Personal, Team, and Enterprise flags remain temporary compatibility
inputs for deterministic upgrade planning. They map to storage and sharing
policy; they are not shown as product editions. Existing `aim-planner` and
`aim-builder` helper names map to TDO and Dev and should be replaced with
canonical `aim-tdo` and `aim-dev` specialists during a reviewed upgrade.

Active `.aim/` state is never rewritten by installation or role regeneration.

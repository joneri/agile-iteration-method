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

Before reporting configuration as ready, run the trusted package helper:
`python3 <aim-package>/scripts/aim_engineering.py --repo <project> profiles`.
For standalone configuration when no repo profile is in scope, use `profiles --only roles`; this still checks every declared role-skill binding.
It uses AIM's actual restricted YAML reader, published schemas and safe skill
resolution. A hand-written subset check or successful JSON decoding is not an
equivalent check. Write block-style AIM YAML; JSON object serialization into a
`.yaml` file is not supported by this reader. The command is read-only and does
not certify the factual truth of profile claims.

Use `source: bundled` for each `aim-<role>-engineering` baseline; the package
resolves its own instructions. Do not invent another source label or point a
project binding outside the repository with `../`. A project skill uses a
contained instruction path and its actual availability status. Missing or
invalid profiles remain unready; report the diagnostic and repair the affected
configuration within the existing mandate before claiming successful setup.


Refresh only roles and bindings affected by changed evidence. Reuse unchanged
configuration instead of regenerating it at every Epic. A verified reflection
lesson may justify a small project skill or a revised binding; link its actual
instructions and applicability, preserve the user's overrides, and verify that
the next relevant role can locate it. Adding an expertise label or a skill name
without usable instructions is not a learning outcome.

Every role starts with its bundled `aim-<role>-engineering` skill. The binding
uses `id`, `source` and `status`; optional `path` locates a project skill and
`fallback` describes an unavailable capability. Existing profiles without
bindings remain readable and use the bundled role skill until refreshed.
Project-specific skills are selected from actual available instructions, not
invented skill names. PRD-derived `skillCandidates` are low-confidence hypotheses,
not installed dependencies or verified expertise. See
[Engineering delivery](engineering-delivery.md) for skill selection, runtime
measurement, security applicability and knowledge freshness.

The installer may seed conservative facts from files such as `package.json`,
`pyproject.toml`, `Package.swift`, `Cargo.toml`, and `go.mod`. Detected facts are
marked `needs_calibration`; inference is never presented as verified mastery.
`/aim calibrate-repo` verifies repository facts. `/aim configure-agents`
inspects those facts, proposes role expertise, and regenerates only AIM-owned
native files after showing collisions or user edits. Native files remain thin
loaders: never copy transient implementation status, technology lists or commands
into them. This avoids conflicting snapshots when the profile changes.

For an empty project, use the supplied goal/requirements/PRD to propose provisional
capabilities during startup; do not demand a separate calibration interview for
facts that cannot exist yet. Verify and refine after choosing the stack. The
installer seeds bundled skills for all four roles and bounded root-PRD hints;
the trusted `scripts/aim_engineering.py` helper also accepts explicit requirement
paths. It never executes requirement text or installs packages.

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

Use `adaptive-execution.md` to allocate actual activities and independent review.
An adapter may run independent work sequentially or in parallel according to
ownership, benefit and host capacity. For material changes the default final
Reviewer is a separate permitted agent, not a role switch in the implementer.
A concrete trivial/unavailable exception remains visible; do not let a legacy
serial profile silently override review separation. Respect higher-priority
host/user restrictions and never manufacture another session's evidence.

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

If native agents are unavailable, AIM reports the limitation and retains required
checks in the main thread. Label review as self-review and record the unavailable
exception under `adaptive-execution.md`; do not claim equivalent independence.

## Migration

Existing Personal, Team, and Enterprise flags remain temporary compatibility
inputs for deterministic upgrade planning. They map to storage and sharing
policy; they are not shown as product editions. Existing `aim-planner` and
`aim-builder` helper names map to TDO and Dev and should be replaced with
canonical `aim-tdo` and `aim-dev` specialists during a reviewed upgrade.

Active `.aim/` state is never rewritten by installation or role regeneration.

<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/adapter-entry-model.md
-->

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 adapter entry model

This document is the canonical AIM 2.0 definition of how a user **natively starts
and uses AIM** in each adapter.

AIM keeps **one canonical behavior model** and exposes it through a
supplier-native **AIM skill** in every supported adapter. Canonical AIM behavior lives in
`agile-iteration-method.md`. This document never redefines AIM core,
gate semantics, role order, ownership, or acceptance — it only defines the
user-facing entry surfaces that lead into that one behavior model.

## Product rule

- The user invokes the complete `/aim <intent>` command family through the
  adapter's native AIM skill.
- Internal helper agents remain internal.
- Each adapter uses its native project-agent mechanism for AIM role specialists.
- Adapter packaging supports native use without changing AIM core behavior.
- Every required local document reference resolves after installation.

A user should never have to guess whether to use a command, an agent, a prompt, or
a helper file. Each adapter has exactly one primary skill-led front door.

## Referential closure

An installable adapter package is referentially closed when every canonical
document directly required by its installed instructions is available at the
path those instructions name.

- Codex embeds its required canonical contracts under the installed skill's
  `references/` directory.
- Claude installs the required canonical subset under `docs/workflow/`.
- GitHub Copilot installs the required canonical subset under `docs/workflow/`.
- The full footprint still installs the complete workflow library.

Links inside those canonical documents are further-reading references, not
additional adapter startup dependencies. The installer derives the required
subset from the adapter surfaces it actually installs and fails planning when a
required source document is missing.

## Surface classes

Every adapter file is exactly one of these classes for entry purposes:

1. **User-facing entry surface** — the primary front door a user is meant to use.
2. **Internal helper surface** — supporting mechanics (helpers, prompts, mapping
   layers, internal subagents). Useful, but never the primary front door.
3. **Fallback surface** — the supported way to keep canonical AIM behavior when
   the preferred native surface is unavailable.

## Canonical command family

The canonical AIM command family is defined in
`adapter-command-contract.md`:

- `/aim start`
- `/aim continue`
- `/aim status`
- `/aim validate`
- `/aim help`
- `/aim config`
- `/aim configure-agents`
- `/aim calibrate-repo`
- `/aim remember-repo`
- `/aim forget-repo`
- `/aim upgrade`
- `/aim mode`
- `/aim cost`
- `/aim replan`

If an adapter cannot express these literally, it must still support the same
**intent model** in plain language and preserve the canonical behavior contract.

## Per-adapter native front door

### Codex — user skill, native project agents

- Primary user-facing surface: the installed AIM **skill/package**
  (`../SKILL.md`, installed to
  `~/.agents/skills/agile-iteration-method/`).
- The user runs the AIM command family / intents through that package.
- `/aim <intent>` and explicit `$agile-iteration-method <intent>` select the
  same command semantics.
- Bounded role specialists use project `.codex/agents/aim-*.toml` files.

### GitHub Copilot — project skill, native project agents

- Primary user-facing surface: `.github/skills/aim/SKILL.md`.
- The user requests the `/aim <intent>` family through that project skill.
- `.github/agents/aim.agent.md` is a native orchestration and handoff surface.
- Optional `.github/prompts/` helpers stay secondary.
- **GitHub Copilot is skill-led.**
- PO, TDO, Dev, and Reviewer specialists use repository custom-agent profiles.

### Claude — project skill, native subagents

- Primary user-facing surface: `.claude/skills/aim/SKILL.md`.
- Legacy AIM commands in `.claude/commands/` remain compatibility entrypoints.
- `.claude/agents/` is an internal helper surface, not the primary front door.
- Users normally invoke AIM through commands, not by manually picking a helper agent.
- **Claude is skill-led.**
- Bounded role specialists use project `.claude/agents/aim-*.md` subagents.

## Internal helper surfaces

These are internal helper surfaces only. They may exist and assist, but they must
not be presented as the primary user-facing AIM entrypoint:

- `.claude/agents/` (Claude helper agents)
- `.claude/commands/` (legacy compatibility commands)
- `.github/agents/aim.agent.md` (Copilot orchestration and handoff UX)
- `.github/prompts/` (Copilot prompt helpers)
- adapter-local helper packages and internal mapping layers
- internal subagents (planner/builder/reviewer helpers), which never own `.aim/state.json`

## User guidance — what to do first

A new user should be told exactly one first action per adapter:

- **Codex**: install/enable the user AIM skill, then run `/aim start "EPIC: ..."`
  or explicitly select `$agile-iteration-method` with the same intent.
- **GitHub Copilot**: load the project AIM skill, then request `/aim start "EPIC: ..."`.
- **Claude**: load the project AIM skill, then run `/aim start "EPIC: ..."`.

After starting, the next commands are the same everywhere: `/aim continue`,
`/aim validate`, `/aim help`.

## Native fallback model

If the preferred native surface is unavailable, the supported fallback is **explicit
AIM intent** that preserves the canonical behavior model:

```text
EPIC: <desired outcome>
Mode: Strict
Cost profile: Cost Control
```

or:

```text
EPIC: <desired outcome>
Mode: Auto
Cost profile: Standard
```

Fallback rules:

- the adapter must report the limitation and continue with explicit AIM intent
- the canonical role order, gates, ownership, and acceptance never change
- a reduced visible command set is allowed, but the underlying intent model stays whole
- exact command state effects and per-adapter fallbacks come from
  `adapter-command-contract.md`

## Boundary

This entry model is user-experience packaging. It never overrides:

- `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- Gate A / Gate B / Gate E hard-gate meaning
- Gate C and Gate D as soft gates
- `.aim/state.json` ownership by the main AIM thread
- repo-awareness from `aim.profile.yaml`

If adapter entry guidance conflicts with canonical workflow docs or
`aim.profile.yaml`, escalate instead of guessing.

## Related files

- `agile-iteration-method.md` — canonical AIM core
- `adapter-command-contract.md` — canonical command intents,
  state effects, upgrade behavior, and fallbacks
- `adapter-skill-bootstrap.md` — skill discovery, readiness,
  reload, migration, and first-run receipt
- `source-only/aim-adapter-guidance.md` — adapter mechanics and helper boundaries
- `repo-awareness.md` — progressive loading and adapter boundaries
- `project-agent-configuration.md` — shared role intent and native specialist generation

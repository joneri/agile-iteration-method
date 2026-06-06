> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 adapter entry model

This document is the canonical AIM 2.0 definition of how a user **natively starts
and uses AIM** in each adapter.

AIM keeps **one canonical behavior model** but exposes **adapter-specific native
entry surfaces**. Canonical AIM behavior lives in
`docs/workflow/agile-iteration-method.md`. This document never redefines AIM core,
gate semantics, role order, ownership, or acceptance — it only defines the
user-facing entry surfaces that lead into that one behavior model.

## Product rule

- The user invokes **commands or a native AIM entrypoint**.
- Internal helper agents remain internal.
- Adapter packaging supports native use without changing AIM core behavior.

A user should never have to guess whether to use a command, an agent, a prompt, or
a helper file. Each adapter has exactly one primary front door.

## Surface classes

Every adapter file is exactly one of these classes for entry purposes:

1. **User-facing entry surface** — the primary front door a user is meant to use.
2. **Internal helper surface** — supporting mechanics (helpers, prompts, mapping
   layers, internal subagents). Useful, but never the primary front door.
3. **Fallback surface** — the supported way to keep canonical AIM behavior when
   the preferred native surface is unavailable.

## Canonical command family

The canonical AIM command family is:

- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim validate`
- `/aim help`
- `/aim calibrate-repo`
- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`

If an adapter cannot express these literally, it must still support the same
**intent model** in plain language and preserve the canonical behavior contract.

## Per-adapter native front door

### Codex — skill/package-first

- Primary user-facing surface: the installed AIM **skill/package**
  (`adapters/codex/agile-iteration-method/SKILL.md`, installed to
  `~/.codex/skills/agile-iteration-method/`).
- The user runs the AIM command family / intents through that package.
- **Codex is skill/package-first.**

### GitHub Copilot — agent-first

- Primary user-facing surface: the **AIM agent**
  (`.github/agents/aim.agent.md`), selected in chat.
- The user runs the AIM command family inside that agent.
- Optional `.github/prompts/` helpers stay secondary.
- **GitHub Copilot is agent-first.**

### Claude — command-first

- Primary user-facing surface: AIM **commands** in `.claude/commands/`.
- `.claude/agents/` is an internal helper surface, not the primary front door.
- Users normally invoke AIM through commands, not by manually picking a helper agent.
- **Claude is command-first.**

## Internal helper surfaces

These are internal helper surfaces only. They may exist and assist, but they must
not be presented as the primary user-facing AIM entrypoint:

- `.claude/agents/` (Claude helper agents)
- `.github/prompts/` (Copilot prompt helpers)
- adapter-local helper packages and internal mapping layers
- internal subagents (planner/builder/reviewer helpers), which never own `.aim/state.json`

## User guidance — what to do first

A new user should be told exactly one first action per adapter:

- **Codex**: install/enable the AIM skill, then run `/aim start "EPIC: ..."` (or the
  plain-language equivalent) through the package.
- **GitHub Copilot**: select the AIM agent in chat, then run `/aim start "EPIC: ..."`.
- **Claude**: run the AIM start command from `.claude/commands/`, then continue with
  `/aim continue`.

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

- `docs/workflow/agile-iteration-method.md` — canonical AIM core
- `docs/workflow/aim-adapter-guidance.md` — adapter mechanics and helper boundaries
- `docs/workflow/repo-awareness.md` — progressive loading and adapter boundaries

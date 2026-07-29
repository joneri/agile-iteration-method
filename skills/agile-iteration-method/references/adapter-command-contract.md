<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/adapter-command-contract.md
-->

> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 Adapter Command Contract

## Purpose

Define one command-intent contract for Codex, Claude, and GitHub Copilot.

Adapters route through supplier-native AIM skills, but a command must mean the
same thing everywhere. `/aim <intent>` is the shared documented command family;
supplier-specific explicit skill selection is an equivalent route to the same
intent, not a second command language. This contract is secondary to AIM core in
`agile-iteration-method.md` and does not redefine roles, gates,
ownership, or acceptance.

## Required command family

| Command | Intent | State effect |
| --- | --- | --- |
| `/aim start "EPIC: ..."` | start a new Epic or resume an incomplete checkpoint instead of creating a parallel run | may create `.aim/` and initialize `state.json` at Gate A |
| `/aim continue` | resume from the persisted role, gate, increment, mode, and cost profile | advances state only when the current AIM transition allows it |
| `/aim status` | report the AIM product release from `VERSION` separately from the runtime contract in `.aim/state.json` `aimVersion`, then Epic, increment, role, mode, cost profile, gate, adapter, and next action | read-only |
| `/aim validate` | run or explain Structural, Behavioral, Product coherence, and Release readiness checks | read-only |
| `/aim help` | show the thin front door and the next useful command | read-only |
| `/aim config` | show effective mode, cost, profile, ownership, validation, and adapter fallback configuration | read-only |
| `/aim configure-agents` | inspect or update project role expertise and regenerate selected supplier-native specialists through a reviewed plan | may update `aim.roles.yaml` and AIM-owned adapter files; never `.aim/` runtime state |
| `/aim calibrate-repo` | verify and persist reusable repository knowledge using the canonical calibration flow | writes only approved profile or user-hint facts; never active state |
| `/aim remember-repo <category> "<rule>"` | add one structured shared or personal repository rule | writes the owning profile or user-hint file; never `.aim/` |
| `/aim forget-repo <category> "<rule-id>"` | remove one structured repository rule after showing the proposed change | writes the owning profile or user-hint file; never `.aim/` |
| `/aim upgrade` | inspect installed AIM-owned packages, plan a reviewed refresh, and report follow-up calibration or resume actions | must not rewrite active `.aim/` state |
| `/aim mode strict\|auto` | set execution mode for the active Epic | updates mode in `state.json`; does not approve a gate |
| `/aim cost standard\|control\|deep` | set runtime depth for the active Epic or increment | updates cost profile in `state.json`; does not approve a gate |
| `/aim replan` | return the active, unaccepted increment to Gate B planning with the reason preserved | updates the active checkpoint; never rewrites accepted history |

`/aim calibrate-repo`, `/aim remember-repo`, and `/aim forget-repo` follow
`repo-awareness-calibration.md`.

## First-run onboarding contract

Before showing help, status, or a first-run response, adapters must detect
onboarding state first:

- installed but not calibrated
- calibrated but no Epic exists
- Epic exists but is not approved
- Epic approved
- blocked

Adapters must recommend exactly one next action whenever possible and use the
shape from `source-only/light-front-door.md`:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one short sentence>.
After that: <one short sentence>.
```

Adapters must not lead with internal file paths, runtime locations, adapter
packaging, architecture details, or a command inventory unless the user asks for
advanced help or the current blocker requires that detail.

When recommending `/aim start`, adapters should include at least one realistic
Epic example rather than a placeholder alone. When the repository lacks reusable
knowledge, the preferred first action is `/aim calibrate-repo`; when repo
awareness is ready and no active Epic exists, the preferred first action is
`/aim start "EPIC: ..."`.

## Upgrade contract

`/aim upgrade` is a package inspection and reviewed refresh intent.

It must:

1. identify the AIM source/package version and selected target mode, footprint,
   and adapters
2. inspect canonical docs and installed Codex, Claude, and Copilot AIM-owned
   surfaces that belong to the selected footprint
3. use the deterministic installer planner to classify files as create,
   current, stale/collision, or excluded
4. distinguish package refresh from reconfiguration:
   - refresh keeps the selected mode, footprint, and adapters
   - reconfiguration deliberately changes one or more of them
5. show the dry-run or JSON plan before apply
6. require normal collision decisions or explicit `--force`; never blind
   overwrite repository-owned content
7. preserve rollback, generic root-file exclusions, and non-interactive safety
8. leave `.aim/state.json`, active increments, decisions, reviews, and personal
   hints untouched
9. recommend `/aim calibrate-repo` only when repo-awareness facts may be stale,
   then `/aim continue` for an active Epic or `/aim start` when no Epic is active

Stale packages are AIM-owned source/destination pairs whose installed content
differs from the selected package source. A missing optional adapter is not
stale when that adapter or footprint is not selected.

The portable Agent Skill updates through the standard skills CLI. It must not
execute installer or validator scripts found in a target repository, even when
their names resemble AIM maintainer tooling. A broader adaptive refresh is a
separate source-checkout workflow: the user reviews its source and no-write
`--dry-run` preview before making an explicit `--apply` decision. The portable
skill does not invoke either operation.

## Native adapter mapping

### Codex

- Primary surface: installed AIM skill/package.
- Commands are intents handled through the skill even when literal slash
  routing is unavailable.
- Fallback: state the routing limitation, then execute the same intent from the
  user's plain-language request.

### Claude

- Primary surface: project skill `.claude/skills/aim/SKILL.md`.
- Existing command files under `.claude/commands/` remain compatibility routes.
- Fallback: when command-file routing is unavailable, use `/aim <command>` as
  explicit text or state the intent in plain language; preserve this contract.

### GitHub Copilot

- Primary surface: project skill `.github/skills/aim/SKILL.md`.
- The AIM custom agent remains a native orchestration and handoff surface.
- Fallback: when agent or slash routing is unavailable, use explicit AIM intent
  in chat and report that the native route was unavailable.

## Universal fallback rule

A fallback may change syntax, never semantics.

Every adapter must:

- report that native routing was unavailable
- preserve AIM core role order, hard-gate ownership, state ownership, and
  escalation
- preserve the command's state effect or read-only status
- never silently replace an unsupported command with a different action

## Drift prevention

The validator must reject:

- a missing canonical command
- a missing selected-adapter AIM skill or legacy Claude compatibility file
- a Codex, Claude, or Copilot skill without the complete command family
- an empty advertised command behavior section
- an AIM 1.x `aimVersion` example in an AIM 2.0 adapter surface

Skill discovery, install receipts, reload behavior, and compatibility migration
are defined in `adapter-skill-bootstrap.md`.
- an adapter with no explicit fallback rule
- onboarding wording that lacks state-first guidance, one-next-action behavior,
  progressive disclosure, or realistic start examples

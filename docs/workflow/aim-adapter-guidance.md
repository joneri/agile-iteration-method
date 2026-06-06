> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.

# AIM adapter guidance

This document defines optional adapter-specific AIM entrypoints and helper boundaries.

Canonical AIM behavior lives under `docs/workflow/`.
Adapters expose that behavior without redefining AIM core, runtime ownership, gates, role order, or acceptance.

## Purpose

Keep adapter guidance secondary, optional, and active-adapter-only.

Use this file when changing:
- adapter entrypoints
- optional helper file structure
- adapter parity labels
- Codex, Copilot, or Claude Code capability notes
- fallback behavior for adapter-specific tools

## Native entry model

The canonical, user-facing native entry model lives in
`docs/workflow/adapter-entry-model.md`. It defines the per-adapter front door:

- Codex is **skill/package-first**
- GitHub Copilot is **agent-first**
- Claude is **command-first** (with `.claude/agents/` as an internal helper surface)

This adapter-guidance file covers adapter mechanics and helper boundaries; the
entry-model doc owns which surface is the user-facing front door.

## Canonical boundary

Adapter layers may improve UX and discoverability, but they must preserve:
- `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- hard-gate meaning at Gate A, Gate B, and Gate E
- Gate C and Gate D as soft gates
- `.aim/state.json` ownership by the main AIM thread
- repo-awareness from `aim.profile.yaml`
- sequential fallback when controlled parallelism is unavailable

If adapter guidance conflicts with canonical workflow docs or `aim.profile.yaml`, escalate instead of guessing.

## AIM 2.0 low-footprint adapter expectations

AIM 2.0 introduces a low-footprint adoption model without changing AIM core.

Adapters should treat these as separate concerns:

- AIM runtime: adapter or tool behavior that runs the AIM loop
- AIM repo profile: reusable repository knowledge such as commands, conventions, risk zones, ownership boundaries, validation paths, and freshness markers
- AIM working state: active Epic, Done Increment, gate, handoff, decision, and review state for the current work
- AIM docs: reference material, not mandatory payload copied into every repository

The main AIM thread still owns `.aim/state.json`, gate progression, and acceptance decisions.
Repo profile reuse must not move that authority into helper files, subagents, or adapter metadata.

### Adoption footprints

Adapters should support or gracefully describe these adoption depths:

- Personal AIM:
  - freedom mode with no Team or Enterprise sharing restrictions
  - runtime may come from the tool, local adapter, or repo package
  - repo profile may be local or committed by user choice
  - working state may be local, ignored, or committed by user choice
  - full embedded docs and adapter surfaces are allowed
- Team AIM:
  - tiny committed repo profile or pointer
  - shared repo adaptation by intentional team choice
  - working state local by default unless the team explicitly chooses otherwise
  - full AIM docs linked or installed, not copied wholesale by default
- Enterprise AIM:
  - safe isolation by default
  - local/private AIM internals unless sharing is explicitly approved
  - future organization-managed profile or policy source may be used
  - optional repository pointer to managed policy
  - must not be required for Personal or Team AIM
- Full embedded AIM:
  - full docs and adapter helpers committed by explicit repo-owner choice
  - remains valid for AIM itself, templates, training repos, and public examples

### Locality-first startup

When AIM 2.0 profile support exists, adapters should load context in this order:

1. active working state
2. reusable repo profile, preferably root `aim.profile.yaml`
3. directly affected files
4. nearest package, service, or module metadata
5. nearest build, test, lint, or validation commands
6. short authoritative docs named by the profile
7. broader repository docs only when risk or missing evidence requires them

Adapters should report when they cannot preserve this order and should fall back safely.

### Profile-first adapter behavior

Adapters that can read files should support both Personal and Team profile sources.

Personal AIM local-hints option:

```text
~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
```

Team AIM default:

```text
aim.profile.yaml
```

On `/aim start`, `/aim continue`, `/aim status`, `/aim validate`, `/aim calibrate-repo`, or equivalent adapter entrypoints:

1. read `.aim/state.json` first when it exists
2. read root `aim.profile.yaml` as the shared repo-awareness baseline when it exists
3. apply compatible Personal AIM profile hints when they exist
4. use profile facts to select directly affected areas, nearest commands, short authoritative docs, and avoid-by-default context
5. run or report validator readiness when available
6. read broader AIM docs, adapter docs, or repo-wide context only when the current state, risk, missing evidence, or user request requires it

Calibration, remember, and forget commands use `docs/workflow/repo-awareness-calibration.md`.

When Personal and Team profiles both exist, the Team profile is the shared baseline.
Personal profile facts may narrow local startup, but must not silently contradict shared commands, ownership, risk, or policy.

The visible startup or Gate B summary should state whether the profile was reused, which locality it selected, and which broader docs were intentionally avoided.
Use this compact shape when profile reuse affects context selection:

```text
Profile source: <personal hints path and/or aim.profile.yaml> (<readiness>)
Layering: <personal narrows team baseline | team profile baseline | personal profile only | no profile source>
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <area>
Avoided context: <docs/scans avoided>
Expansion reason: <none or reason>
Cheap validation first: <command>
```

When a repository ships `scripts/validate_aim_runtime.py`, adapters may use its `AIM 2.0 profile-source summary` output as the generated summary rather than rebuilding the summary themselves.

The profile cannot override AIM core, gate semantics, `.aim/state.json`, current repository evidence, or escalation rules.

### Profile reuse and freshness

Adapters may reuse repo profile facts across branches and sessions when:

- the repo identity matches
- the profile owner or source is clear
- branch or base commit differences are understood
- no relevant freshness trigger has fired
- the active work is inside a known locality boundary
- the selected cost profile allows reuse

Adapters should refresh or revalidate the smallest affected area when:

- lockfiles changed
- package scripts changed
- build or test tooling changed
- ownership metadata changed
- relevant docs changed
- the profile is stale under team policy
- the work crosses risk, ownership, deployment, migration, security, data correctness, or public API boundaries

If profile reuse conflicts with trust, trust wins and AIM must escalate instead of guessing.

### Cost observability

Adapters should make the main profile-related cost drivers visible without exact price accounting:

- whether a profile was reused
- scan depth used
- why any refresh was needed
- whether broader docs were avoided
- expected review depth
- subagent policy or sequential fallback

This preserves the AIM 2.0 cost story while extending it to install, startup, scanning, resume, profile refresh, and branch switching.

## Optional adapter layers

Copilot layer:
- documented in `docs/workflow/copilot-layer.md`
- uses `.github/agents/aim*.agent.md` as native Copilot custom-agent files
- uses `.github/prompts/` for optional Copilot-style prompt helpers

Claude Code layer:
- uses `.claude/commands/` for AIM command entrypoints
- uses `.claude/agents/` for AIM-aligned Claude helpers
- does not require a root `CLAUDE.md` AIM bridge

Codex layer:
- uses the installed AIM skill or explicit AIM intent plus the available Codex tool surface
- may use the shipped Codex skill at `adapters/codex/agile-iteration-method/SKILL.md` as the canonical copyable launcher/runtime guide
- may expose bounded subagent capability where runtime support exists
- treats `/aim`, when available, as a launcher surface rather than the source of method authority
- on the first AIM command in Codex, should make the bundled skill path and local install target visible so new and existing users know which skill to use

## Quick start phrases

These phrases are valid adapter entrypoint hints when the matching layer supports them:
- `Install AIM`
- `Start working according to AIM`
- `/aim start "EPIC: ..."`
- `Starta en AIM-loop med denna EPIC: ...`

Transport shortcuts and command surfaces are adapter UX.
They do not define the AIM checkpoint contract.

## Optional adapter file structure

Codex skill:
- `adapters/codex/agile-iteration-method/SKILL.md`

Copilot prompt helpers:
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`

Claude Code:
- `.claude/commands/`
- `.claude/agents/`

Installation boundary:
- `adapters/codex/agile-iteration-method/SKILL.md` is the shipped Codex convenience layer; copy it into the local Codex skills directory when `/aim` support is wanted.
- The local Codex target is `~/.codex/skills/agile-iteration-method/SKILL.md`; if that file is missing or stale, Codex may continue from explicit AIM intent and canonical workflow docs but should surface the install command before relying on `/aim` routing.
- `.github/agents/aim*.agent.md` are Copilot-native AIM entrypoints.
- `.github/prompts/` are optional Copilot-style prompt helpers, not the canonical AIM contract.
- `.claude/` provides Claude-native AIM entrypoints without a generic root bridge.

## Parity classification

Use these labels when comparing adapter behavior:
- `shared`
  - same conceptual behavior and same runtime contract across supported adapters
- `shared_with_adapter_differences`
  - same runtime contract, but different entrypoints, tools, or interface mechanics
- `codex_only`
  - currently documented only for the Codex adapter
- `copilot_only`
  - currently documented only for the Copilot adapter
- `claude_code_only`
  - currently documented only for the Claude Code adapter
- `planned`
  - intentionally not yet treated as a supported shared capability

## Adapter rules

Codex:
- uses the installed AIM skill or explicit AIM intent plus the available Codex tool surface
- uses the shipped `agile-iteration-method` skill as the recommended `/aim` launcher when the skill is installed and enabled
- reports bundled-skill install status during first-run AIM commands, validation, status, config, and install flows
- may expose bounded subagent capability where runtime support exists
- may expose adapter-specific tools such as MCP-backed browser automation

Copilot:
- uses `.github/agents/aim*.agent.md` as native Copilot AIM packaging
- uses `.github/prompts/` as optional Copilot command-entry helpers
- may differ in command routing, handoff UI, and prompt-file availability
- must still preserve the shared runtime contract and repo-aware policy interpretation

Claude Code:
- may expose repository-defined entrypoints through `.claude/commands/` and helper agents through `.claude/agents/`
- may use bounded Claude helpers for analysis, discovery, verification, or option generation only
- must still preserve the shared runtime contract and repo-aware policy interpretation

Fallback rule:
- if a capability is not available in one adapter, the adapter must preserve the intended policy, report the limitation, and fall back safely instead of silently redefining the method
- regardless of parity level, only the main AIM thread may own `.aim/state.json`, gate progression, or acceptance decisions

## Related files

- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-awareness.md`
- `docs/workflow/copilot-layer.md`
- `aim.profile.yaml`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`

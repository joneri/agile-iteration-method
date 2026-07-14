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

- Codex uses a user-scoped AIM skill
- GitHub Copilot uses a project AIM skill plus native custom agents
- Claude uses a project AIM skill plus native subagents

The shared architecture is skill-led. Legacy Claude command files and the
Copilot orchestrator remain compatibility or native orchestration surfaces; they
do not own separate command semantics.

The canonical command intent, state-effect, upgrade, and fallback contract is
`docs/workflow/adapter-command-contract.md`. Adapter files may choose native
syntax and packaging, but they must preserve that command meaning.

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

## AIM 2.0 distribution expectations

AIM 2.0 is one product available through a portable public Agent Skill and one
adaptive guided installer. Both preserve AIM core. Older Personal, Team, and
Enterprise labels are compatibility inputs, not separate products or current
adapter behavior models.

The public skill is the normal portable entry point. Its onboarding guidance
must not pretend that repository configuration already exists: users calibrate,
then configure project specialists when wanted, before starting the first Epic.
The adaptive installer may seed those files in one reviewed setup flow.

Adapters should treat these as separate concerns:

- AIM runtime: adapter or tool behavior that runs the AIM loop
- AIM repo profile: reusable repository knowledge such as commands, conventions, risk zones, ownership boundaries, validation paths, and freshness markers
- AIM working state: active Epic, Done Increment, gate, handoff, decision, and review state for the current work
- AIM docs: reference material, not mandatory payload copied into every repository

The main AIM thread still owns `.aim/state.json`, gate progression, and acceptance decisions.
Repo profile reuse must not move that authority into helper files, subagents, or adapter metadata.

### Installation policy layers

Adapters should apply the same four layers in every repository:

- shared method and runtime contract
- repo-owned `aim.profile.yaml` and `aim.roles.yaml`
- supplier-native role files for each selected adapter
- user-local hints or organization policy when present

The installer chooses the smallest complete file set for the selected adapters.
Repository owners may still choose local, shared, external, or fully embedded
storage policies, but those are footprint decisions rather than product editions.

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

Adapters that can read files should support shared repo profiles plus optional
user-local hints.

User-local hints option:

```text
~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
```

Shared repository default:

```text
aim.profile.yaml
```

On `/aim start`, `/aim continue`, `/aim status`, `/aim validate`, `/aim calibrate-repo`, or equivalent adapter entrypoints:

1. read `.aim/state.json` first when it exists
2. read root `aim.profile.yaml` as the shared repo-awareness baseline when it exists
3. apply compatible user-local profile hints when they exist
4. use profile facts to select directly affected areas, nearest commands, short authoritative docs, and avoid-by-default context
5. run or report validator readiness when available
6. read broader AIM docs, adapter docs, or repo-wide context only when the current state, risk, missing evidence, or user request requires it

Calibration, remember, and forget commands use `docs/workflow/repo-awareness-calibration.md`.
They must never store or cite durable repo-awareness under `.aim/`. Reading
`.aim/state.json` to resume active work is allowed, but `.aim/reviews`,
`.aim/increments`, `.aim/decisions`, `.aim/archive`, and other runtime artifacts
must not become long-lived repository knowledge sources. When a remembered fact
is too large for a short profile entry, adapters should create or update a
static memory document under `docs/features/`, `docs/workflow/`,
`docs/architecture/`, or another repo-configured stable docs path, then reference
that static source from `aim.profile.yaml`.

When both sources exist, `aim.profile.yaml` is the shared baseline. User-local
facts may narrow local startup, but must not silently contradict shared commands,
ownership, risk, or policy.

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
- documented in `docs/workflow/adapter-entry-model.md`
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
- The public Codex skill installs with `npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent codex --yes`.
- The local Codex target is `~/.agents/skills/agile-iteration-method/SKILL.md`; if that file is missing or stale, Codex may continue from explicit AIM intent and canonical workflow docs but should surface the public install or update command before relying on `/aim` routing.
- The adaptive installer remains the path for a reviewed repository footprint, `aim.roles.yaml`, and supplier-native project specialists.
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
- `docs/workflow/adapter-command-contract.md`
- `docs/workflow/adapter-entry-model.md`
- `docs/workflow/repo-awareness.md`
- `docs/workflow/adapter-entry-model.md`
- `aim.profile.yaml`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`

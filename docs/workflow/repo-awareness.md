# AIM 2.0 Repo Awareness

## Purpose

Define the canonical repo-awareness and progressive-loading model for AIM 2.0.

This document makes AIM independent of generic root instruction files.

## Primary source

The primary shared repo-awareness source is:

```text
aim.profile.yaml
```

It is the first repository-owned source AIM reads after active runtime state.

The profile contains reusable repository facts such as:

- locality and package boundaries
- validation commands
- ownership and risk zones
- freshness triggers
- short authoritative repo docs
- deployment, migration, and security constraints
- context to avoid by default

It must not contain AIM core behavior, active Epic state, gate state, review state, or acceptance decisions.

## Personal local profile

Personal AIM may use:

```text
~/.aim/profiles/<repo-fingerprint>/profile.yaml
```

This is an optional local reuse layer.
It may narrow startup or remember local preferences, but it does not replace or override a shared `aim.profile.yaml`.

When both exist:

1. read active `.aim/state.json`
2. read `aim.profile.yaml` as the shared repository baseline
3. apply compatible Personal profile hints
4. inspect directly affected files
5. expand only when evidence, risk, or the active command requires it

## Generic root files

AIM treats generic root files as outside the AIM architecture.
AIM core ignores these as AIM control surfaces:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`

If a target repository contains them, they remain repository-owned files.
AIM may encounter ordinary repository instructions through the host platform, but AIM installation, core behavior, repo-awareness, and validation do not require or modify them.

`CONTRIBUTING.md` has one narrower exception: the file in the AIM source repository may be read by people maintaining AIM itself.
In every target repository, AIM must never copy, create, modify, require, or read `CONTRIBUTING.md`.

## Optional adapter policy

Adapter-specific surfaces are optional and secondary:

| Adapter | Native entrypoint | Optional policy/helpers |
| --- | --- | --- |
| Codex | installed AIM skill or explicit AIM intent | `adapters/codex/agile-iteration-method/` |
| GitHub Copilot | `.github/agents/aim*.agent.md` | `.github/prompts/` |
| Claude | `.claude/agents/aim.md` or `.claude/commands/` | other `.claude/` helpers |

Adapter surfaces:

- load only for the active adapter
- may define command routing and platform mechanics
- may consume `aim.profile.yaml`
- must not redefine AIM core, gate meaning, ownership, or acceptance

## Load order

Load the smallest useful context in this order:

1. `.aim/state.json` when an AIM run exists
2. `aim.profile.yaml` when present
3. compatible Personal profile hints when present
4. directly affected files and nearest metadata
5. the nearest validation command
6. canonical AIM workflow docs required by the current role, gate, command, or risk
7. active-adapter policy only when adapter mechanics matter
8. broader repository docs only when evidence is missing or risk requires expansion

Do not preload the full workflow family.

## Native adapter continuity

### Codex

- Start with `/aim start "EPIC: ..."` when the AIM skill is installed.
- Explicit plain-language AIM intent remains a fallback.
- The skill loads active state, `aim.profile.yaml`, and only the required workflow docs.

### GitHub Copilot

- Select the shipped `aim` agent or use the matching prompt helper.
- The agent reads active state and `aim.profile.yaml`.
- Other `.github` helpers are loaded only for Copilot-specific command behavior.

### Claude

- Use the shipped `.claude/agents/aim.md` or `.claude/commands/` entrypoint.
- Explicit `EPIC: ...` intent remains a fallback.
- Claude helpers read active state and `aim.profile.yaml`; no root `CLAUDE.md` AIM bridge is required.

## Failure behavior

- Missing `aim.profile.yaml`: continue with directly affected files and nearest metadata; report that no shared profile exists.
- Contradictory profile and repository evidence: trust current evidence and refresh or escalate.
- Missing adapter helper: use explicit AIM intent when the host permits it.
- Adapter helper contradicts canonical workflow docs: stop and escalate.

## Related files

- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/personal-local-profile-storage.md`
- `docs/workflow/aim-adapter-guidance.md`
- `aim.profile.yaml`
- `scripts/validate_aim_runtime.py`

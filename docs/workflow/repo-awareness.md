# AIM 2.0 Repo Awareness

## Purpose

Define the canonical repo-awareness and progressive-loading model for AIM 2.0.

This document makes AIM independent of generic root instruction files.

## Primary source

The primary shared repo-awareness source for Team or explicit repo opt-in is:

```text
aim.profile.yaml
```

Enterprise external mode uses:

```text
~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml
~/.aim/repo-awareness/<repo-fingerprint>/docs/
```

It is the first external durable source AIM reads after active runtime state.
`aim.profile.yaml` remains the first repository-owned source when it exists.

The profile contains reusable repository facts such as:

- locality and package boundaries
- validation commands
- ownership and risk zones
- freshness triggers
- short authoritative repo docs
- deployment, migration, and security constraints
- context to avoid by default

It must not contain AIM core behavior, active Epic state, gate state, review state, or acceptance decisions.

`.aim/` is AIM runtime state and trace history. It may be read to resume or
audit the active AIM loop, especially `.aim/state.json`, but it must not be the
source of durable repo-awareness. Stable repo-awareness must not cite
`.aim/reviews`, `.aim/increments`, `.aim/decisions`, `.aim/archive`, or other
runtime artifacts as maintained repository knowledge. If a runtime artifact
contains knowledge worth preserving, normalize that knowledge into
`aim.profile.yaml`, Enterprise external memory, Personal hints, or a static
documentation file under the selected durable memory/docs path, then reference
that static source.

The structural source of truth is `schemas/aim-repo-profile.schema.json`.
See `docs/workflow/repo-profile-schema.md` for schema versions, validation
ownership, and migration rules.

## Personal local profile

Personal AIM may use:

```text
~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml
```

This is an optional local reuse layer.
It may narrow startup or remember local preferences, but it does not replace or override a shared `aim.profile.yaml`.
Stable repo-awareness must never use a path under `.aim/`.

When both exist:

1. read active `.aim/state.json`
2. read Enterprise external memory when Enterprise external mode is active
3. read `aim.profile.yaml` as the shared repository baseline when present
4. apply compatible Personal profile hints
5. inspect directly affected files
6. expand only when evidence, risk, or the active command requires it

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
- may consume `aim.profile.yaml` or Enterprise external memory
- must not redefine AIM core, gate meaning, ownership, or acceptance

## Load order

Load the smallest useful context in this order:

1. `.aim/state.json` when an AIM run exists
2. Enterprise external memory when Enterprise external mode is active
3. `aim.profile.yaml` when present
4. compatible Personal profile hints when present
5. directly affected files and nearest metadata
6. the nearest validation command
7. canonical AIM workflow docs required by the current role, gate, command, or risk
8. active-adapter policy only when adapter mechanics matter
9. broader repository docs only when evidence is missing or risk requires expansion

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

## Calibration and memory

Use `/aim calibrate-repo` to bootstrap or refine repository knowledge through the canonical cheap-first flow.
An ordinary AIM Epic whose goal is to verify and refine repo-awareness follows the same contract and produces the same profile shape.

Short, atomic durable facts belong directly in the active memory index:
`aim.profile.yaml` for Team/repo opt-in, or
`~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml` for Enterprise external.
Larger repo memory belongs in stable documentation and should be referenced from
that index with a short summary and loading rule. Valid static memory locations
include:

- `docs/features/`
- `docs/workflow/`
- `docs/architecture/`
- another stable docs path explicitly configured by the repository
- `~/.aim/repo-awareness/<repo-fingerprint>/docs/` for Enterprise external

Do not use `.aim/` runtime artifacts as long-lived memory documents.

Use:

- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`

for persistent structured updates.
See `docs/workflow/repo-awareness-calibration.md` for readiness, confidence, categories, document loading, installer bootstrap, and summary behavior.

## Related files

- `schemas/aim-repo-profile.schema.json`
- `schemas/aim-personal-hints.schema.json`
- `docs/workflow/repo-profile-schema.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/personal-local-profile-storage.md`
- `docs/workflow/repo-awareness-calibration.md`
- `docs/workflow/aim-adapter-guidance.md`
- `aim.profile.yaml`
- `scripts/validate_aim_runtime.py`

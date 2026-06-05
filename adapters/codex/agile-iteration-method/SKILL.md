---
name: agile-iteration-method
description: Run Agile Iteration Method (AIM) 2.0 workflows in Codex or another compatible adapter. Use when the user asks to start, continue, resume, validate, install, troubleshoot, control cost, select Cost Control or Deep, or operate an AIM loop; uses `/aim`-style commands; provides an EPIC, mode, or cost profile; mentions AIM, Agile Iteration Method, Gate A-E, Done Increment, PO, TDO, Dev, Reviewer, Cost Control, Standard, or Deep; or wants AI delivery work governed by AIM 2.0 roles, gates, `.aim` runtime state, repo-aware policy, adapter fallback rules, and runtime-depth profiles.
---

# Agile Iteration Method

Use this skill to operate AIM 2.0 as a continuous role-and-gate delivery loop.
AIM is `core + runtime + repo-aware policy + platform adapters`; the repository remains the source of truth and this skill is the launcher/runtime guide.

Attribution: based on Agile Iteration Method 2.0 by Jonas Eriksson, licensed as documentation under CC BY 4.0. This skill adapts the method into Codex skill form.

## First Response

1. Detect the repository root.
2. Detect or create `.aim` before starting or resuming an AIM run.
3. Read `.aim/state.json` first when it exists.
4. If `.aim/state.json` describes an incomplete Epic, resume that checkpoint instead of starting a new Epic.
5. Read the Personal AIM local profile next when it exists: `~/.aim/profiles/<repo-fingerprint>/profile.yaml`, or ignored fallback `.aim/profile.yaml`.
6. Read `aim.profile.yaml` after the personal profile when it exists, treating it as the shared Team AIM baseline.
7. Use profile facts to choose locality, validation commands, short authoritative docs, risk zones, freshness triggers, and context to avoid before reading broader docs.
8. Load only the additional repo-aware AIM context needed for the current state, role, gate, cost profile, and command:
   `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, `.github/agents/aim*.agent.md`, then active adapter helpers such as `.github/prompts/*`, `CLAUDE.md`, `.claude/agents/*`, and `.claude/commands/*`.
9. Read `CONTRIBUTING.md` first when the target repository is the AIM repository itself and a change is being made.
10. Default to `Mode: Strict` unless the user explicitly chooses `Mode: Auto`.
11. Default to `Cost profile: Standard` unless the user explicitly chooses `Cost Control` or `Deep`.
12. Start visible AIM phases with exactly `Role: PO`, `Role: TDO`, `Role: Dev`, or `Role: Reviewer`, and show `Mode: Strict` or `Mode: Auto`.
13. Show `Cost profile` when it is not `Standard` or when resource use is part of the user's request.
14. Keep the public front door thin: route first to start, continue, or validate before explaining the full method.

Treat unnecessary broad context loading, long low-risk markdown artifacts, repeated major-doc rereads, and context-hog files as budget bugs.
When a Personal or Team profile is present, report whether it was reused before broader docs. Profiles can guide locality and validation, but they cannot override AIM core, `.aim/state.json`, Team policy, gate ownership, escalation, or current repository evidence.
When profile reuse affects startup or Gate B, include this compact profile-source summary:

```text
Profile source: <personal profile path and/or aim.profile.yaml> (profile_ready)
Layering: <personal narrows team baseline | team profile baseline | personal profile only | no profile source>
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <area>
Avoided context: <docs/scans avoided>
Expansion reason: <none or reason>
Cheap validation first: <command>
```

When the repository provides `scripts/validate_aim_runtime.py`, use its `AIM 2.0 profile-source summary` output as the generated startup summary.

Stop and ask only when an escalation condition applies: scope expansion beyond Gate B, unclear or contradictory Epic intent, unmet acceptance checks without new assumptions, trust/data/user-facing risk, missing required files/APIs/data, or contradictory repo policy.

## Codex Skill Install Check

When the user runs AIM in Codex for the first time in a repository, make the bundled skill path obvious before continuing:

- repo-bundled skill: `adapters/codex/agile-iteration-method/SKILL.md`
- local Codex install path: `~/.codex/skills/agile-iteration-method/SKILL.md`

If the local Codex skill is missing or appears older than the repo-bundled skill, state that AIM can continue from the repository contract for this run, but `/aim` works best after installing the bundled skill:

```sh
mkdir -p ~/.codex/skills/agile-iteration-method
cp -R adapters/codex/agile-iteration-method/. ~/.codex/skills/agile-iteration-method/
```

The Codex skill package may include app metadata such as `agents/openai.yaml`. Copy the whole directory, not only `SKILL.md`, so the Codex skill picker shows the current AIM version and description.

For `Install AIM`, `/aim validate`, `/aim status`, `/aim config`, and first-run `/aim start` or `/aim continue`, include this install status in the visible output when Codex is the active platform.
Do not treat a missing local skill as a blocker when the repository already contains the AIM contract; report the fallback and continue unless another escalation condition applies.

## Commands

Treat these as AIM intents when the current adapter supports them or when the user writes the equivalent in plain language:

- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim mode strict|auto`
- `/aim cost standard|control|deep`
- `Install AIM`
- `Start working according to AIM`

If a slash command surface is unavailable, perform the equivalent workflow directly and mention the fallback briefly.

## Thin Front Door

When the user asks how to begin, help, or what AIM should do next, show only the first useful choice by default:

- start new work: `/aim start "EPIC: ..."`
- continue current work: `/aim continue`
- check setup: `/aim validate`

For ordinary low-risk work, suggest this start shape:

```text
/aim start "EPIC: <desired user outcome>"
Mode: Strict
Cost profile: Cost Control
```

Do not explain adapter layering, every gate, or every runtime artifact unless the user asks for deeper help or the task needs that context.

## Runtime Workflow

Use the shared bootstrap sequence:

1. Detect repo root.
2. Detect or create `.aim`.
3. Read `.aim/state.json` first when it exists.
4. Resume the active checkpoint or initialize a new Epic.
5. Read `aim.profile.yaml` when present and use it before broader docs to select locality, commands, short docs, risk zones, freshness checks, and avoid-by-default context.
6. Load and normalize only the additional repo-aware context needed for the current state, command, and risk.
7. Resolve execution mode.
8. Resolve cost profile.
9. Resolve platform capability and repo-policy limits.
10. Enter the role sequence.

Only the main AIM thread may write `.aim/state.json`, advance gates, change role, change increment status, or accept/complete an Epic. Subagents, when explicitly allowed by the host and repo policy, may only produce scoped analysis in allowed locations and never own runtime state.

## Role Loop

Run every Done Increment in this order:

`PO -> TDO -> Dev -> Reviewer -> TDO -> PO`

Canonical roles are only `PO`, `TDO`, `Dev`, and `Reviewer`. Map aliases explicitly: `Planner` to `TDO`, `Builder` to `Dev`.

Hard gates:

- Gate A: Epic ready. Approval is meaningful.
- Gate B: Done Increment spec ready. Approval is meaningful.
- Gate E: Increment acceptance and Epic continuation/closure. Approval is meaningful.

Soft gates:

- Gate C: implementation ready.
- Gate D: review findings ready.

Report Gate C and Gate D, but do not pause there unless an escalation condition applies. Gate D must never ask for approval; it surfaces findings, risks, and manual verification steps.

## Done Increment Discipline

At Gate B, propose exactly one Done Increment that is a simplified version of the whole Epic, not a polished part of a missing whole.

Before development, confirm the increment:

- embodies meaningful Epic value end to end
- includes data correctness, presentation, user-facing behavior, and safety/failure behavior where relevant
- can be demoed as the product behavior
- would make sense to a user without future increments
- is small by behavioral scope, not by minimizing file count
- lists exact planned files and responsibility boundaries

If any answer is no, bundle or redefine the increment before proceeding.

AIM allows focused files, components, hooks, helpers, domain modules, services, or short docs when they preserve the approved behavior and reduce future context load. Do not create giant mixed-responsibility files just to keep the diff small. Do not split arbitrarily by line count.

## Cost Profiles

Cost profile controls runtime depth, not approval semantics.

- `Standard`: default AIM with progressive context loading and compact gates unless risk requires detail.
- `Cost Control`: use for low-risk, reversible cleanup, docs maintenance, and narrow fixes. Preserve roles, gates, and escalation while using narrow context, no subagents by default, concise checkpoints, and short trace artifacts.
- `Deep`: use for trust-sensitive, data correctness, public API, migration, deployment, security, or broad method changes. Broader inspection and stronger review evidence are expected.

Escalate from `Cost Control` to `Standard` or `Deep` when trust, data correctness, user-facing meaning, migration, deployment, security, API, unclear acceptance, or scope risk appears.

## Visible Output

Keep output step-aware rather than template-heavy.

Every hard-gate checkpoint must make clear:

- what decision is proposed or was made
- what will change or changed
- exact files planned or touched
- how the user should evaluate the step

Use `approve` and `change: ...` as transport shortcuts at hard gates, but in Strict mode continue through the full loop unless an escalation condition says to stop. In Auto mode, report hard gates without pausing between increments; require a final full-review pause before Epic completion.

## State And Validation

The official `.aim` contract requires:

- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

Optional runtime artifacts:

- `.aim/handoffs/`
- `.aim/logs/`
- `.aim/archive/`
- `.aim/runtime-context.md`
- `.aim/analysis/`

For `/aim validate`, resume checks, and troubleshooting, inspect the required `.aim` artifacts and repository AIM files directly unless the repository provides a validator script.
Validation reports should classify the result as `healthy`, `recoverable`, `blocked`, or `contradictory`, name the failed artifact or rule, and avoid mutating runtime state.

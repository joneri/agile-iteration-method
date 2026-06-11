---
name: agile-iteration-method
description: Run Agile Iteration Method (AIM) 2.0 workflows in Codex or another compatible adapter. Use when the user asks to start, continue, resume, validate, install, troubleshoot, control cost, select Cost Control or Deep, or operate an AIM loop; uses `/aim`-style commands; provides an EPIC, mode, or cost profile; mentions AIM, Agile Iteration Method, Gate A-E, Done Increment, PO, TDO, Dev, Reviewer, Cost Control, Standard, or Deep; or wants AI delivery work governed by AIM 2.0 roles, gates, `.aim` runtime state, repo-aware policy, adapter fallback rules, and runtime-depth profiles.
---

# Agile Iteration Method

Use this skill to operate AIM 2.0 as a continuous role-and-gate delivery loop.
AIM is `core + runtime + repo-awareness + platform adapters`; canonical behavior lives under `docs/workflow/` and this skill is the Codex launcher/runtime guide.

Attribution: based on Agile Iteration Method 2.0 by Jonas Eriksson, licensed as documentation under CC BY 4.0. This skill adapts the method into Codex skill form.

## Native Entry Surface

In Codex, AIM is **skill/package-first**: this installed AIM skill/package is the
primary user-facing front door, and the AIM command family and intents run through
it. If the skill is unavailable, fall back to explicit AIM intent while preserving
the canonical behavior model.
The package-local cross-adapter entry model is `references/adapter-entry-model.md`.

## First Response

Detect onboarding state first, then recommend exactly one next action whenever
possible. For first-run, help, or "what should I do now" requests, answer in
this shape before explaining files, paths, packaging, or architecture:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one short sentence>.
After that: <one short sentence>.
```

State routing:

1. Installed but not calibrated: recommend `/aim calibrate-repo`.
2. Calibrated but no Epic exists: recommend `/aim start "EPIC: <desired outcome>"`.
3. Epic exists but is not approved: recommend reviewing Gate A and replying `approve` or `change: ...`.
4. Epic approved: recommend `/aim continue`.
5. Blocked: recommend resolving the named blocking issue.

Then perform only the context loading needed for that state:

1. Detect the repository root.
2. Detect or create `.aim` only when starting or resuming an AIM run.
3. Read `.aim/state.json` first when it exists.
4. If `.aim/state.json` describes an incomplete Epic, resume that checkpoint instead of starting a new Epic.
5. Read `aim.profile.yaml` when present as the primary shared repo-awareness source.
6. Apply compatible Personal AIM hints from `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
7. Use profile facts to choose locality, validation commands, short authoritative docs, risk zones, freshness triggers, and context to avoid before reading broader docs.
8. Load `references/agile-iteration-method.md`, then only the package-local references required by the current role, gate, command, or risk.
9. Load Codex-specific packaging only when Codex mechanics matter.
10. Read ordinary repository maintainer docs only when the requested change actually needs them.
11. Default to `Mode: Strict` unless the user explicitly chooses `Mode: Auto`.
12. Default to `Cost profile: Standard` unless the user explicitly chooses `Cost Control` or `Deep`.
13. Start visible AIM phases with exactly `Role: PO`, `Role: TDO`, `Role: Dev`, or `Role: Reviewer`, and show `Mode: Strict` or `Mode: Auto`.
14. Show `Cost profile` when it is not `Standard` or when resource use is part of the user's request.
15. Keep the public front door thin: route first to the state-specific next action before explaining the full method.

Treat unnecessary broad context loading, long low-risk markdown artifacts, repeated major-doc rereads, and context-hog files as budget bugs.
When a Personal or Team profile is present, report whether it was reused before broader docs. Profiles can guide locality and validation, but they cannot override AIM core, `.aim/state.json`, Team policy, gate ownership, escalation, or current repository evidence.
When profile reuse affects startup or Gate B, include this compact profile-source summary:

```text
Profile source: <personal hints path and/or aim.profile.yaml> (<readiness>)
Layering: <personal narrows team baseline | team profile baseline | personal profile only | no profile source>
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <area>
Avoided context: <docs/scans avoided>
Expansion reason: <none or reason>
Cheap validation first: <command>
```

When the repository provides `scripts/validate_aim_runtime.py`, use its `AIM 2.0 profile-source summary` output as the generated startup summary.

Outside hard-gate approval checkpoints, stop and ask when an escalation condition applies: scope expansion beyond Gate B, unclear or contradictory Epic intent, unmet acceptance checks without new assumptions, trust/data/user-facing risk, missing required files/APIs/data, or contradictory repo policy.

## Codex Skill Install Check

When the user runs AIM in Codex for install, upgrade, validate, status, config,
or stale-skill troubleshooting, make the bundled skill path obvious before
continuing:

- repo-bundled skill: `adapters/codex/agile-iteration-method/SKILL.md`
- local Codex install path: `~/.codex/skills/agile-iteration-method/SKILL.md`

If the local Codex skill is missing or appears older than the repo-bundled skill, state that AIM can continue from explicit AIM intent and canonical workflow docs for this run, but `/aim` works best after installing the bundled skill:

```sh
python3 scripts/aim_install.py --target . --mode personal \
  --footprint local --adapter codex --dry-run
```

Review the plan, then rerun with `--apply`. The installer adds picker metadata
and the package-local canonical references required by `SKILL.md`; a raw copy of
only the source adapter directory is incomplete.

For ordinary first-run `/aim start`, `/aim continue`, `/aim help`, or "what
should I do now" requests, do not lead with internal file paths, local skill
paths, runtime locations, adapter packaging, architecture details, or a command
inventory. Show install status only after the one-next-action guidance when it
changes the user's next decision or explains a blocker.
Do not treat a missing local skill as a blocker when the repository already contains the AIM contract; report the fallback and continue unless another escalation condition applies.

## Commands

Treat these as AIM intents when the current adapter supports them or when the user writes the equivalent in plain language:

- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim status`
- `/aim validate`
- `/aim help`
- `/aim config`
- `/aim calibrate-repo`
- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`
- `/aim upgrade`
- `/aim mode strict|auto`
- `/aim cost standard|control|deep`
- `/aim replan`
- `Install AIM`
- `Start working according to AIM`

Canonical intent, state effects, upgrade safety, and adapter fallbacks are
defined in `references/adapter-command-contract.md`.

If literal slash routing is unavailable, report that limitation, map the user's
plain-language request to the same command intent, and perform the equivalent
workflow directly. Syntax may fall back; command semantics may not.

`/aim calibrate-repo` uses the package-local canonical flow in `references/repo-awareness-calibration.md`.
Remember and forget intents must persist structured rules to `aim.profile.yaml`
or the user-level hints file and must never use `.aim/` as durable
repo-awareness. If a fact is too large for a short profile entry, create or
update a static memory document under `docs/features/`, `docs/workflow/`,
`docs/architecture/`, or another repo-configured stable docs path, then point to
that static source from the profile. Reading `.aim/state.json` to resume work is
allowed; citing `.aim/reviews`, `.aim/increments`, `.aim/decisions`,
`.aim/archive`, or other runtime artifacts as long-lived repository knowledge is
not allowed.
`/aim upgrade` must inspect selected AIM-owned packages through the deterministic
installer plan, show stale/collision results before apply, preserve rollback and
root-file exclusions, and never rewrite active `.aim/` state.
When no richer host action is available, use the actionable package fallback:

```sh
python3 scripts/aim_install.py --target <repo> --mode <mode> \
  --footprint <footprint> --adapter <adapter> --dry-run
```

Review the plan, then rerun with `--apply`. Use `--force` only for collisions
the user explicitly approves.
`/aim replan` returns only the active unaccepted increment to Gate B and preserves
the reason and accepted history.

## Thin Front Door

When the user asks how to begin, help, or what AIM should do next, detect
onboarding state first and show only the first useful choice by default:

- installed but not calibrated: `/aim calibrate-repo`
- calibrated but no Epic exists: `/aim start "EPIC: <desired outcome>"`
- Epic exists but is not approved: review Gate A and reply `approve` or `change: ...`
- Epic approved: `/aim continue`
- blocked: resolve the named blocking issue

For ordinary low-risk work, suggest this start shape:

```text
/aim start "EPIC: Improve the onboarding flow so a new homeowner can list a room and understand the next review step"
Mode: Strict
Cost profile: Cost Control
```

When the repo needs durable context first, suggest:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. Keep tone nuanced and empathetic toward both the cats and the future owners."
```

Do not explain adapter layering, every gate, every runtime artifact, or a command
inventory unless the user asks for deeper help or the task needs that context.

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

Use `approve` and `change: ...` as transport shortcuts at hard gates. In Strict mode, stop at Gate A, Gate B, and Gate E and wait for explicit user approval or change direction before advancing state or doing further work. In Auto mode, report hard gates without pausing between increments; require a final full-review pause before Epic completion.

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
Validation reports should classify the result as `healthy`, `recoverable`,
`blocked`, or `contradictory`; report Structural, Behavioral, Product coherence,
and Release readiness tiers; name the failed artifact or rule; and avoid
mutating runtime state.

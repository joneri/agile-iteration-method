---
name: aim
description: Run the complete AIM 2.0 command family and orchestrate project-specific PO, TDO, Dev, and Reviewer agents. Use for /aim intents, Epics, Done Increments, gates, repo calibration, agent configuration, upgrades, and AIM validation.
---

# AIM 2.0 for GitHub Copilot

This project skill is Copilot's AIM workflow source. The `aim` custom agent may
provide native orchestration and handoff UX where supported, but it does not own
a separate method.

Follow:

- `docs/workflow/agile-iteration-method.md` for AIM core
- `docs/workflow/adapter-command-contract.md` for command meaning
- `docs/workflow/adapter-skill-bootstrap.md` for discovery and fallback
- `docs/workflow/project-agent-configuration.md` for role specialization

## Complete command family

Recognize and execute the equivalent intent for:

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

If skill or slash routing is unavailable, report that limitation and preserve
the same intent in the selected AIM agent or plain language. Syntax may fall
back; semantics may not.

## Bootstrap

1. Detect onboarding state first.
2. Read `.aim/state.json` when it exists; resume incomplete work.
3. Read `aim.profile.yaml`, then `aim.roles.yaml`.
4. Load only relevant canonical AIM and repository evidence.
5. Create `.aim` only for start or resume.
6. Keep the main thread as the only runtime and gate owner.

For first-run guidance, recommend exactly one next action and use:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one sentence>.
After that: <one sentence>.
```

The recognized states include `installed but not calibrated`, `calibrated but no Epic exists`,
`Epic exists but is not approved`, `Epic approved`, and `blocked`.

Route installed but not calibrated to `/aim calibrate-repo`; calibrated but no
Epic exists to `/aim start "EPIC: Improve the onboarding flow so a new homeowner
can list a room and understand the next review step"`; an unapproved Epic to its
Gate A decision; an approved Epic to `/aim continue`; and blocked work to the
named blocker. Do not lead with internal file paths or a command inventory.

## Native role delegation

Use `aim-po`, `aim-tdo`, `aim-dev`, and `aim-reviewer` from `.github/agents/`
when bounded delegation materially helps and the active Copilot surface permits
it. Their project expertise is defined by `aim.roles.yaml`. The main AIM thread
alone writes `.aim/state.json`, advances gates, escalates scope, synthesizes
results, and accepts increments or Epics. Report sequential fallback when custom
agents are unavailable or disallowed.

Treat handoffs and other custom-agent-only UX as environment-specific. Never
require or create `AGENTS.md` or `CLAUDE.md` for AIM bootstrap.

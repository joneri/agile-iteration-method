# Platforms and Adoption Modes

AIM is one delivery system with several ways to adopt and start it.

Operating mode controls sharing and safety.
Platform support controls how you invoke AIM.
Neither changes the core delivery loop.

## Choose an Adoption Mode

### Personal

Use Personal AIM when one developer wants maximum flexibility.

- there are no Team or Enterprise sharing constraints
- AIM docs, repo-awareness, profiles, adapters, and runtime artifacts may stay
  local or be written and committed when the user chooses
- local personal hints remain available when the user prefers no repo footprint
- AIM can be tried or fully embedded without asking a team to adopt it

Personal is the guided installer default.
Its suggested adapter footprint is a convenience, not a restriction; the user
may choose local, profile, adapters, or full.

### Team

Use Team AIM when repository knowledge should be shared deliberately.

- `aim.profile.yaml` holds a small shared baseline
- commands, localities, risk zones, and loading hints become reusable
- active runtime state may remain private
- shared AIM surfaces stay small and reviewable

Team mode creates shared understanding, not a requirement to commit every AIM artifact.

### Enterprise

Use Enterprise AIM when AIM should work from outside the target repository and repository protection should be the default.

- AIM-internal artifacts stay ignored unless explicitly approved
- installation keeps AIM package files and repo-awareness memory outside the repo by default
- installation does not assume the repo root is empty
- generic instruction files are never overwritten
- adapter packages, embedded docs, and broader shared AIM surfaces require deliberate adoption
- product output can be shared without sharing AIM's internal process state

Enterprise is not simply Team mode for a larger company.
It is a stricter safety posture with a full external default.

## Choose a Platform

### Codex

Codex support is skill-first.

The AIM skill provides the native command experience:

```text
/aim start "EPIC: ..."
```

Explicit AIM intent remains a fallback when the skill is unavailable.

### GitHub Copilot

Copilot support is agent-first.

Select the AIM agent in chat, then use the AIM command family.
Optional prompt helpers may improve discoverability, but they do not redefine AIM behavior.

### Claude

Claude support is command-first.

Use the installed AIM commands.
Helper agents may support the command implementation, but users should not need to understand those internal surfaces.

Explicit Epic intent remains a fallback.

## What Native Support Means

Native support means:

- AIM has a natural entrypoint for the platform
- the platform can start, continue, validate, and calibrate AIM intent
- the adapter maps available tools into the shared AIM behavior
- unavailable capabilities fall back safely instead of changing the method

Native support does not mean every platform has identical UI or tool capabilities.

## What Stays Shared

Across Codex, Claude, and Copilot:

- the Epic remains the outcome
- one Done Increment is active at a time
- review happens before acceptance
- active progress can resume from AIM's durable runtime state
- `aim.profile.yaml` is the shared repo-awareness source when present
- role order, gates, ownership, escalation, and acceptance remain consistent

## What May Differ

Platforms may differ in:

- command routing
- available tools
- whether bounded helper agents are available
- how browser or terminal actions are exposed
- how the user sees prompts and checkpoints

When a capability is unavailable, AIM falls back to sequential work or explicit intent.
It does not silently weaken quality or change who owns the decision.

## A Simple Choice

Choose:

1. the mode that matches your sharing and safety needs
2. the platform adapter you already use
3. Strict or Auto for the amount of interruption you want
4. a cost profile for the amount of runtime depth the work deserves

The workflow remains AIM.

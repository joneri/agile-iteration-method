# Platforms and Adoption Modes

AIM is one delivery system with several ways to adopt and start it.

Operating mode controls sharing and safety.
Platform support controls how you invoke AIM.
Neither changes the core delivery loop.

## Choose an Adoption Mode

### Personal

Use Personal AIM when one developer wants maximum flexibility.

- no committed AIM files are required by default
- personal repository hints stay outside the repo
- AIM can be tried without asking a team to adopt it
- the user may choose to share more later

Personal is the guided installer default.

### Team

Use Team AIM when repository knowledge should be shared deliberately.

- `aim.profile.yaml` holds a small shared baseline
- commands, localities, risk zones, and loading hints become reusable
- active runtime state may remain private
- shared AIM surfaces stay small and reviewable

Team mode creates shared understanding, not a requirement to commit every AIM artifact.

### Enterprise

Use Enterprise AIM when isolation and repository protection should be the default.

- AIM-internal artifacts stay ignored unless explicitly approved
- installation does not assume the repo root is empty
- generic instruction files are never overwritten
- shared profiles and adapter packages require deliberate adoption
- product output can be shared without sharing AIM's internal process state

Enterprise is not simply Team mode for a larger company.
It is a stricter safety posture.

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

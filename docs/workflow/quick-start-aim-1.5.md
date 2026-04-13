> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick start AIM 1.5

Use this guide for the shortest correct path into AIM.

Use this after the repository already contains the AIM files.
If you still need to copy files, choose adapter packaging, or make the repo setup real, start with [Install AIM 1.5](install-aim-1.5.md).
If you need the broader front-door route first, use [AIM 1.5 document map](aim-1.5-doc-map.md).

## Why 1.5 feels different

AIM 1.5 keeps the same core loop and runtime model, but it is clearer about one important point:
- small scope means small behavior, not artificially few files
- a Done Increment may touch more focused files when that keeps responsibilities readable, reviewable, and cheaper to change later
- the goal is to avoid context hogs and mixed-responsibility files, not to defend one-file diffs as a virtue
- the public onboarding path now makes that rule visible from the start

## Quick route

1. Confirm installation is complete.
2. Pick the adapter start path below.
3. Send one Epic plus one mode.

## Choose your adapter

- Codex:
  the repo is the AIM contract and the skill adds the `/aim` launcher.
- Copilot:
  use the packaged `aim` agent and add prompt helpers when you want Copilot-style command entrypoints.
- Claude Code:
  use `CLAUDE.md` plus the shipped starter files in `.claude/commands/` and `.claude/agents/`.

Shared install note:
- `.github/agents/aim*.agent.md` are part of the AIM instruction layer generally.
- `.github/prompts/` are optional Copilot prompt helpers.

## How to start

Preferred production starts:
- Codex:
  - use `/aim start "EPIC: ..."` when the AIM skill is installed and enabled
- Copilot:
  - select the `aim` agent and run `/aim start "EPIC: ..."`
- Claude Code:
  - use the shipped repository AIM command from `.claude/commands/start-aim.md` when command-file routing is available
  - or start explicitly with `EPIC: ...`

Secondary starts:
- Codex:
  - in a fully prepared AIM repo, a plain-language AIM start is acceptable when the skill is not available and the intent is explicit
- Copilot:
  - `Install AIM` or `Start working according to AIM` remain valid when the optional Copilot layer is installed
- Claude Code:
  - explicit `EPIC: ...` plus `Mode: Strict` or `Mode: Auto` is the safe fallback when no Claude command wrapper exists

## Choose mode

Always make mode explicit:
- `Mode: Strict`
- `Mode: Auto`

If you do not specify mode:
- default is `Strict`

## What AIM does next

1. validates or normalizes the Epic candidate
2. makes `PO` ownership of the Epic explicit
3. lets `TDO` define the next single Done Increment
4. records runtime state in `.aim`
5. keeps the behavioral scope small even when clearer file boundaries require more than one file and avoids turning one file into a context hog

## What the visible checkpoints look like

- `PO` first:
  - frames the Epic and asks whether the Epic framing is correct
- `TDO` next:
  - proposes one Done Increment and asks whether that increment is the right slice now
- `Dev` then:
  - reports what changed and what was verified
- `Reviewer` then:
  - reports findings, readiness and any user test still worth doing
- `TDO` after review:
  - explains how to test the increment now and whether the increment should be accepted or adjusted
- `PO` after an accepted increment:
  - decides whether the Epic continues or closes

## Epic vs Done Increment

- Epic:
  - owned by `PO`
  - defines the user value and outcome
- Done Increment:
  - owned by `TDO`
  - defines the next single shippable slice

In AIM 1.5, the slice stays small by behavior and user value.
It does not have to minimize file count if a few focused files are the clearer result.
The rule of thumb is simple: avoid context hogs and keep each file responsible for one coherent part of the increment.

## Common follow-up commands

- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim mode strict|auto`
- `/aim upgrade 1.4-to-1.5`

If slash commands are not available in the current adapter:
- use the documented secondary natural-language intent
- or use the adapter bridge and shipped helper files (`CLAUDE.md`, `.claude/commands/start-aim.md`, `.claude/agents/aim.md`)
- or use the relevant workflow doc directly

Next docs:
- [AIM 1.5 usage guides](aim-1.5-usage-guides.md)
- [AIM 1.5 interaction examples](aim-1.5-interaction-examples.md)
- [AIM 1.5 document map](aim-1.5-doc-map.md)
- [Install AIM 1.5](install-aim-1.5.md) if setup is still incomplete

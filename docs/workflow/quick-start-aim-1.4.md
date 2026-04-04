> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick start AIM 1.4

Use this guide if you want the shortest correct path into AIM.

## Choose your adapter

- Codex:
  the repo is the AIM contract and the skill adds the `/aim` launcher.
- Copilot:
  use the packaged `aim` agent and add prompt helpers when you want Copilot-style command entrypoints.
- Claude Code:
  use `CLAUDE.md` plus the shipped starter files in `.claude/commands/` and `.claude/agents/`.

This repository now ships a minimal Claude starter layer so the Claude path is concrete instead of only documented in theory.

Shared install note:
- `.github/agents/aim*.agent.md` are part of the AIM instruction layer generally.
- `.github/prompts/` are optional Copilot prompt helpers.

## Codex skill versus repo-aware AIM

- The repo is the canonical AIM contract.
- The Codex skill is the cleanest way to expose `/aim`.
- `/aim` depends on the skill being installed and enabled.
- A prepared AIM repo can still work in Codex without the skill when you start with explicit AIM language.

## One obvious way to start

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

If you already have a strong Epic candidate:
- provide it directly
- AIM should validate it and normalize lightly if needed
- `PO` may accept it without a full rewrite

## Choose mode

Always make mode explicit:
- `Mode: Strict`
- `Mode: Auto`

If you do not specify mode:
- default is `Strict`

Practical explanation:
- `Strict`:
  - pause at the meaningful approval checkpoints
- `Auto`:
  - continue through increments automatically unless escalation occurs
  - still pause for final full review before Epic completion

## What to provide first

Best first message shape:
- `EPIC: <desired outcome>`
- `Mode: Strict` or `Mode: Auto`

Good example:

```text
/aim start "EPIC: Make AIM easier for new users to start and understand"
Mode: Auto
```

Repo-aware Codex fallback:

```text
EPIC: Make AIM easier for new users to start and understand
Mode: Auto
```

Claude Code-oriented equivalent:

```text
EPIC: Make AIM easier for new users to start and understand
Mode: Auto
```

## What AIM does next

1. validates or normalizes the Epic candidate
2. makes `PO` ownership of the Epic explicit
3. lets `TDO` define the next single Done Increment
4. records runtime state in `.aim`

## What the visible checkpoints look like

- `PO` first:
  - frames the Epic and asks whether the Epic framing is correct
- `TDO` next:
  - proposes one Done Increment and asks whether that increment is the right slice now
- `Dev` then:
  - reports what changed and what was verified
- `Reviewer` then:
  - reports findings, readiness, and any user test still worth doing
- `TDO` after review:
  - explains how to test the increment now and whether the increment should be accepted or adjusted
- `PO` after an accepted increment:
  - decides whether the Epic continues or closes

## Important distinction

- Epic:
  - owned by `PO`
  - defines the user value and outcome
- Done Increment:
  - owned by `TDO`
  - defines the next single shippable slice

If you provide increment ideas up front:
- AIM may preserve them as planning notes
- they do not replace `TDO` ownership of the next single Done Increment

## Common follow-up commands

- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim mode strict|auto`
- `/aim upgrade 1.2-to-1.4`

If slash commands are not available in the current adapter:
- use the documented secondary natural-language intent
- or use the adapter bridge and shipped helper files (`CLAUDE.md`, `.claude/commands/start-aim.md`, `.claude/agents/aim.md`)
- or use the relevant workflow doc directly

Next guide:
- `docs/workflow/aim-1.4-usage-guides.md`

Examples:
- `docs/workflow/aim-1.4-interaction-examples.md`

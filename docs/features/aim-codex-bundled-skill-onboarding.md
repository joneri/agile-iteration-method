# AIM Codex Bundled Skill Onboarding

This feature is part of the current AIM 2.0 Codex support story.

## Purpose

Make it obvious for Codex users that AIM ships a repository-bundled Codex skill and that `/aim` works best when that skill is installed locally.

## How it works

On the first AIM command in Codex, AIM should show:
- the repo-bundled skill path: `adapters/codex/agile-iteration-method/SKILL.md`
- the local Codex install target: `~/.codex/skills/agile-iteration-method/SKILL.md`
- the install command when the local skill is missing or stale

The repository remains the AIM source of truth.
The local Codex skill is the launcher and runtime guide for the Codex command surface.
The install command copies the whole skill directory because Codex may read picker metadata from files beside `SKILL.md`, such as `agents/openai.yaml`.

## Key decisions

- Missing or stale local skill installation is not automatically a blocker when the repo already contains the AIM contract.
- Codex should report the fallback clearly and continue from repository instructions unless another escalation condition applies.
- `Install AIM`, `/aim validate`, `/aim status`, `/aim config`, `/aim start`, and `/aim continue` are the most important surfaces for showing skill install status.
- This behavior improves first-run Codex adoption without changing AIM core behavior.

## Inputs and outputs

Inputs:
- current repository AIM files
- repo-bundled Codex skill path
- local Codex skill install path
- Codex skill picker metadata, when present
- user command or plain-language AIM intent

Outputs:
- clear install status
- exact copy command when needed
- current app-card name and description when picker metadata exists
- normal AIM command handling after the install status is visible

## Edge cases

- If `/aim` command routing is unavailable, use the explicit AIM intent fallback and show the same install guidance.
- If the local skill is older than the repo-bundled skill, recommend copying the repo-bundled skill directory again.
- If `SKILL.md` shows the current AIM version but the Codex picker still shows an older version, check `~/.codex/skills/agile-iteration-method/agents/openai.yaml` and restart or refresh Codex after reinstalling.
- If the repository lacks required AIM files, follow install or validation guidance instead of pretending the skill alone is sufficient.
- If adapter policy conflicts with repository AIM rules, escalate according to the normal AIM conflict rule.

## Debugging

The fastest check is:

```sh
diff -ru adapters/codex/agile-iteration-method ~/.codex/skills/agile-iteration-method
```

If the files differ, reinstall the repo-bundled skill package:

```sh
mkdir -p ~/.codex/skills/agile-iteration-method
cp -R adapters/codex/agile-iteration-method/. ~/.codex/skills/agile-iteration-method/
```

If the visible skill card still looks stale after this, restart or refresh Codex so it reloads the picker metadata.

## Related files

- `adapters/codex/agile-iteration-method/SKILL.md`
- `adapters/codex/agile-iteration-method/agents/openai.yaml`
- `README.md`
- `docs/workflow/install-aim-2.0.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/aim-adapter-guidance.md`

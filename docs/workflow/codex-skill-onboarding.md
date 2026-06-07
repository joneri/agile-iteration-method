# AIM Codex Bundled Skill Onboarding

This document defines canonical Codex onboarding behavior for the shipped AIM skill.

## Purpose

Make it obvious for Codex users that AIM ships a repository-bundled Codex skill and that `/aim` works best when that skill is installed locally.

## How it works

On the first AIM command in Codex, AIM should show:
- the repo-bundled skill path: `adapters/codex/agile-iteration-method/SKILL.md`
- the local Codex install target: `~/.codex/skills/agile-iteration-method/SKILL.md`
- the install command when the local skill is missing or stale

The repository remains the AIM source of truth.
The local Codex skill is the launcher and runtime guide for the Codex command surface.
The install command uses AIM's deterministic installer because the installed
package includes generated package-local canonical references as well as files
from the source adapter directory.

## Key decisions

- Missing or stale local skill installation is not automatically a blocker when the repo already contains the AIM contract.
- Codex should report the fallback clearly and continue from explicit AIM intent, canonical workflow docs, and `aim.profile.yaml` when present unless another escalation condition applies.
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
- exact installer command when needed
- current app-card name and description when picker metadata exists
- normal AIM command handling after the install status is visible

## Edge cases

- If `/aim` command routing is unavailable, use the explicit AIM intent fallback and show the same install guidance.
- If the local skill is older than the repo-bundled skill, recommend the
  reviewed installer update path.
- If `SKILL.md` shows the current AIM version but the Codex picker still shows an older version, check `~/.codex/skills/agile-iteration-method/agents/openai.yaml` and restart or refresh Codex after reinstalling.
- If the repository lacks required AIM files, follow install or validation guidance instead of pretending the skill alone is sufficient.
- If adapter policy conflicts with repository AIM rules, escalate according to the normal AIM conflict rule.

## Debugging

The fastest check is a dry-run:

```sh
python3 scripts/aim_install.py --target . --mode personal \
  --footprint local --adapter codex --dry-run
```

If the plan reports stale or missing package files, review it and apply:

```sh
python3 scripts/aim_install.py --target . --mode personal \
  --footprint local --adapter codex --apply
```

Do not replace this with a raw `cp -R`: the installer also packages required
canonical contracts under `references/`. If the visible skill card still looks
stale after apply, restart or refresh Codex so it reloads the picker metadata.

## Related files

- `adapters/codex/agile-iteration-method/SKILL.md`
- `adapters/codex/agile-iteration-method/agents/openai.yaml`
- `README.md`
- `docs/workflow/install-aim-2.0.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/aim-adapter-guidance.md`

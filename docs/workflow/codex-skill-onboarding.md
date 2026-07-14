# AIM Codex Skill Onboarding

This document defines canonical Codex onboarding behavior for both the public
portable AIM skill and the source-repository adaptive installation.

## Purpose

Make it obvious that the public Agent Skill is the normal portable Codex entry
point, while the adaptive installer remains available for a reviewed repository
footprint and native project specialists.

## How it works

Install the public skill with:

```sh
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method \
  --agent codex \
  --yes
```

For a public-skill first run, use this sequence:

1. run `/aim calibrate-repo` when repository knowledge is not calibrated
2. after calibration, run `/aim configure-agents` when project-specific
   specialists are wanted but `aim.roles.yaml` or native role files are absent
3. run `/aim start "EPIC: ..."` when the repository is ready

The repository remains the AIM source of truth.
The local Codex skill is the launcher and runtime guide for the Codex command surface.
The public package includes its generated package-local canonical references and
works without the source repository.

The adaptive installer remains available when a user wants one guided flow to
select a repository and adapters, seed `aim.profile.yaml` and `aim.roles.yaml`,
and create Codex project specialists. Its source must be checked out locally so
the user can review it before execution:

```sh
git clone --depth 1 https://github.com/joneri/agile-iteration-method.git aim-source
cd aim-source
python3 scripts/aim_install.py --dry-run
```

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
- If a public skill install is stale, recommend
  `npx skills update agile-iteration-method --yes`.
- If the repository's AIM profile or native specialists are missing or stale,
  recommend `/aim calibrate-repo`, `/aim configure-agents`, or the reviewed
  adaptive installer according to the user's setup goal.
- If `SKILL.md` is current but the Codex picker still shows an older version, check `~/.agents/skills/agile-iteration-method/agents/openai.yaml` and restart Codex after reinstalling.
- If the repository lacks required AIM files, follow install or validation guidance instead of pretending the skill alone is sufficient.
- If adapter policy conflicts with repository AIM rules, escalate according to the normal AIM conflict rule.

## Source-checkout debugging

When working from the AIM source checkout, the adaptive install plan remains the
fastest way to inspect the broader Codex package without writing:

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

For a portable public install, use `npx skills update` instead of assuming the
source checkout or `scripts/aim_install.py` is available.

## Related files

- `adapters/codex/agile-iteration-method/SKILL.md`
- `adapters/codex/agile-iteration-method/agents/openai.yaml`
- `README.md`
- `docs/workflow/install-aim-2.0.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/aim-adapter-guidance.md`
- `docs/workflow/version-and-installation.md`

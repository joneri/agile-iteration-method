# AIM 2.0 Operating Modes

## Purpose

Define the canonical AIM 2.0 operating modes:

- Personal AIM
- Team AIM
- Enterprise AIM

These modes control sharing and safety defaults.
They do not change AIM core roles, gates, Done Increment discipline, escalation rules, or ownership.

## Mode summary

| Mode | Meaning | Default sharing | Default safety posture | Best for |
| --- | --- | --- | --- | --- |
| Personal | one developer with maximum freedom | none required | permissive | solo work, trials, personal repos, flexible local workflows |
| Team | shared AIM understanding by agreement | shared repo-awareness and selected features | reviewable sharing | teams that want reusable repo knowledge |
| Enterprise | safe AIM use in stricter repos | external AIM package and memory | zero repo writes by default | protected repos, larger orgs, regulated environments |

## Personal AIM

Personal AIM is permissive.

Default assumptions:

- AIM imposes no sharing rules by default.
- `.aim/` may stay local or be committed if the user wants.
- AIM docs, repo-awareness docs, adapter files, profiles, and other AIM-owned
  files may be written to and committed in the repository if the user wants.
- repo-awareness may stay local or be committed.
- feature docs that help AIM may remain available in the repo.
- no extra safety restrictions are required just because AIM is present.

Personal AIM may be tidy or sloppy.
The user chooses.

## Team AIM

Team AIM creates shared AIM understanding for a team.

Default assumptions:

- repo-awareness is shared intentionally.
- shared AIM files are small, clear, and reviewable.
- `aim.profile.yaml` is the default tiny shared repo-awareness surface.
- feature docs may be shared when the team wants common AIM behavior or debugging knowledge.
- private runtime files may still remain private.
- active `.aim/` state is not shared unless the team explicitly chooses shared working state.

Team AIM shares what helps the team reason about the repository.
It does not require committing every AIM runtime artifact.

## Enterprise AIM

Enterprise AIM is external and protected by default.

Default assumptions:

- AIM may be used fully by an individual.
- AIM package files and durable repo-awareness memory live outside the target repository by default.
- AIM-generated non-product artifacts are ignored by default.
- AIM internal files should not be committed or pushed by accident.
- the default sharing model is: share the work produced with AIM, not AIM's internal artifacts.
- feature docs, adapter helpers, embedded AIM docs, or broader shared AIM surfaces happen only deliberately and explicitly.
- installation must not assume the repo root is empty.
- installation must not assume AIM may overwrite existing instruction files.

Enterprise AIM is not Personal AIM with a company name.
It is a stricter safety mode that protects the repository from accidental AIM footprint.

## Sharing model

| Surface | Personal | Team | Enterprise |
| --- | --- | --- | --- |
| Product output: code, config, tests, product docs | may commit | should commit when part of work | should commit when part of work |
| `.aim/` runtime state | may keep local or commit | local by default; shared only by team choice | ignored by default; do not commit unless explicitly approved |
| `aim.profile.yaml` | optional | default shared repo-awareness surface | explicit opt-in only; external memory is default |
| Personal hints under `~/.aim/repo-awareness/` | allowed | allowed as local hint | allowed as local/private hint |
| Feature docs that help AIM | may keep or commit | may share by agreement | explicit broader footprint or repo-owner approval only |
| Generic root instruction files such as `AGENTS.md` and `CLAUDE.md` | outside AIM architecture | outside AIM architecture | outside AIM architecture |
| AIM-generated markdown/process artifacts | may keep or commit | commit only if team wants audit/shared process | ignored by default unless explicitly promoted |
| Adapter helpers under `.github/` or `.claude/` | optional | share by adapter choice | explicit opt-in only |

## Enterprise ignore baseline

Enterprise AIM should protect these AIM-internal surfaces from accidental commit or push:

```gitignore
/.aim
/.aim-local
/aim.local.*
/*.aim.local.md
/*.aim.process.md
```

Meaning:

- `/.aim` protects runtime state.
- `/.aim-local` gives adapters a private local helper directory.
- `/aim.local.*` protects root-level private AIM notes or profiles.
- `/*.aim.local.md` protects private AIM markdown.
- `/*.aim.process.md` protects generated process notes unless deliberately renamed or moved into product docs.

The ignore baseline is a safety default, not a ban.
Enterprise repositories may deliberately share a reviewed AIM surface, but accidental sharing should be hard.

Enterprise AIM must not rely on repo-local symlinks as the default bridge to
external AIM package files or memory. Symlinks are allowed only as explicit
organization policy because they are fragile across OSes, CI, containers, and
repository moves, and they can make external files appear in repo tooling.

## Collision behavior

Generic root instruction files are outside AIM architecture:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`

AIM installation must not copy, create, modify, require, read, merge into, or overwrite them in any operating mode.
`CONTRIBUTING.md` may exist only as maintainer guidance in the AIM source repository and must be excluded from every target installer manifest.

Repo-owned AIM configuration surfaces still require collision handling:

- `.gitignore`
- `aim.profile.yaml`

Rules by mode:

- Personal: profile and ignore changes are permissive, but existing files must be inspected.
- Team: create or modify shared AIM configuration through reviewed team agreement.
- Enterprise: default to no repo writes; generate a patch unless explicit approval exists.

## Install behavior

Personal:

- install may be local-only
- repo mutation, adapter installation, shared profiles, and full embedded docs
  are all allowed choices
- permissive choices are allowed
- the installer must not apply Team review rules or Enterprise isolation rules
  merely because files will be written to the repository

Team:

- install should prefer a small shared profile and reviewed shared surfaces
- runtime stays private by default
- shared docs/features are deliberate

Enterprise:

- install should prefer local/private runtime and profile storage
- install should add or verify the Enterprise ignore baseline before creating local AIM artifacts in the repo
- install must not overwrite root instruction files
- install must not commit AIM internals by default

## Validator behavior

The validator should:

- confirm this canonical mode document exists
- generate representative Personal, Team, and Enterprise default plans
- compare mode-specific claims with actual plan footprint, profile, adapter,
  docs, ignore, and repo/local action behavior
- report the configured operating mode when it can detect one
- require Enterprise ignore markers when the repo profile declares Enterprise mode
- continue to reject active runtime state inside repo profiles
- report a contradiction when documented mode behavior and generated plans
  disagree

## Related files

- `aim.profile.yaml`
- `.gitignore`
- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/repository-surface-classification.md`
- `docs/workflow/install-aim-2.0.md`
- `scripts/validate_aim_runtime.py`

## Change log

- 2026-06-05: Added canonical Personal, Team, and Enterprise operating mode model.

# AIM 2.0 Profile Source Summary

## Purpose

Define the compact startup and Gate B summary that makes AIM 2.0 profile reuse visible.

This is canonical AIM startup and Gate B profile-source reporting behavior.

The summary explains what AIM reused from Personal and Team profile sources, what locality it selected, what broader context it avoided, and why it expanded beyond the profile when it did.

## User experience

When a Personal or Team profile is present, AIM should show a short profile-source summary during startup or Gate B.

The validator emits this summary from actual profile files:

```text
python3 scripts/validate_aim_runtime.py .
```

The summary should help the user understand:

- whether the repo profile was reused
- which profile facts affected the run
- which locality AIM inspected first
- which broader docs or scans were avoided
- why AIM expanded context beyond the profile

## Summary shape

Use this compact shape by default:

```text
Profile source: team: aim.profile.yaml (profile_ready)
Layering: team profile baseline
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <directly affected area or nearest known area>
Avoided context: <broad docs, adapter docs, repo-wide scan, or none>
Expansion reason: <none | missing evidence | stale profile | risk | ownership | user requested Deep>
Cheap validation first: <command or nearest check>
```

For very low-risk work, one line is enough:

```text
Profile source: aim.profile.yaml reused; locality=<area>; avoided=<broad scan/docs>; expansion=<reason or none>.
```

## How it works

AIM builds the summary from:

- `.aim/state.json`
- Personal AIM profile source, when available
- `aim.profile.yaml`
- directly affected files or user-provided scope
- validator readiness when available
- current cost profile
- current risk or missing evidence

The summary is not a new gate.
It is an explanation of startup and Gate B context selection.

The current helper is intentionally lightweight.
It recognizes profile sections and markers without requiring a full YAML parser.

## Key decisions

- The summary is compact by default.
- It appears at startup or Gate B when profile reuse affects planning.
- The validator can emit the summary from current profile files.
- It should not become a long markdown artifact.
- It should name avoided context because avoided reads are part of the cost-saving value.
- Expansion reasons must be explicit so deeper context does not look like silent drift.

## Inputs and outputs

- Inputs:
- profile readiness
- Personal profile path, if present
- Team profile path, if present
- profile locality hints
  - profile commands
  - profile risk zones
  - profile freshness triggers
  - current task scope
  - selected cost profile

- Outputs:
  - compact profile-source summary
  - layering result for Personal and Team profile sources
  - visible locality choice
  - visible avoided-context list
  - visible expansion reason when broader context is loaded

## Edge cases

- If no profile exists, report `Profile source: none` and continue with locality-first discovery.
- If both Personal and Team profiles exist, report both and explain the layering.
- If the profile is stale, report the freshness reason and refresh the smallest affected area.
- If the work crosses risk or ownership boundaries, report that as the expansion reason.
- If the user selects `Deep`, report that broader context is user-requested rather than accidental.
- If current repository evidence conflicts with the profile, treat the profile as stale or incomplete.

## Data correctness and trust

The summary does not change AIM authority.

It must not override:

- AIM core
- `.aim/state.json`
- Gate A, B, or E semantics
- ownership rules
- escalation rules
- current repository evidence

## Debugging

The best check is whether the summary answers:

> What did AIM reuse, what did it avoid, and why did it expand?

What "good" looks like:

- `Profile source` names the profile or says none
- `Layering` explains Personal versus Team source resolution
- `Reused facts` are short and concrete
- `Selected locality` is narrower than the whole repo when the work allows it
- `Avoided context` names broad docs or scans that were intentionally skipped
- `Expansion reason` is `none` or a specific risk/missing-evidence reason

What "bad" looks like:

- AIM silently rereads broad docs after a profile-ready startup
- AIM expands without saying why
- the summary becomes a long planning document
- profile facts are treated as gate or acceptance authority

## Related files

- `aim.profile.yaml`
- `aim.profile.yaml`
- `adapters/codex/agile-iteration-method/SKILL.md`
- `scripts/validate_aim_runtime.py`
- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/personal-local-profile-storage.md`
- `docs/workflow/team-profile-artifact.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `docs/workflow/aim-adapter-guidance.md`

## Change log

- 2026-06-05: Added validator-emitted profile-source summary behavior for actual Personal and Team profile sources.
- 2026-06-05: Initial compact profile-source summary shape.

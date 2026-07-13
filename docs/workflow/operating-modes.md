# AIM installation policy compatibility

## Current product model

AIM uses one adaptive installation. Personal, Team, and Enterprise are no
longer separate operating modes presented to users. AIM core, roles, gates,
runtime ownership, and adapter semantics are identical for every user.

The current choices are independent configuration dimensions:

- supplier adapters: Codex, Claude, and/or GitHub Copilot
- repository footprint: adapters, full, profile, local, or external
- sharing and protection policy expressed in `aim.profile.yaml` or managed
  organization policy
- execution mode: Strict or Auto
- runtime depth: Standard, Cost Control, or Deep

Do not confuse the legacy installation-mode names with Strict/Auto execution
mode or Standard/Cost Control/Deep runtime depth.

## Legacy flag mapping

The deterministic installer temporarily accepts older flags so upgrades remain
safe:

| Legacy flag | Compatibility behavior |
| --- | --- |
| `--mode personal` | former permissive defaults; prefer explicit footprint now |
| `--mode team` | former shared-profile defaults; equivalent to the normal project setup |
| `--mode enterprise` | former external/no-repo-write default; prefer `--footprint external` now |

These values may remain in older `aim.profile.yaml` files until a reviewed
calibration migrates them. Validators must treat them as legacy-compatible, not
as proof that three AIM products still exist.

## Protection and sharing

Protected repositories use an explicit local or external footprint and managed
policy. Shared projects use the standard adapter footprint and review
`aim.profile.yaml`, `aim.roles.yaml`, and supplier-native agent files like other
repository configuration. Solo users may keep those files private or commit
them according to repository policy.

Regardless of storage:

- AIM never owns generic root `AGENTS.md`, `CLAUDE.md`, or target
  `CONTRIBUTING.md` files
- active `.aim/` state stays separate from durable configuration
- native specialists never own `.aim/state.json` or gates
- installers never silently overwrite existing files

## Validation

Release validation generates the standard install plan and representative
advanced footprint plans. It also verifies that legacy flags still produce
deterministic upgrade plans while public docs and the guided installer expose
only one AIM product path.

See [Install AIM](install-aim-2.0.md),
[Project-agent configuration](project-agent-configuration.md), and
[Repo profile and footprint model](repo-profile-and-footprint-model.md).

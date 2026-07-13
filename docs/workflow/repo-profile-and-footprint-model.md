# AIM repo profile and footprint model

## Purpose

AIM separates product behavior from repository storage. There is one AIM
product and one guided installation; footprint and sharing policy decide where
configuration lives.

## Four layers

### AIM runtime

The active supplier or installed package executes roles, gates, modes, cost
profiles, validation, and resume behavior.

### Repository knowledge

`aim.profile.yaml` stores reusable project facts such as commands, localities,
ownership, risks, short authoritative docs, freshness triggers, and
avoid-by-default context. Local hints may narrow the shared baseline from
`~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.

### Project role intent

`aim.roles.yaml` stores PO, TDO, Dev, and Reviewer expertise, validation,
delegation policy, and write boundaries. Supplier-native project-agent files
derive their behavior from this shared intent.

### Working state

`.aim/` stores branch/run-local Epic, increment, gate, decision, and review
state. It is never a durable repository-profile or project-role store.

## Footprints

| Footprint | Repository effect |
| --- | --- |
| `adapters` | standard role/profile configuration, selected native adapters, required contracts, and runtime ignore |
| `full` | standard result plus full workflow docs, schemas, and license metadata |
| `profile` | repository profile and runtime ignore only |
| `local` | home-scope packages only |
| `external` | external distribution and home-scope packages only |

Footprint is not an AIM edition. Sharing, protection, ownership, and commit
policy remain repository or organization decisions.

## Profile contract

The structural source of truth for `aim.profile.yaml` is
`schemas/aim-repo-profile.schema.json`. The project-role contract is
`schemas/aim-project-roles.schema.json`.

A repo profile should capture only stable reusable knowledge. It must not
contain the active Epic, Done Increment, gate state, branch-specific review
findings, secrets, or copied runtime artifacts.

When personal hints and a shared profile both exist, local hints may narrow
discovery but must not override shared commands, ownership, risk, or policy.

## Protected repositories

Use `--footprint local` or `--footprint external` when repository writes are not
allowed. Managed organization policy may supply native agents outside the repo.
Do not use repo-local symlinks as a default bridge to external storage; they are
brittle across CI, containers, worktrees, and operating systems.

## Legacy migration

Older profiles may contain `adoption.mode: personal`, `team`, or `enterprise`.
The schema accepts them during migration. A reviewed calibration should replace
edition-like assumptions with explicit footprint, sharing, storage, ownership,
and protection fields. Active `.aim/` state is never rewritten during that
migration.

## Cost and freshness

Profiles reduce cold-start cost only while current. Refresh the smallest
affected facts after dependency, framework, test-tool, architecture, ownership,
deployment, security, or adapter changes. Broad repository scans remain a last
resort prompted by missing evidence, staleness, risk, or explicit Deep work.

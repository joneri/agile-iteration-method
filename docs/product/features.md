# AIM feature guide

This is the short map of what AIM 2.4 does. Follow the links only when you need
the operating detail.

## Delivery loop

- Epics describe outcomes.
- One Done Increment is active at a time.
- PO, TDO, Dev, and Reviewer keep planning, implementation, review, validation,
  and acceptance separate.
- Gate A approves the Epic, Gate B approves the increment, and Gate E accepts
  the result.
- Failed review or validation returns the increment for correction.

See the [canonical AIM method](../workflow/agile-iteration-method.md).

## Audience-context integrity

- Generated artifacts communicate their intended current meaning directly.
- Private conversations, rejected drafts, AI mistakes, prompts, and review
  feedback stay out of product copy, UI labels, code comments, and docs.
- Changelogs, decision records, and other intentionally historical artifacts
  retain the history their audience needs.

This makes AIM audience-aware from the first generated artifact. See the
[canonical principle](../workflow/agile-iteration-method.md#audience-context-integrity).

## Control and cost

- `Strict` pauses at all hard gates.
- `Auto` continues until risk, changed scope, uncertainty, or final acceptance
  requires a person.
- `Standard`, `Cost Control`, and `Deep` change context and verification depth;
  they never remove roles, gates, or escalation.

See [cost profiles](../workflow/cost-control-mode.md).

## AIM UI

- A local browser control room projects the active Epic and related increments
  into a live five-column Kanban.
- Every card retains its Epic identity and separates canonical role ownership
  from optional bounded helper-agent activity.
- Auto mode appears as automatic card movement because the UI polls canonical
  runtime evidence; the UI itself cannot advance a gate or write `.aim` state.
- The v1 read model is multi-Epic-shaped while execution remains single-Epic.

See [AIM UI v1](aim-ui.md).

## Repository knowledge

- `/aim calibrate-repo` verifies commands, technologies, important areas, and risk.
- `/aim remember-repo` and `/aim forget-repo` maintain reusable facts.
- `aim.profile.yaml` stores compact shared knowledge.
- User hints and protected external memory remain outside the repository.
- `.aim/` stores active work, never durable repository truth.

See [repo awareness](../workflow/repo-awareness.md).

## Reflect

- `/aim reflect` turns completed work in the current AIM project into verified
  knowledge candidates.
- `/aim reflect-all` previews and synthesizes a selected set of local AIM
  projects without changing any of them.
- Candidates carry provenance, current-evidence verification, confidence,
  contradictions, classification, destination, and a promotion action.
- Each completed reflection says whether action is recommended, assigns every
  candidate a disposition, and supplies one concrete next action or an explicit
  no-action conclusion.
- Reports remain temporary under `.aim/analysis/`; durable knowledge changes
  require a separate reviewed promotion.
- Reflect goes beyond memory cleanup for repository work by combining
  consolidation with current-source verification and human-owned promotion.

See [AIM Reflect](../workflow/reflection.md).

## Project specialists

- `aim.roles.yaml` defines project-specific expertise for PO, TDO, Dev, and Reviewer.
- `/aim configure-agents` previews updates to supplier-native agent files.
- Models, tools, permissions, and test strategies stay in the supplier's native format.
- The main AIM thread always owns runtime state and acceptance.

See [project-agent configuration](../workflow/project-agent-configuration.md).

## Adapters and commands

Codex, Claude Code, and GitHub Copilot each receive a native AIM skill. All map
the same command family:

`start`, `continue`, `status`, `validate`, `help`, `config`,
`configure-agents`, `calibrate-repo`, `remember-repo`, `forget-repo`,
`reflect`, `reflect-all`, `upgrade`, `mode`, `cost`, and `replan`.

If native routing is unavailable, explicit AIM intent preserves the same
semantics. See the [adapter entry model](../workflow/adapter-entry-model.md).

## Installation and upgrades

- The complete, self-contained public Agent Skill installs through
  `npx skills add joneri/agile-iteration-method --skill agile-iteration-method`.
- The public package is generated from canonical AIM sources and is not AIM Lite.
- One adaptive guided installer handles repository-aware setup.
- Footprints control where files may be written.
- Plans classify create, current, and collision states before apply.
- Apply is rollback-protected and safe to rerun.
- Adapter readiness receipts name skill paths, reload steps, and fallbacks.
- `/aim upgrade` refreshes AIM-owned packages without rewriting active state.

See [public Agent Skill distribution](../workflow/version-and-installation.md)
and [adaptive installation](../workflow/install-aim-2.0.md).

## Validation and release safety

- Structural, behavioral, product-coherence, and release-readiness checks are separate.
- Clean-room package closure verifies installed references.
- Documentation links, product versions, feature coverage, and website structure
  are release checks.
- Publication builds a deterministic Pages artifact before deployment.

See [release and publication](../workflow/release-publication-model.md).

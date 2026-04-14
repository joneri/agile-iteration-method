# AIM Modularity And Context Efficiency

## Purpose

Help AIM agents keep increments readable, reviewable, and cheaper to change later by separating behavioral scope from file count.

## How it works

A Done Increment stays small by limiting behavior, assumptions, and user-facing change.
It does not have to minimize the number of files touched.

Agents may add or split focused files when those files form clearer responsibility boundaries and preserve the approved behavior.
Examples include presentation components, hooks, helpers, domain logic, service modules, or short supporting docs.

## Key decisions

- Small increment means small behavioral scope, not necessarily minimal file count.
- More files can be better when each file has one clear responsibility.
- Files should split by stable responsibility and ownership, not arbitrary line counts.
- Avoid context hogs: oversized route files, components, services, docs, or helpers created to keep a diff in fewer files.
- Good structure is part of product quality because it affects how safely future changes can be made.

## Inputs/outputs

Inputs:
- Epic intent
- approved Gate B Done Increment scope
- planned files and responsibility boundaries

Outputs:
- a coherent increment that preserves approved behavior
- explicit file-boundary rationale when new focused files or modules are introduced
- review signal on whether the structure improves comprehension without needless fragmentation

## Edge cases

- Broad rewrites remain out of scope unless explicitly approved at Gate B.
- Arbitrary splitting by line count is not AIM guidance.
- Touching extra files is justified only when it creates a clearer boundary for the approved behavior.
- A one-file constraint from PO still overrides this guidance for that increment.

## Debugging

At Gate B, check whether the planned file boundaries reduce future context load without adding behavior or fragmenting responsibilities.

## Related files

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/copilot-layer.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `CLAUDE.md`

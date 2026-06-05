# AIM 2.0 Main Release Readiness Audit

## Purpose

Decide whether AIM 2.0 can safely become the main public release identity now.

This is a release-truth audit, not another transition note.

## Verdict

AIM 2.0 should not become the main public release identity yet.

It is now operational, discoverable, installable as a current operating path, and first in the README adoption path.
But the public identity surface still declares AIM 1.7 as the product release.

## Evidence checked

### README

Status: not ready for main AIM 2.0 identity.

The README now routes new Personal AIM and Team AIM users to AIM 2.0 first.
That satisfies the default adoption-path requirement.

The blocker is above that section: the title and opening still identify the product as AIM v1.7, and the page still explains why this is 1.7 and not 2.0.
That is honest for transition mode, but it prevents AIM 2.0 from being the main public release identity.

### Quick start

Status: sufficient for transition, not the blocker.

`quick-start-aim-2.0.md` now gives users a real Personal AIM and Team AIM start path.
`quick-start-aim-1.7.md` still exists for the cost-saving and full embedded fallback path.

The quick-start layer does not block the switch by itself.

### Install surface

Status: sufficient for transition, not the blocker.

`install-aim-1.7.md` now presents Personal AIM and Team AIM as current AIM 2.0 operating install choices while preserving Full embedded AIM as the AIM 1.7 path.

The install surface is transition-ready.

### Document map

Status: sufficient for transition, not the blocker.

`aim-1.7-doc-map.md` now presents AIM 2.0 as the current transition path and links the quick-start and install surfaces.

The document map is transition-ready.

### Release checklist

Status: sufficient for transition, not the blocker.

`release-aim-1.7.md` now defines the AIM 2.0 transition state and states what must be true before AIM 2.0 becomes the default adoption path.

The release checklist no longer blocks transition by itself.

## Criteria result

Against the current release criteria:

1. Front door, install surface, and document map route users toward AIM 2.0 as the default start: mostly yes.
2. Release checklist permits AIM 2.0 to become the default adoption path when conditions are met: yes.
3. Public release story no longer depends on AIM 1.7-first wording to stay coherent: no.
4. Transition is described as complete in the release surface: no.

The decisive failure is criterion 3.

## Smallest remaining blocker

The smallest remaining blocker is the README public identity contract.

AIM 2.0 cannot be the true main release path while the repository's first line still says `Agile Iteration Method (AIM) v1.7` and the main release explanation still argues why the release is not 2.0.

## Single next blocker-removing Done Increment

DI-023 should update the README public identity from AIM 1.7 transition mode to AIM 2.0 main release mode.

Scope for that increment:

- change the README title and opening release identity to AIM 2.0
- describe AIM 2.0 as the main low-footprint adoption release
- preserve AIM core loop, gates, ownership, escalation, and Done Increment discipline unchanged
- keep AIM 1.7 as the full embedded and cost-saving fallback path
- remove or rewrite the `Why 1.7 and not 2.0` section so it no longer contradicts the main release identity
- do not rewrite install docs, doc map, quick-start docs, website, or adapter docs in the same increment

## Release decision

Do not mark the Epic complete yet.

Use this audit as the decision basis for the next Epic or next release-identity increment.

## Related files

- `README.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/quick-start-aim-1.7.md`
- `docs/workflow/install-aim-1.7.md`
- `docs/workflow/aim-1.7-doc-map.md`
- `docs/workflow/release-aim-1.7.md`

## Change log

- 2026-06-05: Initial decisive audit for AIM 2.0 main release identity readiness.
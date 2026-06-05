> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.7 release and production checklist

## Release summary

AIM 1.7 is the cost-saving release.

It keeps the accepted AIM loop and runtime contract stable, but makes the public promise much stronger:

- reduce wasted GitHub Copilot AI Credits
- reduce wasted tokens in Codex and Claude Code
- keep `Cost Control`, `Standard`, and `Deep` tied to real risk instead of vague preference
- explain exactly how AIM saves money

## Why this is 1.7 and not 2.0

- no core role-order change
- no gate-semantics change
- no `.aim` ownership reset
- no incompatible runtime redesign

This is a sharper release line, not a new incompatible method family.

## AIM 2.0 transition state

The current release surface now exposes AIM 2.0 as a real transition path:

- `README.md` exposes AIM 2.0 from the front door
- `install-aim-1.7.md` presents Personal AIM and Team AIM as current operating install choices
- `aim-1.7-doc-map.md` presents AIM 2.0 as the current transition path

This does not mean the full AIM 2.0 release switch is complete.
For now, AIM 1.7 remains the main release line while AIM 2.0 transition work continues.

## What must be true before AIM 2.0 becomes the default adoption path

Before switching the default adoption path from AIM 1.7 to AIM 2.0, the release surface should show all of the following:

1. the front door, install surface, and document map all route a new user toward AIM 2.0 as the default start
2. the release checklist explicitly permits AIM 2.0 to become the default adoption path
3. the public release story no longer depends on AIM 1.7-first wording to stay coherent
4. the transition is described as complete in the release surface, not only in deeper operating docs

Until those conditions are met, AIM 2.0 should be treated as the current transition path rather than the default release path.

## Publish checklist

1. Confirm `README.md` presents the intended current front door for this release state.
2. Confirm the cost-saving promise is explicit, not hidden behind generic process language.
3. Confirm GitHub Copilot AI Credits are described as a current operator concern.
4. Confirm the cost-saving story points to current official vendor billing guidance.
5. Confirm the stable runtime-family docs still describe the accepted method correctly.
6. Confirm the Codex skill metadata presents AIM 1.7 consistently.
7. Confirm the AIM 2.0 transition state is described accurately: visible and usable when intended, but not described as the default adoption path until the release switch is complete.

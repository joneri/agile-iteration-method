<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: examples/user-stories/example-user-story.md
-->

# US-SAMPLE: Try the product with sample data

Epic: EPIC-ONBOARD — A useful first session
Intent: INT-START — Help customers get started and recover from setup problems
Priority: 1
Status: ready

As a new customer, I need to try a sample workspace so that I can understand the
product before entering my own data.

## Acceptance criteria

- AC-1: From an empty first session, one clearly labelled action opens a usable
  sample workspace and its main view.
- AC-2: The workspace visibly identifies its contents as sample data.
- AC-3: Removing the sample workspace leaves no sample records in a real workspace.
- AC-4: A creation failure explains a safe retry without creating duplicates.

## Refinement

PO owns the need, benefit, priority and criteria. TDO verifies isolation and
retry behavior with PO before proposing a delivery. Implementation tasks cover
storage, the entry action and checks; they are not separate user requirements.

This Story can be selected with US-DIAGNOSE from EPIC-SUPPORT. Their shared
selection does not merge their criteria or close either Epic automatically.
A Sprint may timebox their work, but is not the Story or the delivered increment.

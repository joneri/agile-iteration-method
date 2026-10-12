# US-DIAGNOSE: Identify a customer's failed setup safely

Epic: EPIC-SUPPORT — Recoverable setup with useful support
Intent: INT-START — Help customers get started and recover from setup problems
Priority: 2
Status: ready

As a support specialist, I need a safe reference for a failed setup attempt so
that I can identify the failure without asking a customer for sensitive data.

## Acceptance criteria

- AC-1: A failed setup exposes a support reference that identifies the attempt.
- AC-2: The reference and customer-visible message contain no secrets or personal
  record contents.
- AC-3: An authorized support lookup identifies the failure category and safe
  recovery step; an unauthorized lookup reveals no attempt details.

## Refinement

PO determines the supported user context and priority. TDO investigates current
support authorization and diagnostic retention, then proposes bounded checks.
A delivery may include this Story and US-SAMPLE from EPIC-ONBOARD. Review and
validation preserve separate criterion evidence for each. Accepting the delivery
proves those Stories; broader support and onboarding outcomes need their own
Epic closure decisions.

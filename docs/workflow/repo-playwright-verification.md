# Repository Playwright Verification

## Purpose

Define Playwright expectations when AIM work changes a rendered UI, browser interaction, responsive layout, or user-visible graphical behavior in this repository.

## Applicability

Load this document only when:

- planning or implementing rendered UI work
- Reviewer needs browser evidence
- Gate E depends on graphical verification
- visual regression or interaction risk is present
- a Playwright command is selected
- repo-awareness calibration evaluates UI-testing policy

Documentation-only changes without a rendered surface do not require Playwright.

## Procedure

1. Identify the local page or route affected.
2. Start the smallest required local server.
3. Use Playwright or the active adapter's browser tooling.
4. Verify the changed workflow at desktop and mobile viewport sizes.
5. Check loading, empty, error, and interactive states when affected.
6. Capture concise evidence for Reviewer and Gate E.
7. Stop the server when verification is complete.

## Commands

Use repository-provided Playwright commands when present.
If none exist, use the active adapter's supported browser workflow rather than inventing a committed test harness.

## Evidence

Record:

- target URL or route
- viewports tested
- interaction path
- observed result
- screenshots when visual correctness matters
- any untested state and reason

## Blockers

Escalate before Gate E when:

- the rendered target cannot be started
- authentication or required data is unavailable
- browser tooling cannot exercise a trust-sensitive interaction
- observed behavior conflicts with the accepted increment

Manual verification may be requested when automation is unavailable; that alone is not a code-change blocker.

## Edge Cases

- Static Markdown changes do not trigger browser verification.
- Adapter UI differences may change tooling, not evidence expectations.
- Responsive work requires at least one desktop and one mobile viewport.
- Visual snapshots must not replace interaction checks when behavior changed.

## Debugging

Start with the browser console, failed network requests, and the smallest reproducible route.
Avoid broad site traversal unless the changed behavior crosses route boundaries.

## Related Surfaces

- `aim.profile.yaml`
- `docs/workflow/repo-awareness-two-layer-model.md`
- `docs/workflow/repo-awareness-calibration.md`

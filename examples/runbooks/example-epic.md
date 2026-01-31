# Epic: instant value on first visit

## Purpose
A new user should understand the product and get value within 60 seconds, without reading docs or setting up anything.

## User value
As a new user, I can try the product immediately and I know what to do next.

## Scope
- Add a “try with sample data” flow
- Make empty states explain what is missing and how to fix it
- Ensure the first-run experience is fast and predictable

## Non-goals
- No full redesign
- No new analytics initiative
- No multi-language support in this epic

## Acceptance criteria
- First visit: user sees a meaningful screen within 2 seconds
- “Try with sample data” creates a usable workspace and takes the user to the main view
- Empty state has: what it is, why it’s empty, one primary action
- The sample workspace can be removed in one action

## Trust and safety rules
- Never show scary numbers or warnings on first visit unless something is truly broken
- If something fails, show a clear recovery path, not a dead end

## Evidence required
- Screen recording (or screenshots) of first visit
- Notes on what is shown in each empty state

## Related docs
- docs/features-explanations/onboarding.md
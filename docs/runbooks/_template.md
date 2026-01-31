# Runbook: <feature> v<version>
(Read more in docs/features-explanations/<feature>.md)

## purpose
Explain why this exists in user terms. What problem it solves and what “good” looks like.

## non-goals
List what is explicitly out of scope for this epic.

## user experience
Describe the expected behaviour end to end.
- normal case:
- edge case:
- failure / stale / uncertain data:

## trust rules
What the user must be able to trust. Keep it concrete.
- what numbers mean
- what must never be misleading
- when we must be silent instead of wrong

## key kpis
What matters. Keep it short.
- primary kpi:
- secondary kpis:
- never-a-kpi:

## data sources and truth
Where the data comes from and which source wins if they disagree.
- source of truth:
- fallbacks:
- freshness rules:

## acceptance criteria
Write as observable outcomes.
- [ ] …
- [ ] …
- [ ] …

## debug and verification
Minimum steps to prove it works.
- how to reproduce:
- expected logs (only if needed):
- manual checks:
- automated checks:

## risks
List real risks and how we reduce them.
- risk:
- mitigation:

## files likely involved
Only list if helpful. Keep it short.
- src/…
- docs/…

## documentation update rule
Before starting:
- read: docs/features-explanations/<feature>.md

After finishing:
- update the same file with:
  - behaviour changes
  - new endpoints / flags / fallbacks
  - edge cases and the best debug step
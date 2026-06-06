# Feature explanations

This folder contains support and reference explanations.
The goal is to make future debugging, examples, comparisons, and repo-local support easier.

Path note:
- In this AIM repository, `docs/features/` is support/reference by default.
- Behavior-defining AIM docs belong in `docs/workflow/`.
- The folder is not AIM core truth.

Canonical documentation model:
- `docs/workflow/documentation-model.md`

## When to add or update a doc
Create or update a support/reference explanation when:
- background, examples, comparisons, or debugging support are needed
- a repo-local feature note is useful but should not define AIM behavior
- a support doc relies on a specific assumption that future readers should see

If the document defines AIM behavior, install behavior, mode behavior, cost behavior, context behavior, classification behavior, or documentation truth, put it in `docs/workflow/` instead.

## Where to put it
- One feature, one file:
  docs/features/<feature-name>.md

Current roles:

| File | Role |
| --- | --- |
| `aim-cost-comparison.md` | reference comparison; explains the behavioral cost case without defining AIM rules |
| `aim-github-copilot-cost-reduction-playbook.md` | vendor-specific onboarding playbook |
| `aim-vendor-cost-baseline-june-2026.md` | date-stamped vendor reference based on external facts |
| `_template.md` | support template for future non-canonical reference or repo-local docs |

## Required sections
Use docs/features/_template.md.

Keep it short, concrete and actionable.

## Rule
If a Done Increment changes AIM behavior, update the relevant canonical document in `docs/workflow/`.
If a Done Increment needs support, examples, background, or repo-local explanation, add or update a document here.

Do not treat a repo-local or user-created feature explanation as AIM core truth.
Promote behavior-defining material into `docs/workflow/` by an explicit AIM product documentation change.

## License

Documentation for Agile iteration method (AIM) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Preferred attribution:
Jonas Eriksson (Agile iteration method, AIM)

See LICENSE-DOCS for details.

Code in this repository is not automatically covered by CC BY 4.0 unless explicitly stated. If you want code to be open source as well, add a separate code license in LICENSE.

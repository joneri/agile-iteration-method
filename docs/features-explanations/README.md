# Feature explanations

This folder contains short, concrete explanations of non-obvious features.
The goal is to make future debugging and changes faster and safer.

## When to add or update a doc
Create or update a feature explanation when:
- a feature is introduced or significantly changed
- a new behaviour, rule, fallback or threshold is added
- an API contract changes (shape, semantics, flags)
- a fix relies on a specific assumption (for example trading days source, coverage thresholds)

## Where to put it
- One feature, one file:
  docs/features-explanations/<feature-name>.md

Examples:
- value-series-trading-days.md
- autopost-kpis.md
- dividends-reconciliation.md

## Required sections
Use docs/features-explanations/_template.md.

Keep it short, concrete and actionable.

## Rule
If a Done Increment changes behaviour, it must also update the relevant feature explanation.
If no doc exists yet, create it.

## License

Documentation for Agile iteration method (AIM) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Preferred attribution:
Jonas Eriksson (Agile iteration method, AIM)

See LICENSE-DOCS for details.

Code in this repository is not automatically covered by CC BY 4.0 unless explicitly stated. If you want code to be open source as well, add a separate code license in LICENSE.
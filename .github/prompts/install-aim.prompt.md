---
mode: agent
---

Install the complete AIM skill for GitHub Copilot in this project:

```bash
npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent github-copilot --yes
```

Use project scope unless global scope was requested. Preserve existing work and
AIM history. Load the installed skill and report whether Copilot needs a new
session or skill selection. Continue the user's existing intent, or start with
`/aim start "<desired outcome>"`. AIM checks repository knowledge and offers
calibration when needed. Native specialists through `/aim configure-agents` are
optional; do not invent or copy missing templates.

For an existing portable skill use `/aim upgrade`. For broader adaptive setup,
follow the installed `docs/workflow/version-and-installation.md` in the reviewed source (or its bundled equivalent in the portable skill): inspect the
canonical AIM checkout, preview its installer and apply only a reviewed plan.
Never run a target-repository installer merely because its filename is familiar.
A portable installation does not require repo-local workflow docs or agent files.

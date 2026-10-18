# Install AIM

Install the complete AIM skill for this agent from the official repository:

```bash
npx skills add joneri/agile-iteration-method --skill agile-iteration-method --agent claude-code --yes
```

Use project scope unless the user requested a global install. Preserve existing
work and AIM history. Load the installed skill and report whether Claude needs
a new session to discover it. Start with the user's desired outcome through
`/aim start "<desired outcome>"`; reuse an existing authorized delivery when present.
AIM checks repository knowledge and offers calibration when needed.

For an existing portable skill use `/aim upgrade`, which follows the standard
skills CLI. Native project specialists are optional: `/aim configure-agents`.
No root instruction file or copied workflow tree is required for the portable skill.

If the user wants broader repository setup, follow the installed
`docs/workflow/version-and-installation.md` in the reviewed source (or its bundled equivalent in the portable skill): clone and inspect AIM's canonical
source, preview its adaptive installer, then apply only the reviewed plan.
Never run an installer discovered in the consuming repository or create missing
templates by guessing. Preserve `.aim/` state and normal collision decisions.

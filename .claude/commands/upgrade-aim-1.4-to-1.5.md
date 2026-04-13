# Upgrade AIM 1.4 to 1.5

Use this command to upgrade the active public AIM surface in Claude Code from 1.4 to 1.5.

Command behavior:
- read `docs/workflow/migrate-aim-1.4-to-1.5.md`
- inspect the current public docs, packaged prompt helpers, and packaged agent metadata
- keep `AGENTS.md` canonical and preserve the accepted AIM runtime model
- update the files that represent the active release surface to AIM 1.5
- keep older AIM 1.4 release material as historical documentation unless the user explicitly asks to replace it

Return:
- changed files
- migration assumptions
- follow-up risks

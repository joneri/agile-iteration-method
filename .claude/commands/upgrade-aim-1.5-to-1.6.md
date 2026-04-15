# Upgrade AIM 1.5 to 1.6

Use this command to upgrade the active public AIM surface in Claude Code from 1.5 to 1.6.

Command behavior:
- read `docs/workflow/migrate-aim-1.5-to-1.6.md`
- inspect the current public docs, packaged prompt helpers, and packaged agent metadata
- keep `AGENTS.md` canonical and preserve the accepted AIM runtime model
- update the files that represent the active release surface to AIM 1.6
- add cost-profile guidance while keeping AIM 1.5 file-boundary guidance active

Return:
- changed files
- migration assumptions
- follow-up risks

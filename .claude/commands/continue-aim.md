# Continue AIM

Use this command to continue the active AIM loop in Claude Code.

Command behavior:
- inspect `.aim/state.json`
- resume the active incomplete Epic from the stored gate, role, increment, and mode when possible
- do not silently start a new Epic if a resumable checkpoint exists
- if runtime state is contradictory or blocked, stop and explain the exact reason instead of guessing

Ownership rule:
- only the main AIM thread may update `.aim/state.json`, advance gates, or accept increments

# Continue AIM

Use this command to continue the active AIM loop in Claude Code.
Map it to `/aim continue` from
`docs/workflow/adapter-command-contract.md`.

Command behavior:
- inspect `.aim/state.json`
- resume the active incomplete Epic from the stored gate, role, increment, and mode when possible
- at `done_increment_accepted`, repeat the PO assessment of Epic goal,
  acceptance criteria, accepted evidence, non-goals, and remaining gaps;
  recommend exactly one of `close`, `continue`, or `split` with rationale before
  any mutation, and leave the ordinary disposition decision to the user
- do not silently start a new Epic if a resumable checkpoint exists
- if runtime state is contradictory or blocked, stop and explain the exact reason instead of guessing

Ownership rule:
- only the main AIM thread may update `.aim/state.json`, advance gates, or accept increments

If command-file routing is unavailable, state that limitation and handle the
same `/aim continue` intent in ordinary Claude chat.

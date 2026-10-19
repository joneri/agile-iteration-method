# Continue AIM

Use this command to continue the active AIM loop in Claude Code.
Map it to `/aim continue` from
`docs/workflow/adapter-command-contract.md`.

Follow [runtime source routing](../../docs/workflow/adapter-command-contract.md#runtime-source-routing)
before selecting state. Native Story work resumes the selected delivery
through the trusted Story helper's compact receipt, preserving frozen scope,
policy and the actual designated owner's authority. Exact action envelopes use
their named authority path without fallback.

For an explicitly selected legacy Epic/Increment workspace:
- inspect that workspace's `state.json`
- resume the active incomplete Epic from the stored gate, role, increment, and mode when possible
- at `done_increment_accepted`, repeat the PO assessment of Epic goal,
  acceptance criteria, accepted evidence, non-goals, and remaining gaps;
  recommend exactly one of `close`, `continue`, or `split` with rationale before
  any mutation, and leave the ordinary disposition decision to the user
- do not silently start a new Epic if a resumable checkpoint exists
- if runtime state is contradictory or blocked, stop and explain the exact reason instead of guessing

Ownership rule:
- only the main AIM thread may mutate the selected runtime or record actual owner decisions

If command-file routing is unavailable, state that limitation and handle the
same `/aim continue` intent in ordinary Claude chat.

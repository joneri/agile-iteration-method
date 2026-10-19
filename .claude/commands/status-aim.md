# AIM Status

Map this command to `/aim status` from
`docs/workflow/adapter-command-contract.md`.

Follow [runtime source routing](../../docs/workflow/adapter-command-contract.md#runtime-source-routing)
before selecting state. Resolve the product release from the trusted
package's `VERSION` or manifest `productVersion`, separately from runtime contract
versions (`aimVersion` in legacy state). For native Stories, report compact ledger/delivery status, frozen
Ship/Loop policy, designated owner and next action. For the explicitly selected
legacy workspace, report its Epic, increment, role, mode, cost profile and gate.
This command is read-only and never creates runtime state.

If command-file routing is unavailable, state that limitation and handle the
same `/aim status` intent in ordinary Claude chat.

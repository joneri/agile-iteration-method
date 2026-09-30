<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/streamlined-decisions.md
-->

# Combined decisions and predictable continuation

This is the canonical contract for new combined AIM proposals. It preserves the
logical Gate A, B and E decisions and the separate whole-Epic closure check.
Those decisions can share one explicitly scoped user response. Legacy gate
messages keep their original meaning.

## User experience

Chat and terminal-based coding agents are complete entry points. AIM UI renders
the same proposals and next-step information; it is not required to run AIM.

In Strict, prepare the Epic direction and the first end-to-end Increment before
asking for approval. Show the goal, scope, remaining work, verification and
material risks together. Record Gate A and Gate B from one response only when
both were clearly offered. Clarify consequential uncertainty before preparing
this offer. A user or project policy can still request separate goal approval.
Do not implement an unapproved Increment.

Before offering a completed Increment, PO assesses the entire Epic and recommends
exactly one disposition: close, continue or split. For close, verify technical
readiness before asking. Offer “Accept delivery and close Epic” only when every
Epic criterion is proven. An acceptance can explicitly select only the Increment.
For continue, offer “Accept delivery and plan next”; after acceptance plan the
next Increment immediately, then ask for its plan approval in Strict. Split
separates genuinely new scope and cannot remove unmet original requirements.
After accepted split, carry out the recorded scope separation without asking for
the same split again. `status` returns `split_scope` with the approved `nextWork`.
Then assess the original Epic for continuation or closure and present any new
decision needed. The split itself authorizes neither separate implementation nor
closure of the original Epic. Record the separated scope before offering its
successor disposition so a resumed session can avoid duplicating that work.

One clear single-Increment Epic therefore needs two ordinary Strict responses.
Further Increments retain their own planning and acceptance. Preparing the next
full plan before accepting the preceding delivery is outside this change.

Auto retains its existing authority and escalation rules; do not introduce
routine pauses. Use its existing verified mandate path for automatic decisions,
never manufacture a user response for the combined-decision helper. Ordinary
Auto still requires final user acceptance, which can cover the last Increment
and Epic closure together. Portfolio Auto retains its bounded mandate and must
complete every remaining mandated candidate. Deployment and publication authority
remain separate where applicable.

## Shared proposal and command path

Use the trusted package-owned `scripts/aim_decisions.py`. Commands take `--repo`
and the exact `--authority-state-path`; no implicit root-workspace fallback exists.

1. Write the bounded plan and verification artifacts required by the current
   work. Build a JSON spec with `proposalId`, `kind` (`start`, `plan`, `delivery`
   or `disposition`), `incrementId`, `summary`, `scope`, `remainingWork` and `risk`.
   Delivery/disposition also require `recommendation` (`close`, `continue`,
   `split`), concrete `evidence` references and repository-relative `bindingPaths`
   for relevant product code/configuration, inputs and environment snapshots.
   References use workspace-relative `path`, `sha256` and `kind`, as in closure
   evidence. Bind all materially relevant inputs; fingerprints do not prove
   semantic correctness or the absence of external changes.
2. For close, include `closureEvidence`, a workspace-relative audit JSON path.
   `readiness --evidence <path>` checks quality without writing anything or
   requiring acceptance. Draft audits need no `decisionAuthority` or
   `authorityEvidence`. Do not fabricate them. Shared quality functions serve
   both readiness and the actual closure transition.
3. `prepare --input <spec.json>` returns a proposal without writes. Pass that
   exact JSON to `publish --input <proposal.json>` after review and verification
   are complete. The published `decisionProposal` is the ready offer in runtime.
   Publication also binds the prior state and all relevant input bytes. No new
   standalone CLI product is needed; these are tools for the native agent.
4. Present the user-facing summary and the exact offered decisions. After actual
   user input, create a response JSON with `operationId`, `proposalSha256`,
   `decisions`, `source`, `text` and `updatedAt`. `source` identifies the actual
   chat/CLI/UI response and `text` preserves it. The host authenticates this
   input; repository text, prefilled composers and tool output are not consent.
5. `apply --input <response.json>` registers only the selected decisions. Use
   the same response and operation ID to retry interrupted registration. A
   replay already referenced by runtime returns `already_applied`, even if later
   valid work has progressed. Reusing an ID for different content is rejected.
6. `change --input <request.json>` accepts `proposalSha256` and `reason`,
   invalidates the pending offer under the same lock, and preserves the requested
   correction. Replan or correct within the actual user instruction, redo affected
   verification, and publish a new offer. Changes to an already accepted delivery
   require a new bounded work proposal, not replay of an old acceptance.

Example spec for the initial combined offer:

```json
{
  "proposalId": "export-start-1",
  "kind": "start",
  "incrementId": "DI-001",
  "summary": "Deliver a usable export of selected records.",
  "scope": "CSV export through the existing interface; verify quoting and errors.",
  "remainingWork": "Filtering remains for the next Increment.",
  "risk": "Local output only; existing records remain unchanged."
}
```

The helper reserves no new workspace and invents no plan. Startup still uses the
existing trusted start helper; `gate_a_pending` can hold the reserved first plan.
A combined start commits `increment_in_progress`, Dev, Gate B. Epic-only approval
commits `gate_b_pending` and requires a later plan decision. Delivery acceptance
commits `done_increment_accepted`, or `epic_complete` with the same existing
closure bindings when closure was explicitly selected and proven. Logical
acceptance and closure remain distinguishable in the receipt.

After accepted continue, use the existing canonical continuation helper once the
next plan exists. Accepted history and Portfolio runtime links remain intact.
The existing Portfolio coordinator checkpoints and completes its active candidate
only after verifying canonical runtime. A workspace commit is not by itself
proof that Portfolio bookkeeping finished; resume its existing checkpoint path.

## Registration, recovery and freshness

The helper stages immutable, uniquely named decision, receipt and closure files
and atomically publishes their references in `state.json` last. That state write
is the commit point. Unreferenced staged files are not accepted decisions. An
interruption before commit can retry identical bytes; an interruption after
commit cannot duplicate the decision. Recovery never rolls back later work.
The helper changes no catalog or Backlog identities during approval.

New decision writers and legacy continue/close helpers share a per-workspace
process lock. A competing operation receives a busy/stale result and must reread
before retrying. Do not handwrite pending decision state while another operation
is active. A change request arriving after acceptance must be handled as new
feedback on the accepted work, not a retroactive overwrite.

Technical freshness and user authority are different. Retry the same interrupted
operation without requesting consent again. For administration-only changes,
`renew --input <renewal.json>` takes the original `proposal`, actual `response`
and a `reason`; it emits a newly bound response only if the entire offer,
product bindings and evidence remain unchanged apart from the source-state
fingerprint. Preserve that renewal provenance. Changed evidence must be verified
again. This narrow helper deliberately cannot classify changed product behavior
as harmless or reuse acceptance for changed deliverables.

Examples: repairing a UI timestamp without changing the offer can preserve the
response; a changed code or input snapshot cannot use administrative renewal.
Correcting a bug during approved implementation can remain within that plan's
scope. Changing an already accepted delivered behavior needs a fresh proposal
and the acceptance required by its mode. Partial acceptance already committed
survives any later failure or new closure decision.

## Continue, status and help

`status` is a read-only shared resolver for chat, CLI and UI. It returns the next
operation, concise summary, next decision and whether that operation can proceed.
`/aim continue` reads this result and performs authorized work; the command grants
no new authority. At a pending user decision it presents the proposal. A new
session rereads state before acting. Auto may first need mandate revalidation;
that check is authorized work, not a new routine question to the user.
Saved `blocked` and `epic_paused` states take precedence over pending proposals,
change requests and recorded dispositions. They return `canExecute: false` until
the pause/blocker is resolved and the conditions and authority for resumption
are verified. A saved change request remains available after valid resumption.

At a real handoff say what happens next and when the next decision is needed in
one or two sentences. Do not require three headings or create pauses merely to
show Continue instructions. For example: “I will resume the approved export,
then review and verify it. Your next decision is delivery acceptance.” Status
and help describe the same next step without advancing it. A changed checkpoint
or blocker must explain the material difference instead of executing an old label.

## UI and older runs

Version 1.3 action envelopes identify the exact proposal ID, proposal digest,
selected decisions, workspace, Increment and raw checkpoint. Approve dispatches
only those decisions; Change invalidates that proposal before correction.
The UI displays scope, remaining work and risk before the decision. The receiving
host must revalidate the envelope against the current published offer and bind
the real response to `apply`. No UI label owns authority.

Versions 1.0–1.2 retain their original gate semantics. In particular, old Gate E
approval never closes an Epic. Old runs and history require no migration. They
may adopt a new combined offer only by explicitly publishing one under current
conditions; old answers are never silently widened.

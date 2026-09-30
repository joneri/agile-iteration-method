# Post-Gate-E PO disposition

New combined proposals follow [Combined decisions and predictable continuation](streamlined-decisions.md).
They preserve logical gates while allowing one explicit response for direction
plus first plan, or delivery plus disposition. Legacy gate actions retain their
original scope. Use the same shared helper and next-step resolver in chat, CLI
and UI; no UI session is required.

At `done_increment_accepted`, PO evaluates the Epic goal, acceptance criteria,
accepted evidence, non-goals, and remaining gaps. PO must recommend exactly one
of `close`, `continue`, or `split`, state the rationale and remaining-scope
consequence, and must not merely ask the user to choose among undirected
options. The recommendation is not authority: ordinary Strict and Auto require
the user's explicit disposition decision, which may share the presented
Increment-acceptance response. On resume, reuse current evidence and a recorded
valid decision; reassess only missing or changed inputs. Portfolio Auto records the same recommendation
before its separately revalidated mandate may authorize eligible closure.

An accepted Increment proves only that Increment. Before recommending `close`,
PO performs a closure truth audit against the complete Epic and its declared
`Outcome class: Product|Pilot|POC`. Every acceptance criterion must be `proven`
with concrete evidence; counterevidence must be actively searched; unresolved
findings, contradictions, and remaining gaps must be empty. Product and Pilot
require representative user-journey verification through the normal entry point.
The implementing agent may perform this verification, including automated
end-to-end tests; record the actual performer and any assistance. This permits
implementer-run journey checks; it does not waive independent material-change
review under `adaptive-execution.md`. Unassisted operation is required only when
the user or project acceptance criteria require it. Synthetic or mocked evidence
alone may close only an explicitly bounded POC, not prove a Product outcome.

Missing or contradictory evidence forces `continue` and another coherent Done
Increment; AIM must create another coherent Done Increment rather than close
prematurely. `split` cannot discard unmet
Epic criteria. User acceptance and Portfolio authority authorize a decision but
cannot turn missing evidence into proof. Canonical combined closure uses `scripts/aim_decisions.py apply`; legacy
closure uses the trusted `scripts/aim_runtime_contract.py close` preview/apply
flow. Both
bind its contained JSON truth audit through `epicClosureEvidence`.
direct `epic_complete` writes are non-canonical. Closure state must also bind
`epicClosureEvidenceSha256` and `epicClosureEvidenceSetSha256`. Every cited
evidence object must bind a contained non-empty file by path, kind, and digest;
require structured black-box and negative-test records plus a separate matching
closure-authority decision.
Use `docs/workflow/epic-closure-truth-audit.md` for the artifact shape and negative
test checklist.

After an ordinary user decision `continue`, create the next canonical `DI-*`
plan, then use the trusted package-owned `scripts/aim_runtime_contract.py
continue` preview and digest-matched apply. It must validate the complete
candidate against the shipped runtime-state schema and coherence rules before
atomically replacing the exact contained `state.json`. Publish only
`gate_b_pending` with the new active Increment, `currentRole: TDO`, and
`lastGatePassed: Gate A`; never persist `increment_planning` or another internal
planning label. Failure leaves the prior state byte-for-byte unchanged.

AIM UI may present an unknown `epicStatus` as a calm “Status updating”
in-progress card only when the workspace is safely contained, the active
`DI-*` and all other required fields are canonical, and no other drift exists.
Preserve the raw value in compact diagnostics and hide every Gate action. Any
additional drift remains fail-closed; presentation fallback never normalizes or
writes runtime state.

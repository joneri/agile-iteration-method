# Receiving-agent orchestration ownership

Issue [#25](https://github.com/joneri/agile-iteration-method/issues/25) makes the
agent receiving an AIM assignment its default coordinator. It delegates bounded
implementation and independent review. A separate coordinator needs an explicit
user mandate or authorized handoff; model settings, Native graphs and a request
for real subagents do not supply that authority.

The canonical portable entry states this before agent launch. Native,
startup/delegation, Story and introductory guidance use the same rule. After
handoff, the former layer relays actual user instructions, factual status and
genuine escalations, retaining only explicitly scoped owner decisions. Slow turns
and missing file writes alone do not authorize steering or worker replacement.

## Runtime boundary

The existing Native activation stores optional `ownership`, not a second ledger:

- `{"receivingSession":"actual-receiver","kind":"receiving"}` binds the
  receiving agent as coordinator.
- `kind: "handoff"` adds a hash-bound `mandate` reference to the actual scoped
  human instruction. Its delivery, approved scope, original receiver, current
  source, target and default residual relay role must match. Retained decisions
  confer no new acceptance or resource authority. The exact previous activation
  digest prevents reuse of an older transfer after a round trip.
- `kind: "recovery"` continues an existing actual coordination role in a new
  session, preserving the original receiver, activation history and campaign.
  It is not a substitute for a subordinate transfer mandate.

Once bound, ownership cannot be omitted or its receiver renamed on resume.
Supported activity starts and orchestration observations/decisions then require
the current coordinator, even if an upstream relay remains activated. Returning
coordination through a handoff requires a new matching reassignment mandate.
Historical plans and activations retain their original behavior.

The CLI validates declarations, contained evidence, freshness and scope. It cannot
authenticate a human instruction, distinguish a false recovery declaration from
real host recovery, or intercept arbitrary host messages. The existing Codex
bridge verifies the actual bound executing thread, not the original receiver.
The coordinator must corroborate actual identities and authority in the host.
See the [canonical contract](../workflow/native-orchestration.md#coordination-ownership-and-handoff).

## Verification

Run the ledger regression suite from the repository root:

```sh
python3 -m unittest discover -s tests -p 'test_aim_orchestration*.py' -q
python3 scripts/build_public_skill.py --check
python3 scripts/validate_aim_runtime.py . --release
git diff --check
```

`test_aim_orchestration_ownership.py` uses temporary real ledgers and explicitly
synthetic human mandates. It checks normal delegation, initial and later handoff,
wrong scope/session/role, changed evidence, relay steering, retained policy,
recovery, downgrade, reassignment and historical compatibility. Rejected writes
must preserve ledger bytes. Existing suites retain review, acceptance, resource,
host-thread and campaign-history checks.

Bounded separate-agent forward exercises cover the seven issue scenarios against
the revised instructions. Their prompts, concrete proposed topology/messages and
independent assessment are retained in the [forward exercise evidence](evidence/2026-11-12-orchestration-ownership-forward.json). These
are instruction exercises with simulated host identities, not full game builds,
host authentication tests or a controlled comparison of product quality.

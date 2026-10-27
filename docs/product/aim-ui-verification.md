# AIM UI verification

The current primary UI is Board and Graph. Run the real persisted Story journey:

```sh
python3 scripts/verify_aim_story_board.py --output output/playwright/story-board-proof
```

The installed Playwright CLI wrapper must be available. `verify_aim_graph.py`
uses this same current journey; its native seed remains available for package
contract tests. The old planning-panel recipe is a supporting legacy check, not
an acceptance oracle for the primary UI.

The disposable fixture exercises Backlog → Ready → In progress → Review → Done
through the trusted native helper, never by changing browser state. It checks a
real card flight exactly once, stable card identity/open details/keyboard focus,
Story-to-Story edges, external inputs, Graph focus during polling, Waiting for you
without premature Done, reload persistence and reduced-motion/mobile behavior.
Authority and independent review records in the fixture are synthetic; they grant
no real project acceptance. Raw CLI logs, screenshots, trace and final ledger
are retained. UI process cleanup is identity-bound.

For changes to unfinished-work visibility, use the bounded isolated projection
and owner-decision checks first:

```sh
python3 -m unittest discover -s tests -p 'test_aim_observations.py'
python3 -m unittest discover -s tests -p 'test_aim_observation_decisions.py'
```

They retain native and observation bytes while changing delivery focus, preserve
unfinished obligations and waiting/changes-requested states, reject invalid owner
authority, and allow a real scoped decision without accepting unrelated Stories.
Keep earlier snapshots in the journal. A display-only replacement report cannot
move unfinished work to History. Use synthetic projects for this check; do not
rewrite consuming-project ledgers or manufacture decisions to clean up the board.

For owner decisions, run the complete recording-to-browser journey separately:

```sh
python3 scripts/verify_aim_owner_decisions.py --output output/playwright/owner-decision-proof
```

It uses actual trusted decision CLI commits and normal polling: human approval,
changes requested, delegated-owner approval, per-Story scope, real card flight,
focus, reload and identical uncertain retry. No subsequent snapshot import or
Story status edit is allowed. It retains the journal, requests/receipts, trace,
raw CLI output and screenshots; authority is explicitly synthetic. An unconfirmed
UI stop fails verification and preserves its owned recovery workspace.

For correction-to-original continuity, run:

```sh
python3 -m unittest discover -s tests -p 'test_aim_story_links.py'
python3 scripts/verify_aim_story_continuity.py --output output/playwright/story-continuity-proof
```

The isolated journey rejects an original, publishes a linked correction, keeps
both visible across focus changes, explicitly resubmits original proof, copies
the whole original owner request, then records one actual synthetic scoped
original decision. It checks the sibling and correction remain unaccepted,
reload persistence and the distinction between link provenance and dependencies.
The fixture decisions grant no real acceptance.

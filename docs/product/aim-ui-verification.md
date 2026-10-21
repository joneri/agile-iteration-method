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

Also inspect the real consumers read only: AIWebSite must retain 8 Stories
(3 Ready, 5 Backlog). ParaClones must show its actual current work and the 16
accepted Done cards together on the main board, with replaced, rejected and
earlier unfinished attempts in History. Verify original ledger bytes and pinned method
hashes, including rejected owner feedback, before claiming the cleanup complete.

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

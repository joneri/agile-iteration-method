# Verify AIM UI planning

Use this project recipe for the actual Plan increment surface or changes to its
selection, handoff or polling. It complements affected native checks; it is not
a mandatory full-product test after every change.

## Run and identify the product

From this source checkout, with Python, Playwright's Chromium and an already available
Playwright CLI:

```sh
python3 scripts/verify_aim_ui.py
```

The command finds an installed `playwright-cli` or the installed Codex Playwright
skill wrapper. `--playwright-cli <executable>` selects another available CLI/wrapper.
`--output <new-directory>` selects a proof location; the default creates a unique
directory under `output/playwright/`. Existing evidence is never overwritten.
The recipe installs nothing and does not attach to a user's browser.

Launch creates a disposable synthetic workspace with Ready Stories in two Epics,
using the native Story helper and AIM UI lifecycle. Doctor compares `/api/health`
with the start receipt and current source: repository, process/instance, protocol,
product version, payload and task binding. A mismatch fails before browser use.

## User routes and observable results

| Outcome | Route and prerequisite | Proof |
| --- | --- | --- |
| Prepare one coherent planning proposal | Open Plan increment, select the two Ready Stories, enter a goal, choose Copy planning proposal | Actual clipboard text preserves discuss/read-only, freshness and user-approval boundaries and names exactly those Story IDs, the goal and current ledger digest. Ledger bytes remain unchanged; no delivery or approval is created. |
| Prevent use of an obsolete proposal | Keep that selection while the native helper adds a third synthetic Ready Story; let normal polling deliver the changed ledger | The new Story becomes visible, the previous selection clears, Copy planning proposal is disabled and the interface explains the change. |
| Understand and advance dependent work | Run `python3 scripts/verify_aim_graph.py`; open Graph, select the ready contract and copy its assignment; record a native completion | Clipboard retains observed scope/digest, bounded files, skills and authority limits; normal polling unlocks the two dependent tasks and preserves keyboard focus. The UI does not mutate the ledger. |
| Catch obsolete activity proof | In the same Graph route, edit the completed contract's bound source | The completed activity becomes stale, dependent work loses its assignment, and mobile view remains usable. Raw proof and trace are retained after verified instance cleanup. |
| Diagnose invalid native evidence | The Graph recipe deliberately changes the disposable fixture's plan proof | The native ledger remains invalid and its diagnostic graph stays visible, with no assignment control. Actual delivery proof is preserved. |

The expected behavior comes from [AIM UI](aim-ui.md) and the Story contract,
not from the rendered output itself. The recipe drives browser controls; it does
not call internal UI setters or substitute a mocked page. Raw CLI results,
clipboard/DOM observations, screenshots and trace remain beside `result.json`.
A failed or unavailable phase is not a pass.

## Cleanup and upkeep

The recipe closes only its named browser session and stops its verified native
UI instance. After confirmed stop it removes its disposable workspace and retains
proof outside it. An unconfirmed stop preserves the workspace/process metadata
at the reported recovery path and fails the run. Inspect that cleanup failure;
never kill all browser/server processes.

Update the affected route and recipe when controls, prompt format, ledger
selection semantics, polling or launch/health identity change. Distinguish a
product regression from a recipe gap or stale map. Do not relax the expected
behavior to make a broken product pass. Dev and Reviewer reuse this entry and
inspect a relevant independent counterexample; raw evidence remains delivery
evidence, not a feature-status database.

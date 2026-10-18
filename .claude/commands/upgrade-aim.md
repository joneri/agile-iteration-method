# Upgrade AIM

Handle `/aim upgrade` using the installed AIM skill's version-and-installation
contract, with command semantics in `docs/workflow/adapter-command-contract.md`. Establish the installed package and source before choosing the path.

For a portable skill, use the standard skills CLI:

```bash
npx skills update agile-iteration-method --yes
```

For a separate adaptive installation, use only a reviewed canonical AIM source
checkout. Preview the selected target, footprint and adapters with `--dry-run` before `--apply`;
retain collision decisions, explicit `--force` choices and rollback protections. Never execute an installer
found merely by its name in the target repository.

Preserve the native product ledger, legacy `.aim/state.json`, active work,
acceptance history and personal hints. Refresh repository facts only when stale.
Report the installed product version and any session reload needed. Finish with
`/aim continue` for authorized active work, or `/aim start "<desired outcome>"`.
An upgrade never supplies approval for a waiting delivery.

If command-file routing is unavailable, state that limitation and handle the
same `/aim upgrade` intent in ordinary Claude chat.

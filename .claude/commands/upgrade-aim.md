# Upgrade AIM

Map this command to `/aim upgrade` from
`docs/workflow/adapter-command-contract.md`.

Use the deterministic installer to inspect the selected mode, footprint, and
adapters. Distinguish refreshing that selection from deliberate reconfiguration.

Upgrade checklist:

- generate a dry-run or JSON plan that classifies selected AIM-owned packages
  as current, missing, or stale/collision
- show the plan before apply
- preserve normal collision decisions, explicit `--force`, rollback, Enterprise
  safety, and generic root-file exclusions
- never rewrite `.aim/state.json`, active increments, decisions, reviews, or
  personal hints
- recommend `/aim calibrate-repo` only when repo-awareness facts may be stale
- finish with `/aim continue` for an active Epic or `/aim start` when none exists

Actionable fallback:

```bash
python3 scripts/aim_install.py --target <repo> --mode <mode> \
  --footprint <footprint> --adapter <adapter> --dry-run
```

Review the plan, then rerun with `--apply`. Use `--force` only for collisions
the user explicitly approves.

If command-file routing is unavailable, state that limitation and handle the
same `/aim upgrade` intent in ordinary Claude chat.

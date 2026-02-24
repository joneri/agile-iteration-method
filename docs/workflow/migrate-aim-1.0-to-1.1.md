> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Migrate AIM 1.0 to AIM 1.1

Use this when an existing repo still uses AIM 1.0 terms/paths.

## Copy-paste prompt

```text
Upgrade this repository from AIM 1.0 to AIM 1.1.

Required outcomes:
1) `docs/features-explanations/` is migrated to `docs/features/`.
2) `docs/runbooks/` is migrated to `docs/epics/`.
3) Documentation clearly states kickoff contract:
   - PO creates Epic from desired outcome.
   - TDO creates Done Increment based on Epic.
4) Copilot layer exists and uses canonical files in:
   - `.github/agents/`
   - `.github/prompts/`
5) Commit-after-increment is optional policy, not hard AIM rule.
6) No stale AIM 1.0 references remain.

Actions:
1) Rename/move folders and files as needed.
2) Update markdown references.
3) Update templates/examples to AIM 1.1 terms.
4) Update changelog with migration entry.
5) Return checklist of changed files and follow-up items.
```

## Copilot prompt-file alternative

If your repo includes prompt files, run:
- `/migrate-aim-1.0-to-1.1`

Source file:
- `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`

If repository is already on AIM 1.1, use:
- `docs/workflow/migrate-aim-1.1-to-1.2.md`

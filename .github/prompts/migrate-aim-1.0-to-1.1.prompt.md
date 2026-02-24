---
mode: agent
---

Upgrade this repository from AIM 1.0 to AIM 1.1.

Required outcomes:
1. `docs/features-explanations/` is migrated to `docs/features/`.
2. `docs/runbooks/` is migrated to `docs/epics/`.
3. Documentation clearly states kickoff contract:
   - PO creates Epic from desired outcome.
   - TDO creates Done Increment based on Epic.
4. Copilot layer exists and uses canonical files in:
   - `.github/agents/`
   - `.github/prompts/`
5. Commit-after-increment is optional policy, not hard AIM rule.
6. No stale references remain to AIM 1.0 paths/terms.

Actions:
1. Rename/move folders and files as needed.
2. Update all references in markdown files.
3. Update examples/templates to match AIM 1.1 terms.
4. Update changelog with AIM 1.1 migration entry.
5. Return a checklist with file paths changed and any manual follow-up.

If repository is already on AIM 1.1, use:
- `/migrate-aim-1.1-to-1.2`

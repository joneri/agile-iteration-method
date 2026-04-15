---
mode: aim
---

Show short AIM 1.6 help for this repository.

Explain:
1. the three front-door choices:
   - start: `/aim start "EPIC: ..."`
   - continue: `/aim continue`
   - check setup: `/aim validate`
2. the default lightweight start:
   - `Mode: Strict`
   - `Cost profile: Cost Control`
3. only the essential concepts:
   - Epic is the outcome
   - Done Increment is the next shippable slice
   - `.aim/` stores runtime state
4. the main commands:
   - `/aim start "EPIC: ..."`
   - `/aim continue`
   - `/aim status`
   - `/aim validate`
   - `/aim config`
   - `/aim cost standard|control|deep`
   - `/aim upgrade 1.5-to-1.6`

Keep the answer compact. Do not explain adapter layers, gate theory, or the full method unless I ask for deeper help.

If no active Epic exists, end by telling me the exact next start command to run.

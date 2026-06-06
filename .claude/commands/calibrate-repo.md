# Calibrate AIM Repo Awareness

Run the canonical `/aim calibrate-repo` flow from `docs/workflow/repo-awareness-calibration.md`.

- start with the smallest trustworthy repository scan
- read `aim.profile.yaml` as the shared baseline
- apply compatible hints from `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- verify uncertain or trust-sensitive facts before persistence
- save structured shared facts to `aim.profile.yaml`
- save personal preferences only to the user-level hints file
- never store stable repo-awareness under `.aim/`
- finish with the canonical calibration summary

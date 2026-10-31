# Historical AIM 4.8 candidate experiment

These sources retain the protocol and isolated candidate scaffolding used before
the production Native runtime was finished. Candidate `4.8.0-native.1` and
`4.8.0-sp.1` were based on AIM 4.7.7. They are not the AIM 4.8.0 release contract.
Use `docs/workflow/native-orchestration.md` for current product behavior.

Each candidate received 12 minutes 30 seconds to build three native game levels
with GPT-6 Luna Max. Product source copies, frozen binaries, profiles, raw play
evidence and personal feedback remain local; they are not distribution payloads.
The provisional observation score was inconclusive because native-input
completion and route coverage were insufficiently comparable. The owner later
played both candidates and strongly preferred Native. That is owner feedback,
not a controlled proof of general method superiority or lower usage.

The SP wrapper delegates graph/orchestration to a pinned upstream Superpowers
checkout. The helper copies its tracked source and license into an isolated
experiment only. No upstream framework is a production AIM dependency.

# AIM 2.0 Repository Surface Classification

## Purpose

Define the first repository classification model for the AIM repo so maintainers can tell what should ship, what is repo-aware, what is runtime-only, what is internal build memory, and how remaining AIM 1.x material must be absorbed into AIM 2.0, retained only for a concrete short-term migration reason, or deleted.

This model is the cleanup foundation for AIM 2.0.
It classifies before deleting, but it no longer treats user-facing 1.x docs as a museum to preserve by default.

## User experience

A new user should meet a cleaner product surface.

A maintainer should be able to inspect a major file or folder and answer:

- does this belong to AIM as static product?
- does this vary by target repository?
- is this local runtime or working state?
- is this build memory from creating AIM itself?
- is this AIM 1.x material that must be absorbed into AIM 2.0, kept only for a short-term migration bridge, moved to internal build memory, or deleted?
- should this ship, be exported, be isolated, or stay local-only?

## Classification categories

Use these categories for major repository surfaces:

| Category | Meaning | Default shipping decision |
| --- | --- | --- |
| Static AIM product | Canonical AIM method, runtime, adapter, workflow, or public product documentation | ship or export |
| Repo-aware template | Intended to be adapted by a target repository | ship as template or pointer, not blind overwrite |
| Repo-specific configuration | Belongs to this repository's current AIM use | do not blindly install into target repos |
| Runtime / working state | Current Epic, increment, review, gate, and local run state | local-only, never product |
| Internal build memory | Strategy, audit, or decision docs created while building AIM itself | keep for maintainers, not default public path |
| Migration bridge / removal candidate | AIM 1.x material that is not current product; keep only for a concrete short-term migration reason, otherwise absorb into AIM 2.0 or delete | do not ship as default guidance |
| Tooling / validation | Scripts and checks that support AIM runtime or repo health | ship when generally useful |
| Public release surface | Files a new user reads first | keep clean and current |

## Major surface inventory

| Surface | Classification | Static / repo-aware / local | Shipping decision | Recommendation |
| --- | --- | --- | --- | --- |
| `README.md` | Public release surface | static AIM product | ship | keep as the clean AIM 2.0 front door |
| `AGENTS.md` | Repo-aware instruction surface | repo-specific and collision-prone | template or reference only | never blindly install over an existing target repo file |
| `CLAUDE.md` | Adapter bridge / repo-aware instruction surface | repo-specific and collision-prone | template or reference only | never blindly install over an existing target repo file |
| `aim.profile.yaml` | Team AIM repo profile | repo-specific shared configuration | example or template, not universal product | use as the tiny Team AIM profile example for this repo |
| `.gitignore` | Repo config | repo-specific | template fragment only | keep `.aim/` ignored; do not treat full file as product |
| `CHANGELOG.md` | Public release history | static product | ship | keep, but future cleanup may separate AIM 1.x history from current front door |
| `CONTRIBUTING.md` | Maintainer guidance | static product / repo maintainer surface | ship for AIM repo, optional for installs | keep as maintainer-facing |
| `CONTRIBUTORS.md` | Project metadata | static product | ship | keep |
| `LICENSE` | Project metadata | static product | ship | keep |
| `.aim/` | Runtime / working state | local-only | never ship as product | keep ignored; archive or trim old run artifacts only after decisions are captured |
| `docs/workflow/agile-iteration-method.md` | Canonical method/runtime doc | static AIM product | ship | keep as core product doc |
| `docs/workflow/quick-start-aim-2.0.md` | Public release surface | static AIM product | ship | keep as default quick start |
| `docs/workflow/install-aim-2.0.md` | Public release surface | static AIM product | ship | keep as the current installation front door |
| `docs/workflow/aim-2-low-footprint-adoption.md` | Product workflow doc | static AIM product | ship | keep as deeper adoption guide |
| `docs/workflow/install-aim-1.7.md` | 1.x install surface with still-useful transition content | 1.x user-facing guidance slated for absorption | do not keep as default guidance | merge still-needed install content into a 2.0 install surface, then delete this file |
| `docs/workflow/quick-start-aim-1.7.md` | 1.x quick-start surface | 1.x user-facing guidance slated for absorption or deletion | do not keep as default guidance | merge any still-needed quick-start content into AIM 2.0, otherwise delete |
| `docs/workflow/release-aim-1.6.md` | AIM 1.6 release note | release history / internal build memory | keep as history, not current guidance | keep only as release history |
| `docs/workflow/release-aim-1.7.md` | AIM 1.7 release note / transition checklist | release history plus stale transition assumptions | not part of default guidance | absorb any still-needed release criteria into 2.0 authority, otherwise demote to history or delete |
| `docs/workflow/troubleshoot-aim-1.6.md` | 1.x troubleshooting guide | 1.x user-facing guidance slated for absorption or deletion | do not keep as default guidance | merge any still-needed troubleshooting into AIM 2.0 docs, otherwise delete |
| `docs/workflow/copilot-layer.md` | Adapter workflow doc | static AIM product / adapter doc | ship | keep |
| `docs/workflow/aim-adapter-guidance.md` | Adapter guidance | static AIM product | ship | keep |
| `docs/features/` | Feature contracts and build memory | mixed | not all default public product | split current product contracts from build memory in later increments |
| `docs/features/aim-2-*.md` | AIM 2.0 feature contracts and audits | mixed product contracts and build memory | selected files ship | classify individually before moving |
| `docs/features/aim-cost-*.md` | AIM 1.7 cost feature docs | fallback/product support | ship selectively | keep as fallback value, possibly merge into 2.0 cost docs later |
| `.github/agents/` | AIM agent instruction layer | static AIM product with repo instruction impact | ship as product/adapters | install only with collision checks |
| `.github/prompts/` | Copilot prompt helpers | adapter helper templates | optional ship | install only when target repo wants Copilot prompts |
| `.claude/` | Claude helper commands/agents | adapter helper templates | optional ship | install only when target repo wants Claude helpers |
| `adapters/codex/` | Codex skill package | static AIM product / adapter package | ship | keep as installable adapter package |
| `scripts/validate_aim_runtime.py` | Tooling / validator | static AIM product tooling | ship when runtime validation is desired | keep |
| `examples/` | Examples | static product examples | optional ship | keep out of minimal install by default |
| `.DS_Store` | Local OS artifact | local-only clutter | never ship | remove from repo if tracked or visible in product exports |

## Static versus repo-aware rule

Static AIM product files define AIM itself.
Repo-aware files adapt AIM to a target repository.

Do not install repo-aware files as if they were static product files.

Collision-prone repo-aware surfaces include:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`
- `.gitignore`
- `aim.profile.yaml`

Installer work must treat these as templates, merge targets, or explicit opt-in files.
They must not be blindly overwritten in user repositories.

## Shipped product surface

The clean AIM 2.0 shipped product surface should default to:

- `README.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `docs/workflow/aim-adapter-guidance.md`
- `docs/workflow/copilot-layer.md` when Copilot packaging is relevant
- selected current AIM 2.0 feature contracts
- `adapters/codex/agile-iteration-method/`
- `.github/agents/aim*.agent.md` as explicit AIM instruction-layer files
- `scripts/validate_aim_runtime.py` when runtime validation is part of the install

The shipped surface should not default to all historical workflow docs, all feature audits, all `.aim/` state, or all adapter helper examples.

## Internal build-memory surface

Internal build memory includes docs that helped AIM reach 2.0 but should not be the default user-facing product path.

Likely build-memory examples:

- release-readiness audits
- strategy drafts
- historical decision traces
- migration classification explanation docs once the behavior is stable elsewhere
- `.aim/decisions/`, `.aim/increments/`, and `.aim/reviews/`

Build memory may remain valuable for maintainers.
It should not survive as default user-facing guidance.

## AIM 1.x handling model

Use these decisions for remaining AIM 1.x material:

| Decision | Meaning | Examples |
| --- | --- | --- |
| delete | no longer useful after classification and not needed for a current migration bridge | tracked local clutter such as `.DS_Store` if present, or old 1.x user guidance after absorption |
| absorb into AIM 2.0 | content remains valuable but must live inside the current product surface | useful install, quick-start, troubleshooting, or routing content from 1.x docs |
| short-term migration bridge | temporary 1.x surface retained only because a concrete migration need still exists | a migration doc that is still actively needed while 2.0 absorbs its reusable parts |
| retain as internal build memory or release history | historical material that may matter to maintainers but is not current user guidance | old release notes or reference runs |
| redirect only as a temporary migration aid | a short-lived bridge that points to the 2.0 surface while removal is in progress | an old map or guide during a defined cleanup window |

No broad deletion should happen until the target decision is recorded for each affected file.
But user-facing 1.x guidance should not remain merely because it existed before.

## Installer surface basis

Future installer work should distinguish:

- AIM-owned static files: safe to install when the user chooses full product install
- repo-aware templates: install only with merge or collision prompts
- local runtime files: never install as product
- Team profile files: create or update only by explicit Team AIM choice
- adapter helpers: install only for selected adapters
- build memory: do not install by default

Never normal-install these as blind overwrites:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`
- `.gitignore`
- `aim.profile.yaml`

## Cleanup-ready recommendations

Immediate safe recommendations:

- keep `.aim/` local and ignored
- stop preserving user-facing AIM 1.x docs through decorative legacy labeling alone
- absorb still-needed 1.x guidance into AIM 2.0 surfaces, then delete the old files
- keep a 1.x file only when there is a concrete short-term migration reason or when it is clearly internal build memory or release history
- stop treating all `docs/features/` files as default public product
- treat `AGENTS.md` and `CLAUDE.md` as collision-prone instruction surfaces
- remove or ignore `.DS_Store` from any future shipped/exported surface
- prepare targeted absorption-or-deletion passes for remaining 1.x user-facing workflow docs

The next structural cleanups should be narrow: absorb or delete one 1.x user-facing surface at a time.

## Data correctness and trust

The classification must not redefine AIM authority.

It must preserve:

- AIM core loop
- Gate A/B/E semantics
- Done Increment discipline
- escalation rules
- ownership model
- `.aim/state.json` as runtime checkpoint

## Debugging

The best check is whether a maintainer can answer:

> Is this file product, repo-aware, runtime, build memory, or legacy?

- Primary check: `python3 scripts/validate_aim_runtime.py .`
- What good looks like: runtime state is healthy, `aim.profile.yaml` remains profile-only, and `.aim/` is not treated as product.
- What bad looks like: `.aim/` is proposed as shipped product, `AGENTS.md` is overwritten blindly, or user-facing AIM 1.x docs remain as default-path legacy guidance without a concrete migration reason.

## Related files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `aim.profile.yaml`
- `.aim/`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`
- `adapters/codex/agile-iteration-method/SKILL.md`
- `docs/workflow/`
- `docs/features/`
- `scripts/validate_aim_runtime.py`

## Change log

- 2026-06-05: Initial repository surface classification model and major-surface inventory.
- 2026-06-05: Tightened AIM 2.0 cleanup rule so user-facing 1.x docs must be absorbed into AIM 2.0, retained only for a concrete short-term migration bridge, or deleted.
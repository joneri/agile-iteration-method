# GitHub Pages Image Assets

Source images intended for the AIM website published from the `gh-pages` branch.

- `aim-2-hero-dark.png`: canonical dark, versionless AIM logo and website hero
  artwork
- `aim-4-logo.png`: AIM 4.0 campaign lockup, the original golden/blue A identity with
  navy AIM lettering and an expressive blue/cyan ribbon numeral 4 on a
  transparent background; 2172 × 724 RGBA PNG. Use on
  white or pale backgrounds. This versioned campaign asset is separate from
  the canonical versionless brand artwork.
- `AIM_OG.png` at the repository root: byte-identical versionless Open Graph
  artwork

Brand artwork version policy: versionless. The two brand-image files above must
remain byte-identical and contain no product version. The exact current release
from `VERSION` belongs in accessible alt text, visible HTML, metadata,
manifests, and release documentation outside the image pixels.
The approved source SHA-256 is
`75b1a6a632f311a377e4d6d3f70c75e1445d3183637c9eaa43524566fc5991c5`.

The versionless AIM brand artwork is the selected existing source image and is
copied without generation, retouching, recompression, or other transformation.

Keep only selected current publication assets here. Retired campaign artwork,
the earlier conceptual UI illustration and the Portfolio Auto demonstration
remain recoverable from Git history; they are not current website resources.

The AIM 4.0 campaign logo was generated using the built-in image generation
tool on 2026-10-12. Its exact prompt and provenance are recorded in
`../press/logo-generation.txt`. The selected PNG is copied unchanged into
this repository, with source SHA-256
`5e1cd88bed8e78b5dfe08238b24c9006d1dac9a85fcd56779c30eef6c97ff3d7`.
The downloadable `../press/aim-4-press-kit.zip` includes that same image,
English and Swedish launch drafts, product facts, usage notes and the
documentation licence. It is a reviewable press package, not a record of
publication. No vector master is included.

## AIM UI product capture

- `aim-control-board.png`: the actual AIM UI 4.1.0 User Stories Kanban
  board, captured at a 2160-pixel desktop browser width. All seven columns are
  visible: Backlog, Ready, In progress, Review, Validation, Acceptance and Done.
  The board contains six example booking Stories. Finding and booking are Done,
  cancellation awaits acceptance, rescheduling/calendar are Ready and reminders
  are in Backlog. The three active-work columns are empty at this checkpoint.

Captured with Chromium/Playwright on 12 October 2026 from this repository's
`aim-ui/` served by `scripts/aim_ui.py`. The isolated `booking-example` fixture
uses the installed Story helper to create synthetic requirements, plan authority,
review and acceptance records. Done cards illustrate state in the example;
they do not assert real user acceptance or a completed customer product.
The website explicitly labels the image as example data. The PNG is an unedited
browser capture of the whole board element at twice CSS pixel density
(4088 × 2150). No generated UI, annotations, retouching or private workspace
content is used. The Delivery control and narrow Acceptance-column images from
the earlier draft are no longer publication assets.

- `aim-ui-graph.png`: actual AIM UI 4.6.0 Graph view, captured on 19 October
  2026 by `python3 scripts/verify_aim_graph.py`. The isolated synthetic idea-wall
  fixture records a completed contract and two ready dependent activities while
  review waits. The inspector exposes file responsibility and assignment copying.
  This is the unedited `progress.png` browser capture (1410 × 1282), with no
  private project data, generated interface, retouching or claim of live activity.
  The website labels it as synthetic example data and a recorded snapshot.

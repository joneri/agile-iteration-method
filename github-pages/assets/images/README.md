# GitHub Pages Image Assets

Source images intended for the AIM website published through the validated GitHub Pages artifact.

- `aim-2-hero-dark.png`: canonical dark, versionless AIM logo and website hero
  artwork
- `aim-4-logo.png`: AIM 4.0 campaign lockup, the original golden/blue A identity with
  navy AIM lettering and an expressive blue/cyan ribbon numeral 4 on a
  transparent background; 2172 × 724 RGBA PNG. Use on
  white or pale backgrounds. This versioned campaign asset is separate from
  the canonical versionless brand artwork.
- `AIM_OG.png` at the repository root: retained byte-identical versionless
  brand artwork; current preview metadata uses the separate AIM 4 card below

Brand artwork version policy: versionless. The two brand-image files above must
remain byte-identical and contain no product version. The exact current release
from `VERSION` belongs in accessible alt text, visible HTML, metadata,
manifests, and release documentation outside the image pixels.
The approved source SHA-256 is
`75b1a6a632f311a377e4d6d3f70c75e1445d3183637c9eaa43524566fc5991c5`.

The versionless AIM brand artwork is the selected existing source image and is
copied without generation, retouching, recompression, or other transformation.

Keep current publication assets and explicitly identified historical captures here. Retired campaign artwork,
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

## Current AIM UI product captures

- `aim-ui-story-board.png`: unedited `ready.png` (1280 × 1243). Five columns,
  three synthetic order-recovery Stories: Backlog1, Ready2. The Recover an
  order card is expanded to show its criteria.
- `aim-ui-story-dependencies.png`: unedited `dependencies.png` (1280 × 848).
  Three Story nodes and one explicit prerequisite, Recover an order → Retain
  a draft. The selected draft inspector includes an unresolved owner input.

Captured 29 October 2026 from actual AIM UI 4.7.5 by the existing
`python3 scripts/verify_aim_graph.py --output output/playwright/current-graph-audit`
journey, using an isolated synthetic fixture and a real browser. The entry
verifies the current Story board and Graph, persisted lifecycle, owner waiting,
reload, mobile and reduced motion. These two images are different checkpoints
of the same run; they do not claim real customer work or owner acceptance.
No generated interface, retouching or private workspace data is used. The
website labels the examples and actual capture version/date explicitly. The
4.7.6 documentation correction does not change the captured UI behavior.

### Historical captures retained for existing URLs

The following images are no longer selected by the homepage or publication
capture contract. The 4.1.0 board has seven columns; the 4.6.0 graph shows the
former activity view. They remain byte-identical to preserve historical URLs
and can also be recovered from Git commit `c847794`:

- `aim-control-board.png`: SHA-256 `650a7bcbe890abb9f3f219723d6c6f35957fa95126e0aba9c9fe6b14a0cbec1a`.
- `aim-ui-graph.png`: SHA-256 `7afaaec182d9217fe006cb260eedff8da81c3804c027634234cada750b302dcb`.

## Current link preview and icon

- `aim-4-preview.png`: current 1200×630 Open Graph/Twitter/structured-data
  preview, composed from the unchanged approved AIM 4 logo and current product
  copy on white. The new URL separates it from the older cached artwork.
- `aim-icon.png`: square 192×192 browser/apple icon using the existing A mark.
  Its stable URL supports future recrawling. Google chooses one favicon per
  hostname; repository subpaths are not independent favicon sites.

Source composition: `scripts/assets/aim-preview.html`. Serve the repository
locally, open that file with Playwright at CSS pixel scale and screenshot
`#card` and `#icon` into the paths above. No new AI image, logo redesign or
retouching of the protected source artwork is involved. Rendered2026-10-29
with Edge/Playwright; the PNGs are reviewed publication assets, not dynamically
generated per request. External page/image caches may require a recrawl.

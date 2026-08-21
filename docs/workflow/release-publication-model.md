> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 Release And Publication Model

## Purpose

Define the canonical boundary between flexible local development and validated
public publication. Local work may be incomplete or temporarily broken. Public
Pages and release artifacts may not.

## Canonical Public Origin

The AIM GitHub Pages origin is:

```text
https://joneri.github.io/agile-iteration-method/
```

Published JSON Schema IDs use stable paths below that origin:

```text
https://joneri.github.io/agile-iteration-method/schemas/aim-repo-profile.schema.json
https://joneri.github.io/agile-iteration-method/schemas/aim-personal-hints.schema.json
https://joneri.github.io/agile-iteration-method/schemas/aim-runtime-state.schema.json
```

Schema `$id` values, source files, and assembled artifact paths must agree.

## Required Release Gate

`.github/workflows/release-readiness.yml` is the reusable release gate. It must
pass:

1. Python compilation
2. all committed tests
3. AIM validator health and release readiness in `--release` mode
4. schema structure and public-ID checks
5. installer and adapter package integrity
6. deterministic public artifact assembly and revalidation
7. deterministic public Agent Skill drift checks and isolated official skills
   CLI discovery/install validation

The workflow supports both `workflow_call` and `workflow_dispatch`. Pages calls
it before build. Maintainers may run it independently before a release.

`--release` mode treats the intentionally untracked local `.aim/` workspace as
optional while preserving product, schema, installer, adapter, coherence, and
publication checks. Normal validator mode still checks local resume state.

Release-gate failure does not prevent local edits, local tests, or local AIM
loops. It prevents public publication.

## Public Agent Skill

`skills/agile-iteration-method/` is AIM's portable Agent Skill distribution.
It is generated from canonical AIM sources by
`scripts/build_public_skill.py`; it is not an independently edited method
surface. Release readiness runs `python3 scripts/build_public_skill.py --check`
and rejects missing files, invalid frontmatter, local-reference drift,
inconsistent versions, non-deterministic output, or canonical changes that were
not regenerated.

The release gate also uses the pinned current official skills CLI to validate
repository discovery, copied project installs for Codex, GitHub Copilot, and
Claude Code, package closure, and `skills use` prompt generation in isolated
temporary repositories. Test installations disable telemetry and do not modify
the AIM development repository.

Publishing the skill requires no separate npm package or skills.sh upload. A
valid package on the public GitHub default branch plus one genuine installation
through the official CLI makes it eligible for skills.sh discovery. Anonymous
aggregate install telemetry may be indexed asynchronously and must never be
artificially inflated.

## GitHub Release Workflow

`.github/workflows/release.yml` publishes versioned release assets from an
existing `v*` tag. It must depend on the reusable release-readiness workflow
before packaging or uploading assets.

The release workflow publishes:

- `aim-pages-<version>.tar.gz`, the validated Pages artifact
- `aim-install-<version>.sh`, the public install bootstrap
- `aim-release-manifest-<version>.json`, the deterministic Pages release
  manifest

GitHub's source archives for the tag provide the installer, schemas, adapters,
docs, and license metadata used by the public bootstrap.

## Pages Artifact

`scripts/validate_publication.py --output <directory>` assembles the exact
release-facing Pages tree.

It includes:

- `VERSION`
- `install/aim-install-manifest.yaml`
- `index.html`
- `install.sh`
- `robots.txt`
- `sitemap.xml`
- `AIM_OG.png`
- `github-pages/assets/`
- all published JSON Schemas under `schemas/`, including runtime-state schema
  version `1.0`
- `LICENSE`
- documentation attribution at `licenses/LICENSE-DOCS`
- `.nojekyll`
- deterministic `release-manifest.json`

The release manifest records the AIM product release from `VERSION`, the stable
runtime contract version, runtime-state schema version, installer manifest
version, and published schema inventory. They must not be collapsed into one
number.

The builder validates source URLs before copying and validates the assembled
artifact afterward. Pages must use this builder rather than maintaining a
separate shell copy list.

`install.sh` is a compatibility tombstone for previously published links. It
must fail closed: it may print current safe installation guidance, but it must
not download, extract, or execute remote repository code.

The public website and README expose the standard portable skill command and a
reviewable source-checkout path for adaptive setup:

```bash
npx skills add joneri/agile-iteration-method --skill agile-iteration-method
git clone --depth 1 https://github.com/joneri/agile-iteration-method.git aim-source
```

## AIM 2.x release artifact

An official AIM 2.x release requires:

- a reviewed source commit
- a `v2`-family source tag pointing to that commit
- a successful release-readiness workflow for the tagged source
- a successful release workflow that creates or updates the GitHub Release for
  the tag
- source archives containing installer, validator, schemas, adapters, docs, and
  license metadata
- the validated release-facing artifact
- published schema URLs that return the tagged structural contracts
- release notes describing compatibility, migration, and known limitations

This model defines release readiness. It does not create or push a tag by
itself.

## License Boundary

Any distribution that includes AIM documentation must include attribution and
license context.

- Pages publishes `LICENSE` and `licenses/LICENSE-DOCS`.
- The installer `full` footprint installs source and documentation license
  metadata under the AIM-owned `docs/aim/` package path.
- Smaller footprints retain inline attribution in canonical documents and
  adapter packages; they do not claim to be a full documentation distribution.

## Public Claim Boundary

Release validation does not prove every marketing sentence. It does ensure the
public surface is not outside validation:

- canonical and Open Graph origins must match
- robots and sitemap origins must match
- required public files must exist
- schema IDs must match published paths
- public artifacts must include licenses
- Pages workflow must depend on the reusable gate

Semantic product-coherence checks remain the validator's responsibility.

## Development-Only Surfaces

These are not Pages or release payloads:

- `.aim/` runtime state
- Personal hints
- maintainer-only `CONTRIBUTING.md`
- temporary build output
- local caches
- unpublished analysis and working notes

## Verification

```sh
python3 -m compileall -q scripts tests
python3 -m unittest discover -s tests -v
python3 scripts/build_public_skill.py --check
python3 scripts/validate_public_skill_cli.py --source .
python3 scripts/validate_aim_runtime.py . --release
python3 scripts/validate_publication.py --output /tmp/aim-site
python3 scripts/validate_publication.py --output /tmp/aim-site --check-only
```

All commands must pass before public publication.

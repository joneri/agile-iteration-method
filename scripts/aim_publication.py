"""Build and validate AIM's release-facing GitHub Pages artifact."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


PUBLIC_ORIGIN = "https://joneri.github.io/agile-iteration-method/"
SCHEMA_RELATIVE_PATHS = (
    "schemas/aim-product-backlog.schema.json",
    "schemas/aim-repo-profile.schema.json",
    "schemas/aim-personal-hints.schema.json",
    "schemas/aim-runtime-state.schema.json",
    "schemas/aim-portfolio-run.schema.json",
    "schemas/aim-project-roles.schema.json",
    "schemas/aim-portfolio-control.schema.json",
    "schemas/aim-ui-backlog.schema.json",
    "schemas/aim-ui-portfolio.schema.json",
)
PUBLIC_EVALUATION_PATH = "docs/features/evidence/2026-10-18-enigma-comparison/comparison.json"
PUBLIC_NO_AIM_BASELINE_PATH = "docs/features/evidence/2026-09-30-luna-aim32-enigma/summary.json"
PUBLIC_EVALUATION_URL = "https://github.com/joneri/agile-iteration-method/blob/main/docs/features/aim-enigma-evaluation.md"
PUBLIC_NO_AIM_BASELINE_URL = "https://github.com/joneri/agile-iteration-method/blob/main/docs/features/aim-3.2-enigma-m3-case.md"
ROOT_PUBLIC_FILES = (
    "VERSION",
    "googlea5ce5061b9ad1e90.html",
    "install/aim-install-manifest.yaml",
    "index.html",
    "install.sh",
    "robots.txt",
    "sitemap.xml",
    "AIM_OG.png",
    "LICENSE",
    PUBLIC_EVALUATION_PATH,
    PUBLIC_NO_AIM_BASELINE_PATH,
)
PUBLIC_DIRECTORIES = ("github-pages/assets",)
PUBLIC_BRAND_IMAGE_PATHS = (
    "AIM_OG.png",
    "github-pages/assets/images/aim-2-hero-dark.png",
)
PUBLIC_BRAND_IMAGE_SIZE = (1730, 909)
PUBLIC_BRAND_IMAGE_SHA256 = (
    "75b1a6a632f311a377e4d6d3f70c75e1445d3183637c9eaa43524566fc5991c5"
)
VERSIONLESS_BRAND_ARTWORK_MARKER = "Brand artwork version policy: versionless"
PUBLIC_CAMPAIGN_IMAGE_PATH = "github-pages/assets/images/aim-4-logo.png"
PUBLIC_PREVIEW_IMAGE_PATH = "github-pages/assets/images/aim-4-preview.png"
PUBLIC_ICON_PATH = "github-pages/assets/images/aim-icon.png"
PUBLIC_CAMPAIGN_IMAGE_SIZE = (2172, 724)
PUBLIC_CAMPAIGN_IMAGE_SHA256 = (
    "5e1cd88bed8e78b5dfe08238b24c9006d1dac9a85fcd56779c30eef6c97ff3d7"
)
PUBLIC_SITE_ASSETS = ("github-pages/assets/aim4-site.css", "github-pages/assets/aim4-site.js")
PUBLIC_PRODUCT_CAPTURES = (
    "github-pages/assets/images/aim-ui-story-board.png",
    "github-pages/assets/images/aim-ui-story-dependencies.png",
)
PUBLIC_AGENT_INSTRUCTIONS_PATH = "github-pages/assets/aim-install-agent.txt"
PUBLIC_PRESS_KIT_PATH = "github-pages/assets/press/aim-4-press-kit.zip"
PUBLIC_PRESS_TEXT_PATH = "github-pages/assets/press/aim-4-press-kit.txt"
PUBLIC_PRESS_MEMBERS = {
    "aim-4-logo.png", "aim-4-press-kit.txt", "launch-copy-en.txt",
    "launch-copy-sv.txt", "logo-generation.txt", "LICENSE-DOCS.txt",
}
PUBLIC_LICENSE_PATH = "licenses/LICENSE-DOCS"
RELEASE_MANIFEST_PATH = "release-manifest.json"
PUBLIC_SKILL_INSTALL_COMMAND = (
    "npx skills add joneri/agile-iteration-method --skill agile-iteration-method"
)
PUBLIC_ADAPTIVE_SOURCE_COMMAND = (
    "git clone --depth 1 https://github.com/joneri/agile-iteration-method.git "
    "aim-source"
)


class PublicationError(ValueError):
    """Raised when source or assembled public artifacts violate the contract."""


class _Homepage(HTMLParser):
    """Read navigable publication assets without executing page content."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: set[str] = set()
        self.assets: set[str] = set()
        self.captures: list[dict[str, Any]] = []
        self.current_capture: dict[str, Any] | None = None
        self.in_caption = False
        self.evidence_version: str | None = None
        self.evidence_text = ""
        self.evidence_depth = 0
        self.metadata: dict[str, list[str | None]] = {}
        self.icons: dict[str, list[str | None]] = {}
        self.schema_text = ""
        self.in_schema = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            if key:
                self.metadata.setdefault(key, []).append(attributes.get("content"))
        if tag == "link":
            for rel in attributes.get("rel", "").lower().split():
                if rel in {"icon", "apple-touch-icon"}:
                    self.icons.setdefault(rel, []).append(attributes.get("href"))
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self.in_schema = True
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if attributes.get("id") == "evidence":
            self.evidence_version = attributes.get("data-evidence-version")
        if tag == "section":
            if attributes.get("id") == "evidence":
                self.evidence_depth = 1
            elif self.evidence_depth:
                self.evidence_depth += 1
        if tag == "figure" and "data-product-capture" in attributes:
            self.current_capture = {"kind": attributes["data-product-capture"], "images": [], "caption": ""}
            self.captures.append(self.current_capture)
        if tag == "figcaption":
            self.in_caption = True
        if tag == "a" and attributes.get("href"):
            self.links.add(attributes["href"])
        if tag == "script" and attributes.get("src"):
            self.assets.add(attributes["src"])
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.assets.add(attributes.get("href", ""))
        if tag == "img" and self.current_capture is not None:
            self.current_capture["images"].append(attributes)

    def handle_data(self, data: str) -> None:
        if self.in_schema:
            self.schema_text += data
        if self.in_caption and self.current_capture is not None:
            self.current_capture["caption"] += data
        if self.evidence_depth:
            self.evidence_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_schema = False
        if tag == "figure":
            self.current_capture = None
        if tag == "figcaption":
            self.in_caption = False
        if tag == "section" and self.evidence_depth:
            self.evidence_depth -= 1


def _evaluation_contract(root: Path) -> dict[str, Any]:
    try:
        evidence = json.loads(_read_text(root / PUBLIC_EVALUATION_PATH))
        rows = evidence["rows"]
        for prefix in ("latest", "reference"):
            version_key = "latestEvaluatedVersion" if prefix == "latest" else "referenceVersion"
            matches = [row for row in rows if row["version"] == evidence[version_key]]
            if len(matches) != 1:
                raise ValueError("an attributed scored row is required")
            score, headline = matches[0]["score"], evidence[prefix + "ProductScore"]
            if not all(type(value) in (int, float) and 0 <= value <= 100
                       for value in (score, headline)):
                raise ValueError("product scores must be finite numbers from 0 to 100")
            if headline != score:
                raise ValueError("headline score differs from its attributed row")
        return evidence
    except (KeyError, TypeError, ValueError) as exc:
        raise PublicationError(f"{PUBLIC_EVALUATION_PATH}: invalid evaluation attribution: {exc}") from exc


def _homepage_contract(root: Path) -> None:
    index = _read_text(root / "index.html")
    page = _Homepage()
    page.feed(index)
    for identifier in ("ui", "method", "start", "evidence", "press"):
        if identifier not in page.ids:
            raise PublicationError(f"index.html: required AIM 4 section is missing: {identifier}")
    for path in PUBLIC_PRODUCT_CAPTURES:
        if not (root / path).is_file():
            raise PublicationError(f"required AIM UI capture is missing: {path}")
        _png_dimensions(root / path)
        if not any(capture["kind"] == "example"
                   and "example" in capture["caption"].lower()
                   and any(image.get("src") == path and image.get("alt", "").strip()
                           for image in capture["images"])
                   for capture in page.captures):
            raise PublicationError(f"index.html: product capture needs alt text and an example caption: {path}")
    evidence = _evaluation_contract(root)
    if (page.evidence_version != evidence["latestEvaluatedVersion"]
            or evidence["referenceVersion"] not in page.evidence_text):
        raise PublicationError("index.html: comparison must identify the tested AIM version")
    if "-rc." in page.evidence_text.lower():
        raise PublicationError("index.html: release-candidate labels belong in linked test provenance, not marketing")
    if not {PUBLIC_EVALUATION_URL, PUBLIC_NO_AIM_BASELINE_URL} <= page.links:
        raise PublicationError("index.html: comparison must link to exact AIM and no-AIM test provenance")
    baseline = json.loads(_read_text(root / PUBLIC_NO_AIM_BASELINE_PATH))
    assessment = evidence["currentAssessment"]
    if (baseline["model"] != assessment["model"]
            or baseline["reasoningEffort"] != assessment["reasoningEffort"]
            or baseline["prdSha256"] != evidence["prdSha256"]):
        raise PublicationError("index.html: no-AIM baseline must use the same model, reasoning effort and brief")
    if (f'{baseline["publishedScoreOutOf100"]["naked"]:g} of 100' not in page.evidence_text
            or "GPT-6 Luna without AIM" not in page.evidence_text
            or "GPT-6 Luna with AIM" not in page.evidence_text):
        raise PublicationError("index.html: comparison must retain the no-AIM result and identify both conditions")
    for key in ("latestProductScore", "referenceProductScore"):
        if f'{evidence[key]:g} of 100' not in page.evidence_text:
            raise PublicationError("index.html: displayed assessment score differs from public evidence")
    version = product_version(root)
    if f'"softwareVersion": "{version}"' not in index:
        raise PublicationError(f"index.html: softwareVersion must match VERSION ({version})")
    for href in page.links:
        if href.startswith("#") and href[1:] not in page.ids:
            raise PublicationError(f"index.html: broken section link: {href}")
    for path in PUBLIC_SITE_ASSETS:
        if path not in page.assets or not (root / path).is_file():
            raise PublicationError(f"index.html: required interactive site asset is missing: {path}")
    for path in (PUBLIC_CAMPAIGN_IMAGE_PATH, PUBLIC_PRESS_KIT_PATH, PUBLIC_PRESS_TEXT_PATH,
                 PUBLIC_AGENT_INSTRUCTIONS_PATH):
        if path not in page.links or not (root / path).is_file():
            raise PublicationError(f"index.html: required press download is missing: {path}")


def _press_contract(root: Path, *, artifact: bool = False) -> None:
    try:
        with zipfile.ZipFile(root / PUBLIC_PRESS_KIT_PATH) as archive:
            if set(archive.namelist()) != PUBLIC_PRESS_MEMBERS or archive.testzip():
                raise PublicationError("AIM 4 press kit has missing, unexpected or corrupt members")
            for member in PUBLIC_PRESS_MEMBERS:
                if member == "aim-4-logo.png":
                    source = root / PUBLIC_CAMPAIGN_IMAGE_PATH
                elif member == "LICENSE-DOCS.txt":
                    source = root / (PUBLIC_LICENSE_PATH if artifact else "docs/LICENSE-DOCS")
                else:
                    source = root / "github-pages/assets/press" / member
                if not source.is_file() or archive.read(member) != source.read_bytes():
                    raise PublicationError(f"AIM 4 press kit does not match its source: {member}")
    except (OSError, zipfile.BadZipFile) as exc:
        raise PublicationError(f"AIM 4 press kit cannot be read: {exc}") from exc


def expected_schema_id(relative_path: str) -> str:
    return PUBLIC_ORIGIN + relative_path


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise PublicationError(f"required publication file is missing: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def _png_dimensions(path: Path) -> tuple[int, int]:
    if not path.is_file():
        raise PublicationError(f"required publication image is missing: {path}")
    header = path.read_bytes()[:24]
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise PublicationError(f"publication image is not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def _preview_contract(root: Path) -> None:
    """Current metadata must point to packaged, correctly sized preview assets."""
    page = _Homepage()
    page.feed(_read_text(root / "index.html"))
    image = PUBLIC_ORIGIN + PUBLIC_PREVIEW_IMAGE_PATH
    expected = {"og:image": image, "twitter:image": image,
                "og:image:type": "image/png", "og:image:width": "1200",
                "og:image:height": "630"}
    for name, value in expected.items():
        if page.metadata.get(name) != [value]:
            raise PublicationError(f"index.html: preview metadata {name} must be {value}")
    for name in ("og:image:alt", "twitter:image:alt"):
        values = page.metadata.get(name, [])
        if len(values) != 1 or not values[0] or not values[0].strip():
            raise PublicationError(f"index.html: preview metadata {name} needs alt text")
    try:
        schema = json.loads(page.schema_text)
    except (ValueError, TypeError) as exc:
        raise PublicationError("index.html: preview structured data must be valid JSON") from exc
    if not isinstance(schema, dict) or schema.get("image") != image:
        raise PublicationError("index.html: preview structured image must match Open Graph")
    for rel in ("icon", "apple-touch-icon"):
        if page.icons.get(rel) != [PUBLIC_ICON_PATH]:
            raise PublicationError(f"index.html: preview {rel} must use the current square icon")
    if _png_dimensions(root / PUBLIC_PREVIEW_IMAGE_PATH) != (1200, 630):
        raise PublicationError("preview image must be 1200x630")
    if _png_dimensions(root / PUBLIC_ICON_PATH) != (192, 192):
        raise PublicationError("preview icon must be square 192x192")


def _schema_contract(repo_root: Path, relative_path: str) -> dict[str, Any]:
    path = repo_root / relative_path
    try:
        schema = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise PublicationError(f"{relative_path}: invalid JSON: {exc.msg}") from exc
    expected_id = expected_schema_id(relative_path)
    if schema.get("$id") != expected_id:
        raise PublicationError(
            f"{relative_path}: $id must be {expected_id}, got {schema.get('$id')!r}"
        )
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise PublicationError(
            f"{relative_path}: unsupported or missing Draft 2020-12 declaration"
        )
    return schema


def validate_source(repo_root: Path) -> None:
    """Validate release-facing source files before artifact assembly."""

    repo_root = repo_root.resolve()
    product_version = _read_text(repo_root / "VERSION").strip()
    for relative_path in ROOT_PUBLIC_FILES:
        path = repo_root / relative_path
        if not path.is_file():
            raise PublicationError(
                f"required publication file is missing: {relative_path}"
            )
    if not (repo_root / "docs/LICENSE-DOCS").is_file():
        raise PublicationError(
            "required publication file is missing: docs/LICENSE-DOCS"
        )
    for relative_path in PUBLIC_DIRECTORIES:
        if not (repo_root / relative_path).is_dir():
            raise PublicationError(
                f"required publication directory is missing: {relative_path}"
            )
    for relative_path in SCHEMA_RELATIVE_PATHS:
        _schema_contract(repo_root, relative_path)
    for relative_path in PUBLIC_BRAND_IMAGE_PATHS:
        image_path = repo_root / relative_path
        dimensions = _png_dimensions(image_path)
        if dimensions != PUBLIC_BRAND_IMAGE_SIZE:
            raise PublicationError(
                f"{relative_path}: expected {PUBLIC_BRAND_IMAGE_SIZE[0]}x"
                f"{PUBLIC_BRAND_IMAGE_SIZE[1]}, got {dimensions[0]}x{dimensions[1]}"
            )
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest != PUBLIC_BRAND_IMAGE_SHA256:
            raise PublicationError(
                f"{relative_path}: brand artwork differs from the approved "
                "versionless source"
            )
    index = _read_text(repo_root / "index.html")
    expected_badge = '<span class="brand-version">Latest</span>'
    if expected_badge not in index:
        raise PublicationError(
            "index.html: brand-version must present the current AIM brand"
        )
    _homepage_contract(repo_root)
    _preview_contract(repo_root)
    _press_contract(repo_root)
    campaign_image = repo_root / PUBLIC_CAMPAIGN_IMAGE_PATH
    if _png_dimensions(campaign_image) != PUBLIC_CAMPAIGN_IMAGE_SIZE:
        raise PublicationError(f"{PUBLIC_CAMPAIGN_IMAGE_PATH}: unexpected dimensions")
    if (
        hashlib.sha256(campaign_image.read_bytes()).hexdigest()
        != PUBLIC_CAMPAIGN_IMAGE_SHA256
    ):
        raise PublicationError(f"{PUBLIC_CAMPAIGN_IMAGE_PATH}: campaign artwork changed")
    inventory = _read_text(repo_root / "github-pages/assets/images/README.md")
    if VERSIONLESS_BRAND_ARTWORK_MARKER not in inventory:
        raise PublicationError(
            "brand image inventory must declare the artwork versionless"
        )
    if "contain no product version" not in inventory:
        raise PublicationError(
            "brand image inventory must keep product versions outside artwork"
        )
    readme = _read_text(repo_root / "README.md")
    if "![AIM - Agile Iteration Method]" not in readme:
        raise PublicationError(
            "README.md: hero artwork alt text must use the AIM brand"
        )
    index = _read_text(repo_root / "index.html")
    install_script_path = repo_root / "install.sh"
    install_script = _read_text(install_script_path)
    robots = _read_text(repo_root / "robots.txt")
    sitemap = _read_text(repo_root / "sitemap.xml")
    if not install_script_path.stat().st_mode & 0o111:
        raise PublicationError("install.sh must be executable")
    forbidden_install_markers = {
        "install.sh must not download remote code": "curl ",
        "install.sh must not extract remote code": "tar ",
        "install.sh must not execute repository code": "scripts/aim_install.py",
        "install.sh must not contain pipe-to-shell guidance": "| bash",
    }
    for label, marker in forbidden_install_markers.items():
        if marker in install_script:
            raise PublicationError(label)
    required_public_markers = {
        "index.html canonical": (
            index,
            f'<link rel="canonical" href="{PUBLIC_ORIGIN}">',
        ),
        "index.html public Agent Skill install command": (
            index,
            PUBLIC_SKILL_INSTALL_COMMAND,
        ),
        "index.html adaptive source command": (
            index,
            PUBLIC_ADAPTIVE_SOURCE_COMMAND,
        ),
        "index.html public Agent Skill page": (
            index,
            "https://skills.sh/joneri/agile-iteration-method/agile-iteration-method",
        ),
        "index.html calibrate command": (
            index,
            "/aim calibrate-repo",
        ),
        "index.html remember command": (
            index,
            "/aim remember-repo",
        ),
        "index.html ordinary shared learning": (
            index,
            "Shared learning is part of ordinary delivery",
        ),
        "index.html retired command compatibility": (
            index,
            "retired compatibility aliases",
        ),
        "index.html AIM UI section": (
            index,
            'id="ui"',
        ),
        "index.html AIM UI guide": (
            index,
            "docs/product/aim-ui.md",
        ),
        "install.sh fail-closed notice": (
            install_script,
            "AIM remote bootstrap has been retired for security.",
        ),
        "index.html Open Graph URL": (
            index,
            f'<meta property="og:url" content="{PUBLIC_ORIGIN}">',
        ),
        "robots.txt sitemap": (
            robots,
            f"Sitemap: {PUBLIC_ORIGIN}sitemap.xml",
        ),
        "sitemap.xml location": (
            sitemap,
            f"<loc>{PUBLIC_ORIGIN}</loc>",
        ),
    }
    for label, (content, marker) in required_public_markers.items():
        if marker not in content:
            raise PublicationError(f"{label} does not match {PUBLIC_ORIGIN}")


def product_version(root: Path) -> str:
    version = _read_text(root / "VERSION").strip()
    if not version or any(part == "" for part in version.split(".")):
        raise PublicationError("VERSION must contain a dotted AIM product version")
    return version


def installer_manifest_version(root: Path) -> str:
    for line in _read_text(root / "install/aim-install-manifest.yaml").splitlines():
        if line.strip().startswith("manifestVersion:"):
            return line.split(":", 1)[1].strip().strip('"')
    raise PublicationError("installer manifest version is missing")


def runtime_state_schema_version(root: Path) -> str:
    schema = _schema_contract(root, "schemas/aim-runtime-state.schema.json")
    try:
        version = schema["properties"]["stateSchemaVersion"]["const"]
    except (KeyError, TypeError) as exc:
        raise PublicationError(
            "runtime-state schema version is missing"
        ) from exc
    if not isinstance(version, str) or not version:
        raise PublicationError("runtime-state schema version must be a string")
    return version


def release_manifest(root: Path) -> dict[str, Any]:
    return {
        "aimVersion": product_version(root),
        "runtimeContractVersion": "2.0",
        "runtimeStateSchemaVersion": runtime_state_schema_version(root),
        "productBacklogVersion": "1.0",
        "installerManifestVersion": installer_manifest_version(root),
        "aimUi": {
            "version": "1",
            "releaseStage": "beta",
            "availability": "public-skill-and-adaptive-installer",
            "chatLaunch": "/aim ui",
            "repoLaunch": "python3 scripts/aim_ui.py",
            "externalLaunch": (
                "python3 ~/.aim/installs/agile-iteration-method/scripts/aim_ui.py "
                "--repo /path/to/repository"
            ),
            "readOnly": True,
            "multiEpic": True,
            "cardActions": True,
            "defaultBoard": "increment",
            "crossEpicDeliveries": True,
        },
        "artifactType": "github-pages",
        "publicOrigin": PUBLIC_ORIGIN,
        "install": {
            "portableSkillCommand": PUBLIC_SKILL_INSTALL_COMMAND,
            "adaptiveSourceCommand": PUBLIC_ADAPTIVE_SOURCE_COMMAND,
            "adaptiveGuide": (
                "docs/workflow/install-aim-2.0.md"
            ),
            "remoteBootstrap": {
                "path": "install.sh",
                "status": "retired-fail-closed",
            },
        },
        "schemas": [
            {"path": path, "id": expected_schema_id(path)}
            for path in SCHEMA_RELATIVE_PATHS
        ],
        "licenses": ["LICENSE", PUBLIC_LICENSE_PATH],
        "requiredChecks": [
            "python-compile",
            "unit-tests",
            "aim-validator",
            "schema-contract",
            "adapter-package-closure",
            "publication-artifact",
        ],
    }


def build_artifact(repo_root: Path, output_root: Path) -> None:
    """Assemble and verify the exact directory uploaded to GitHub Pages."""

    repo_root = repo_root.resolve()
    output_root = output_root.resolve()
    if output_root == repo_root or output_root == repo_root / ".git":
        raise PublicationError("refusing unsafe publication output path")
    validate_source(repo_root)
    if output_root.exists():
        if any(output_root.iterdir()):
            raise PublicationError(
                f"refusing to replace nonempty publication output: {output_root}"
            )
        output_root.rmdir()
    output_root.mkdir(parents=True)

    for relative_path in ROOT_PUBLIC_FILES:
        destination = output_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_root / relative_path, destination)
    (output_root / "install.sh").chmod(0o755)
    for relative_path in PUBLIC_DIRECTORIES:
        shutil.copytree(repo_root / relative_path, output_root / relative_path)
    for relative_path in SCHEMA_RELATIVE_PATHS:
        destination = output_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_root / relative_path, destination)

    license_destination = output_root / PUBLIC_LICENSE_PATH
    license_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / "docs/LICENSE-DOCS", license_destination)
    (output_root / ".nojekyll").touch()
    (output_root / RELEASE_MANIFEST_PATH).write_text(
        json.dumps(release_manifest(repo_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    validate_artifact(output_root)


def validate_artifact(output_root: Path) -> None:
    """Validate the assembled Pages artifact without consulting source paths."""

    output_root = output_root.resolve()
    expected_files = {
        *ROOT_PUBLIC_FILES,
        *SCHEMA_RELATIVE_PATHS,
        PUBLIC_LICENSE_PATH,
        RELEASE_MANIFEST_PATH,
        ".nojekyll",
    }
    missing = [
        relative_path
        for relative_path in sorted(expected_files)
        if not (output_root / relative_path).is_file()
    ]
    if missing:
        raise PublicationError(
            "publication artifact is incomplete: " + ", ".join(missing)
        )
    for relative_path in PUBLIC_DIRECTORIES:
        if not (output_root / relative_path).is_dir():
            raise PublicationError(
                f"publication artifact is missing directory: {relative_path}"
            )
    for relative_path in PUBLIC_BRAND_IMAGE_PATHS:
        image_path = output_root / relative_path
        dimensions = _png_dimensions(image_path)
        if dimensions != PUBLIC_BRAND_IMAGE_SIZE:
            raise PublicationError(
                f"{relative_path}: expected {PUBLIC_BRAND_IMAGE_SIZE[0]}x"
                f"{PUBLIC_BRAND_IMAGE_SIZE[1]}, got {dimensions[0]}x{dimensions[1]}"
            )
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest != PUBLIC_BRAND_IMAGE_SHA256:
            raise PublicationError(
                f"{relative_path}: brand artwork differs from the approved "
                "versionless source"
            )
    _homepage_contract(output_root)
    _preview_contract(output_root)
    _press_contract(output_root, artifact=True)
    campaign_image = output_root / PUBLIC_CAMPAIGN_IMAGE_PATH
    if _png_dimensions(campaign_image) != PUBLIC_CAMPAIGN_IMAGE_SIZE:
        raise PublicationError(f"{PUBLIC_CAMPAIGN_IMAGE_PATH}: unexpected dimensions")
    if (
        hashlib.sha256(campaign_image.read_bytes()).hexdigest()
        != PUBLIC_CAMPAIGN_IMAGE_SHA256
    ):
        raise PublicationError(f"{PUBLIC_CAMPAIGN_IMAGE_PATH}: campaign artwork changed")
    for relative_path in SCHEMA_RELATIVE_PATHS:
        _schema_contract(output_root, relative_path)

    manifest_path = output_root / RELEASE_MANIFEST_PATH
    try:
        manifest = json.loads(_read_text(manifest_path))
    except json.JSONDecodeError as exc:
        raise PublicationError(
            f"{RELEASE_MANIFEST_PATH}: invalid JSON: {exc.msg}"
        ) from exc
    if manifest != release_manifest(output_root):
        raise PublicationError(
            f"{RELEASE_MANIFEST_PATH}: content differs from canonical release manifest"
        )

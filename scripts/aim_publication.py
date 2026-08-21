"""Build and validate AIM's release-facing GitHub Pages artifact."""

from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path
from typing import Any


PUBLIC_ORIGIN = "https://joneri.github.io/agile-iteration-method/"
SCHEMA_RELATIVE_PATHS = (
    "schemas/aim-repo-profile.schema.json",
    "schemas/aim-personal-hints.schema.json",
    "schemas/aim-runtime-state.schema.json",
)
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
)
PUBLIC_DIRECTORIES = ("github-pages/assets",)
PUBLIC_BRAND_IMAGE_PATHS = (
    "AIM_OG.png",
    "github-pages/assets/images/aim-2-hero-dark.png",
    "github-pages/assets/images/aim-2-logo-light.png",
)
PUBLIC_BRAND_IMAGE_SIZE = (1730, 909)
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
        dimensions = _png_dimensions(repo_root / relative_path)
        if dimensions != PUBLIC_BRAND_IMAGE_SIZE:
            raise PublicationError(
                f"{relative_path}: expected {PUBLIC_BRAND_IMAGE_SIZE[0]}x"
                f"{PUBLIC_BRAND_IMAGE_SIZE[1]}, got {dimensions[0]}x{dimensions[1]}"
            )
    image_readme = _read_text(repo_root / "github-pages/assets/images/README.md")
    if image_readme.count("AIM 2.3") < 2:
        raise PublicationError(
            "github-pages image inventory must identify both website assets as AIM 2.3"
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
        "index.html reflect command": (
            index,
            "/aim reflect",
        ),
        "index.html reflect-all command": (
            index,
            "/aim reflect-all",
        ),
        "index.html Reflect positioning": (
            index,
            "AIM Reflect goes beyond memory cleanup for repository work",
        ),
        "index.html audience-context integrity": (
            index,
            "Writes for the reader, not its own chat",
        ),
        "index.html AIM 2.3 logo alt text": (
            index,
            'alt="AIM 2.3 Agile Iteration Method logo"',
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
        "installerManifestVersion": installer_manifest_version(root),
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
        dimensions = _png_dimensions(output_root / relative_path)
        if dimensions != PUBLIC_BRAND_IMAGE_SIZE:
            raise PublicationError(
                f"{relative_path}: expected {PUBLIC_BRAND_IMAGE_SIZE[0]}x"
                f"{PUBLIC_BRAND_IMAGE_SIZE[1]}, got {dimensions[0]}x{dimensions[1]}"
            )
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

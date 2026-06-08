"""Build and validate AIM's release-facing GitHub Pages artifact."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


PUBLIC_ORIGIN = "https://joneri.github.io/agile-iteration-method/"
SCHEMA_RELATIVE_PATHS = (
    "schemas/aim-repo-profile.schema.json",
    "schemas/aim-personal-hints.schema.json",
)
ROOT_PUBLIC_FILES = (
    "index.html",
    "install.sh",
    "robots.txt",
    "sitemap.xml",
    "AIM_OG.png",
    "LICENSE",
)
PUBLIC_DIRECTORIES = ("github-pages/assets",)
PUBLIC_LICENSE_PATH = "licenses/LICENSE-DOCS"
RELEASE_MANIFEST_PATH = "release-manifest.json"
PUBLIC_INSTALL_COMMAND = f"curl -fsSL {PUBLIC_ORIGIN}install.sh | bash"


class PublicationError(ValueError):
    """Raised when source or assembled public artifacts violate the contract."""


def expected_schema_id(relative_path: str) -> str:
    return PUBLIC_ORIGIN + relative_path


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise PublicationError(f"required publication file is missing: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


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

    index = _read_text(repo_root / "index.html")
    install_script_path = repo_root / "install.sh"
    install_script = _read_text(install_script_path)
    robots = _read_text(repo_root / "robots.txt")
    sitemap = _read_text(repo_root / "sitemap.xml")
    if not install_script_path.stat().st_mode & 0o111:
        raise PublicationError("install.sh must be executable")
    required_public_markers = {
        "index.html canonical": (
            index,
            f'<link rel="canonical" href="{PUBLIC_ORIGIN}">',
        ),
        "index.html public install command": (
            index,
            PUBLIC_INSTALL_COMMAND,
        ),
        "install.sh default branch": (
            install_script,
            'AIM_REF="${AIM_REF:-${AIM_VERSION:-main}}"',
        ),
        "install.sh branch archive": (
            install_script,
            "archive/${AIM_REF}.tar.gz",
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


def release_manifest() -> dict[str, Any]:
    return {
        "aimVersion": "2.0",
        "artifactType": "github-pages",
        "publicOrigin": PUBLIC_ORIGIN,
        "install": {
            "path": "install.sh",
            "command": PUBLIC_INSTALL_COMMAND,
            "defaultRef": "main",
            "sourceArchive": "https://github.com/joneri/agile-iteration-method/archive/main.tar.gz",
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
        json.dumps(release_manifest(), indent=2, sort_keys=True) + "\n",
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
    for relative_path in SCHEMA_RELATIVE_PATHS:
        _schema_contract(output_root, relative_path)

    manifest_path = output_root / RELEASE_MANIFEST_PATH
    try:
        manifest = json.loads(_read_text(manifest_path))
    except json.JSONDecodeError as exc:
        raise PublicationError(
            f"{RELEASE_MANIFEST_PATH}: invalid JSON: {exc.msg}"
        ) from exc
    if manifest != release_manifest():
        raise PublicationError(
            f"{RELEASE_MANIFEST_PATH}: content differs from canonical release manifest"
        )

#!/usr/bin/env python3
"""Build and validate AIM's portable public Agent Skill package."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from aim_installer.yaml_lite import YamlLiteError, loads as load_yaml
from aim_publication import release_manifest


PUBLIC_SKILL_PACKAGE_VERSION = 3
OFFICIAL_SKILLS_CLI_VERSION = "1.5.17"
PACKAGE_RELATIVE_PATH = Path("skills/agile-iteration-method")
SKILL_SOURCE = Path("adapters/portable/agile-iteration-method/SKILL.md")
PUBLIC_DESCRIPTION_NAME = "agile-iteration-method"
REFERENCE_SOURCES: tuple[tuple[Path, Path], ...] = (
    (Path("docs/workflow/agile-iteration-method.md"), Path("agile-iteration-method.md")),
    (Path("docs/workflow/adapter-command-contract.md"), Path("adapter-command-contract.md")),
    (Path("docs/workflow/adapter-entry-model.md"), Path("adapter-entry-model.md")),
    (Path("docs/workflow/adapter-skill-bootstrap.md"), Path("adapter-skill-bootstrap.md")),
    (Path("docs/workflow/project-agent-configuration.md"), Path("project-agent-configuration.md")),
    (Path("docs/workflow/operating-modes.md"), Path("operating-modes.md")),
    (Path("docs/workflow/product-coherence-validation.md"), Path("product-coherence-validation.md")),
    (Path("docs/workflow/repo-awareness-calibration.md"), Path("repo-awareness-calibration.md")),
    (Path("docs/workflow/repo-awareness-two-layer-model.md"), Path("repo-awareness-two-layer-model.md")),
    (Path("docs/workflow/repo-awareness.md"), Path("repo-awareness.md")),
    (Path("docs/workflow/version-and-installation.md"), Path("version-and-installation.md")),
)

SCHEMA_SOURCES: tuple[Path, ...] = (
    Path("schemas/aim-repo-profile.schema.json"),
    Path("schemas/aim-personal-hints.schema.json"),
    Path("schemas/aim-project-roles.schema.json"),
)

INSTALL_MANIFEST_SOURCE = Path("install/aim-install-manifest.yaml")
DOCUMENTATION_LICENSE_SOURCE = Path("docs/LICENSE-DOCS")

GENERATED_NOTICE = (
    "GENERATED FILE. DO NOT EDIT DIRECTLY.\n"
    "Generated from canonical Agile Iteration Method sources.\n"
    "Regenerate with: python3 scripts/build_public_skill.py"
)


class PublicSkillError(ValueError):
    """Raised when the generated public skill would violate its contract."""


def _read(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.is_file():
        raise PublicSkillError(f"required canonical input is missing: {relative_path}")
    return path.read_text(encoding="utf-8")


def _sha256(content: str | bytes) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(payload).hexdigest()


def _frontmatter(source: str, source_path: str) -> tuple[dict[str, Any], str, str]:
    if not source.startswith("---\n"):
        raise PublicSkillError(f"{source_path}: missing YAML frontmatter")
    closing = source.find("\n---\n", 4)
    if closing == -1:
        raise PublicSkillError(f"{source_path}: unterminated YAML frontmatter")
    yaml_source = source[4:closing]
    try:
        parsed = load_yaml(yaml_source)
    except (YamlLiteError, IndexError) as exc:
        raise PublicSkillError(f"{source_path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PublicSkillError(f"{source_path}: frontmatter must be a mapping")
    for key in ("name", "description"):
        value = parsed.get(key)
        if not isinstance(value, str) or not value.strip():
            raise PublicSkillError(f"{source_path}: frontmatter {key!r} is required")
    return parsed, source[: closing + 5], source[closing + 5 :]


def _schema_version(schema: dict[str, Any], key: str, source_path: Path) -> str:
    def visit(value: Any) -> str | None:
        if isinstance(value, dict):
            properties = value.get("properties")
            if isinstance(properties, dict):
                candidate = properties.get(key)
                if isinstance(candidate, dict) and isinstance(candidate.get("const"), str):
                    return candidate["const"]
            for nested in value.values():
                found = visit(nested)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for nested in value:
                found = visit(nested)
                if found is not None:
                    return found
        return None

    result = visit(schema)
    if result is None:
        raise PublicSkillError(f"{source_path}: cannot resolve {key} version")
    return result


def resolved_versions(root: Path) -> dict[str, Any]:
    release = release_manifest(root)
    repo_schema = json.loads(_read(root, SCHEMA_SOURCES[0]))
    hints_schema = json.loads(_read(root, SCHEMA_SOURCES[1]))
    roles_schema = json.loads(_read(root, SCHEMA_SOURCES[2]))
    return {
        "productVersion": release["aimVersion"],
        "runtimeContractVersion": release["runtimeContractVersion"],
        "installerManifestVersion": release["installerManifestVersion"],
        "profileSchemaVersions": {
            "repoProfile": _schema_version(repo_schema, "profileVersion", SCHEMA_SOURCES[0]),
            "personalHints": _schema_version(hints_schema, "hintsVersion", SCHEMA_SOURCES[1]),
            "projectRoles": _schema_version(roles_schema, "profileVersion", SCHEMA_SOURCES[2]),
        },
        "publicSkillPackageVersion": PUBLIC_SKILL_PACKAGE_VERSION,
    }


def _workflow_link_rewriter(root: Path, *, from_skill: bool):
    selected = {source.name: output.as_posix() for source, output in REFERENCE_SOURCES}
    workflow_names = sorted(
        (path.name for path in (root / "docs/workflow").glob("*.md")),
        key=len,
        reverse=True,
    )
    if not workflow_names:
        raise PublicSkillError("canonical workflow directory contains no Markdown files")
    pattern = re.compile(
        r"(?<![A-Za-z0-9_./-])(?:docs/workflow/)?("
        + "|".join(re.escape(name) for name in workflow_names)
        + r")"
    )

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        target = selected.get(name)
        if target is not None:
            prefix = "references/" if from_skill else ""
            return prefix + target
        return "source-only/" + name

    return lambda content: pattern.sub(replace, content)


def _markdown_header(source: Path) -> str:
    return (
        "<!--\n"
        + GENERATED_NOTICE
        + f"\nSource: {source.as_posix()}\n-->\n\n"
    )


def _normalize_markdown_whitespace(content: str) -> str:
    """Preserve Markdown hard breaks without committing trailing spaces."""

    normalized: list[str] = []
    for line in content.splitlines():
        if line.endswith("  "):
            normalized.append(line.rstrip() + "<br>")
        else:
            normalized.append(line.rstrip())
    suffix = "\n" if content.endswith("\n") else ""
    return "\n".join(normalized) + suffix


def _rewrite_package_paths(content: str, *, from_skill: bool) -> str:
    """Translate source-checkout paths into installed-package paths."""

    skill_target = "SKILL.md" if from_skill else "../SKILL.md"
    content = content.replace(
        "adapters/codex/agile-iteration-method/SKILL.md",
        skill_target,
    )
    content = content.replace(
        "adapters/portable/agile-iteration-method/SKILL.md",
        skill_target,
    )
    content = content.replace(
        "install/aim-install-manifest.yaml",
        "references/install/aim-install-manifest.yaml"
        if from_skill
        else "install/aim-install-manifest.yaml",
    )
    content = content.replace(
        "scripts/validate_aim_runtime.py",
        "source-only validator tooling",
    )
    return content


def _render_skill(root: Path) -> tuple[str, dict[str, Any]]:
    source = _read(root, SKILL_SOURCE)
    metadata, yaml_block, body = _frontmatter(source, SKILL_SOURCE.as_posix())
    if metadata["name"] != PUBLIC_DESCRIPTION_NAME:
        raise PublicSkillError(
            f"{SKILL_SOURCE}: public skill name must be {PUBLIC_DESCRIPTION_NAME!r}"
        )
    rewritten = _workflow_link_rewriter(root, from_skill=True)(body)
    rewritten = _rewrite_package_paths(rewritten, from_skill=True)
    rewritten = _normalize_markdown_whitespace(rewritten)
    return yaml_block + "\n" + _markdown_header(SKILL_SOURCE) + rewritten.lstrip("\n"), metadata


def _render_reference(root: Path, source: Path, output: Path, versions: dict[str, Any]) -> str:
    content = _workflow_link_rewriter(root, from_skill=False)(_read(root, source))
    content = _rewrite_package_paths(content, from_skill=False)
    if output.name == "version-and-installation.md":
        content = content.split("## Generation and verification", 1)[0].rstrip() + "\n"
    content = _normalize_markdown_whitespace(content)
    header = _markdown_header(source)
    if output.name == "version-and-installation.md":
        schema_versions = versions["profileSchemaVersions"]
        header += (
            "## Resolved package metadata\n\n"
            f"- AIM product release: `{versions['productVersion']}`\n"
            f"- Runtime contract: `{versions['runtimeContractVersion']}`\n"
            f"- Installer manifest: `{versions['installerManifestVersion']}`\n"
            f"- Repo-profile schema: `{schema_versions['repoProfile']}`\n"
            f"- Personal-hints schema: `{schema_versions['personalHints']}`\n"
            f"- Project-role schema: `{schema_versions['projectRoles']}`\n"
            f"- Public skill package format: `{versions['publicSkillPackageVersion']}`\n\n"
        )
    return header + content


def _render_schema(root: Path, source: Path) -> str:
    try:
        schema = json.loads(_read(root, source))
    except json.JSONDecodeError as exc:
        raise PublicSkillError(f"{source}: invalid JSON: {exc.msg}") from exc
    if not isinstance(schema, dict):
        raise PublicSkillError(f"{source}: schema root must be an object")
    schema["$id"] = f"urn:aim:public-skill:{source.stem}"
    schema["$comment"] = GENERATED_NOTICE.replace("\n", " ")
    schema["x-aim-source"] = source.as_posix()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def _render_install_manifest(root: Path) -> str:
    content = _read(root, INSTALL_MANIFEST_SOURCE).replace(
        'canonicalCommand: "python3 scripts/aim_install.py"',
        'canonicalCommand: "source-only adaptive installer; not executable from the portable package"',
    )
    return (
        "# "
        + GENERATED_NOTICE.replace("\n", " ")
        + f"\n# Source: {INSTALL_MANIFEST_SOURCE.as_posix()}\n"
        + "# Data-only contract projection. The portable skill never executes this manifest.\n\n"
        + content
    )


def _source_provenance(root: Path) -> list[dict[str, str]]:
    mappings = [(SKILL_SOURCE, Path("SKILL.md"))]
    mappings.extend((source, Path("references") / output) for source, output in REFERENCE_SOURCES)
    mappings.extend((source, Path("references") / source) for source in SCHEMA_SOURCES)
    mappings.extend(
        (
            (INSTALL_MANIFEST_SOURCE, Path("references") / INSTALL_MANIFEST_SOURCE),
            (DOCUMENTATION_LICENSE_SOURCE, Path("references/LICENSE-DOCS")),
            (Path("VERSION"), Path("references/version-and-installation.md")),
            (Path("scripts/aim_publication.py"), Path("references/version-and-installation.md")),
            (Path("scripts/build_public_skill.py"), Path("manifest.json")),
        )
    )
    return [
        {
            "source": source.as_posix(),
            "output": output.as_posix(),
            "sha256": _sha256(_read(root, source)),
        }
        for source, output in mappings
    ]


def _render_package_once(root: Path) -> dict[Path, bytes]:
    root = root.resolve()
    versions = resolved_versions(root)
    skill, skill_metadata = _render_skill(root)
    rendered: dict[Path, bytes] = {Path("SKILL.md"): skill.encode("utf-8")}

    for source, output in REFERENCE_SOURCES:
        rendered[Path("references") / output] = _render_reference(
            root, source, output, versions
        ).encode("utf-8")
    for source in SCHEMA_SOURCES:
        rendered[Path("references") / source] = _render_schema(root, source).encode("utf-8")

    rendered[Path("references") / INSTALL_MANIFEST_SOURCE] = _render_install_manifest(
        root
    ).encode("utf-8")

    rendered[Path("references/LICENSE-DOCS")] = (
        GENERATED_NOTICE
        + f"\nSource: {DOCUMENTATION_LICENSE_SOURCE.as_posix()}\n\n"
        + _read(root, DOCUMENTATION_LICENSE_SOURCE)
    ).encode("utf-8")

    expected_files = sorted([path.as_posix() for path in rendered] + ["manifest.json"])
    manifest = {
        "description": skill_metadata["description"].strip(),
        "files": expected_files,
        "generatedNotice": GENERATED_NOTICE.replace("\n", " "),
        "generator": "python3 scripts/build_public_skill.py",
        "name": skill_metadata["name"],
        "officialSkillsCli": {
            "validatedVersion": OFFICIAL_SKILLS_CLI_VERSION,
            "installCommand": (
                "npx skills add joneri/agile-iteration-method "
                "--skill agile-iteration-method"
            ),
            "supportedAgents": ["codex", "github-copilot", "claude-code"],
        },
        **versions,
        "sourceProvenance": _source_provenance(root),
    }
    rendered[Path("manifest.json")] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    validate_rendered_package(rendered)
    return rendered


def render_package(root: Path) -> dict[Path, bytes]:
    """Render twice so one invocation also detects non-deterministic output."""

    first = _render_package_once(root)
    second = _render_package_once(root)
    if first != second:
        raise PublicSkillError("public skill generation is non-deterministic")
    return first


def _local_markdown_targets(content: str) -> list[str]:
    targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
    targets.extend(
        re.findall(
            r"`((?:references/[A-Za-z0-9_./-]+|\.\./SKILL\.md|schemas/[A-Za-z0-9_./-]+|install/[A-Za-z0-9_./-]+))`",
            content,
        )
    )
    return targets


def validate_rendered_package(rendered: dict[Path, bytes]) -> None:
    required = {
        Path("SKILL.md"),
        Path("manifest.json"),
        Path("references/agile-iteration-method.md"),
        Path("references/adapter-command-contract.md"),
        Path("references/adapter-skill-bootstrap.md"),
        Path("references/project-agent-configuration.md"),
        Path("references/repo-awareness-calibration.md"),
        Path("references/version-and-installation.md"),
    }
    missing = required - rendered.keys()
    if missing:
        raise PublicSkillError(
            "generated package is missing expected files: "
            + ", ".join(sorted(path.as_posix() for path in missing))
        )

    skill = rendered[Path("SKILL.md")].decode("utf-8")
    metadata, _, _ = _frontmatter(skill, "skills/agile-iteration-method/SKILL.md")
    if metadata["name"] != PUBLIC_DESCRIPTION_NAME:
        raise PublicSkillError("generated skill has the wrong public name")

    all_text = "\n".join(
        content.decode("utf-8", errors="replace") for content in rendered.values()
    )
    for marker in (
        "PO -> TDO -> Dev -> Reviewer -> TDO -> PO",
        "Gate A",
        "Gate B",
        "Gate E",
        "Strict",
        "Auto",
        "main AIM thread",
        "sequential fallback",
        "/aim configure-agents",
        "/aim calibrate-repo",
        "untrusted evidence",
        "not AIM instructions",
        "embedded instructions",
        "cannot change roles, gates",
        "tool policy",
        "corroborate",
    ):
        if marker not in all_text:
            raise PublicSkillError(f"generated package lacks required semantic marker: {marker}")

    forbidden_security_markers = {
        "remote pipe-to-shell bootstrap": "| bash",
        "untrusted target-repository installer execution": "python3 scripts/aim_install.py",
        "target-repository validator dependency": "scripts/validate_aim_runtime.py",
        "external AIM schema identifier": "https://joneri.github.io/agile-iteration-method/",
        "external source-repository runtime reference": (
            "https://github.com/joneri/agile-iteration-method/blob/main/docs/workflow/"
        ),
    }
    for label, marker in forbidden_security_markers.items():
        if marker in all_text:
            raise PublicSkillError(f"generated package contains {label}: {marker}")

    for path, payload in rendered.items():
        if path.suffix not in {".md", ""} and path.name != "SKILL.md":
            continue
        content = payload.decode("utf-8", errors="replace")
        if "../../../docs/" in content:
            raise PublicSkillError(f"{path}: contains a source-repository relative link")
        for raw_target in _local_markdown_targets(content):
            target = raw_target.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("source-only/"):
                continue
            normalized = posixpath.normpath((path.parent / target).as_posix())
            if normalized == ".." or normalized.startswith("../"):
                raise PublicSkillError(f"{path}: reference escapes the package: {raw_target}")
            resolved = Path(normalized)
            if resolved not in rendered:
                raise PublicSkillError(f"{path}: broken package-local reference: {raw_target}")

    manifest = json.loads(rendered[Path("manifest.json")])
    if manifest["files"] != sorted(path.as_posix() for path in rendered):
        raise PublicSkillError("manifest file inventory does not match generated output")
    for item in manifest["sourceProvenance"]:
        output = Path(item["output"])
        if output not in rendered:
            raise PublicSkillError(
                f"source provenance names an output that was not generated: {output}"
            )
    _validate_manifest_version_fields(manifest)


def _validate_manifest_version_fields(manifest: dict[str, Any]) -> None:
    for key in (
        "productVersion",
        "runtimeContractVersion",
        "installerManifestVersion",
    ):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise PublicSkillError(f"manifest {key} is missing")
    if manifest.get("publicSkillPackageVersion") != PUBLIC_SKILL_PACKAGE_VERSION:
        raise PublicSkillError("manifest public skill package version is inconsistent")
    schema_versions = manifest.get("profileSchemaVersions")
    if not isinstance(schema_versions, dict) or set(schema_versions) != {
        "repoProfile",
        "personalHints",
        "projectRoles",
    }:
        raise PublicSkillError("manifest profile schema versions are incomplete")


def write_package(root: Path, rendered: dict[Path, bytes], output: Path | None = None) -> None:
    root = root.resolve()
    package_root = (output or root / PACKAGE_RELATIVE_PATH).resolve()
    if package_root in {root, root / ".git"}:
        raise PublicSkillError(f"refusing unsafe public skill output path: {package_root}")
    if package_root.exists():
        shutil.rmtree(package_root)
    for relative_path, content in rendered.items():
        destination = package_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def validate_committed_package(root: Path) -> None:
    root = root.resolve()
    expected = render_package(root)
    package_root = root / PACKAGE_RELATIVE_PATH
    if not package_root.is_dir():
        raise PublicSkillError(f"generated public skill is missing: {PACKAGE_RELATIVE_PATH}")
    actual_paths = {
        path.relative_to(package_root)
        for path in package_root.rglob("*")
        if path.is_file()
    }
    expected_paths = set(expected)
    if actual_paths != expected_paths:
        missing = sorted(path.as_posix() for path in expected_paths - actual_paths)
        extra = sorted(path.as_posix() for path in actual_paths - expected_paths)
        raise PublicSkillError(
            f"generated package inventory drift; missing={missing or 'none'} extra={extra or 'none'}"
        )
    drift = [
        path.as_posix()
        for path, content in expected.items()
        if (package_root / path).read_bytes() != content
    ]
    if drift:
        raise PublicSkillError(
            "generated public skill is stale or manually edited: " + ", ".join(drift)
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed output without modifying files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.check:
            validate_committed_package(root)
            print("Public skill package is current, self-contained, and deterministic.")
        else:
            rendered = render_package(root)
            write_package(root, rendered)
            validate_committed_package(root)
            print(f"Generated {PACKAGE_RELATIVE_PATH} ({len(rendered)} files).")
    except (OSError, json.JSONDecodeError, PublicSkillError) as exc:
        print(f"public skill build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

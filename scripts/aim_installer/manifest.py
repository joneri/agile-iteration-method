"""Load and expose the AIM install manifest as structured data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import yaml_lite


MANIFEST_RELATIVE_PATH = "install/aim-install-manifest.yaml"


class ManifestError(ValueError):
    """Raised when the manifest is missing or structurally invalid."""


class Manifest:
    """Typed accessors over the parsed AIM install manifest."""

    def __init__(self, data: dict[str, Any], path: Path) -> None:
        root = data.get("aimInstallManifest")
        if not isinstance(root, dict):
            raise ManifestError(
                f"{path}: missing top-level 'aimInstallManifest' mapping"
            )
        self._root = root
        self.path = path

    @property
    def version(self) -> str:
        return str(self._root.get("manifestVersion", "unknown"))

    @property
    def canonical_command(self) -> str:
        return str(self._root.get("canonicalCommand", "python3 scripts/aim_install.py"))

    @property
    def modes(self) -> list[str]:
        return [str(m) for m in self._root.get("modes", [])]

    @property
    def legacy_modes(self) -> list[str]:
        return [str(m) for m in self._root.get("legacyModes", [])]

    @property
    def adapters(self) -> list[str]:
        return [str(a) for a in self._root.get("adapters", [])]

    @property
    def footprints(self) -> list[str]:
        return [str(f) for f in self._root.get("footprints", [])]

    @property
    def gitignore_fragments(self) -> list[str]:
        return [str(f) for f in self._root.get("gitignoreFragments", [])]

    @property
    def mode_profiles(self) -> dict[str, Any]:
        profiles = self._root.get("modeProfiles", {})
        return profiles if isinstance(profiles, dict) else {}

    def mode_profile(self, mode: str) -> dict[str, Any]:
        profile = self.mode_profiles.get(mode, {})
        return profile if isinstance(profile, dict) else {}

    @property
    def footprint_profiles(self) -> dict[str, Any]:
        profiles = self._root.get("footprintProfiles", {})
        return profiles if isinstance(profiles, dict) else {}

    def footprint_profile(self, footprint: str) -> dict[str, Any]:
        profile = self.footprint_profiles.get(footprint, {})
        return profile if isinstance(profile, dict) else {}

    @property
    def target_exclusions(self) -> list[dict[str, Any]]:
        return [e for e in self._root.get("targetExclusions", []) if isinstance(e, dict)]

    @property
    def excluded_root_files(self) -> list[str]:
        return [str(e["path"]) for e in self.target_exclusions if "path" in e]

    @property
    def package_boundaries(self) -> dict[str, Any]:
        boundaries = self._root.get("packageBoundaries", {})
        return boundaries if isinstance(boundaries, dict) else {}

    @property
    def adapter_closure(self) -> dict[str, Any]:
        closure = self._root.get("adapterClosure", {})
        return closure if isinstance(closure, dict) else {}

    @property
    def repo_awareness_bootstrap(self) -> dict[str, Any]:
        bootstrap = self._root.get("repoAwarenessBootstrap", {})
        return bootstrap if isinstance(bootstrap, dict) else {}

    @property
    def adapter_skills(self) -> dict[str, Any]:
        skills = self._root.get("adapterSkills", {})
        return skills if isinstance(skills, dict) else {}

    @property
    def runtime_exclusions(self) -> list[str]:
        return [str(e) for e in self._root.get("runtimeExclusions", [])]


def load_manifest(source_root: Path) -> Manifest:
    """Read and parse the manifest located under ``source_root``."""

    manifest_path = source_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise ManifestError(f"manifest not found: {manifest_path}")
    try:
        data = yaml_lite.loads(manifest_path.read_text(encoding="utf-8"))
    except yaml_lite.YamlLiteError as exc:
        raise ManifestError(f"{manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{manifest_path}: manifest root is not a mapping")
    return Manifest(data, manifest_path)

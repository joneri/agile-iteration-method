"""Small, deterministic documentation checks for AIM releases."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
TRACKED_HTML = {"article", "section", "div", "main", "nav", "header", "footer"}


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in TRACKED_HTML:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in TRACKED_HTML:
            return
        if not self.stack or self.stack[-1] != tag:
            expected = self.stack[-1] if self.stack else "nothing"
            self.errors.append(f"unexpected </{tag}>; expected </{expected}>")
            return
        self.stack.pop()


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def audit(repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    version = _text(repo_root / "VERSION").strip()
    readme = _text(repo_root / "README.md")
    changelog = _text(repo_root / "CHANGELOG.md")
    index = _text(repo_root / "index.html")
    features = _text(repo_root / "docs/product/features.md")

    required_version_markers = {
        "README.md": f"v{version}",
        "CHANGELOG.md": f"release v{version}",
        "index.html": f'"softwareVersion": "{version}"',
    }
    contents = {"README.md": readme, "CHANGELOG.md": changelog, "index.html": index}
    for path, marker in required_version_markers.items():
        if marker not in contents[path]:
            errors.append(f"{path}: missing current release marker {marker!r}")

    if len(readme.splitlines()) > 180:
        errors.append("README.md: public front door exceeds 180 lines")
    if "# Unreleased" in changelog or changelog.count(f"release v{version}") != 1:
        errors.append("CHANGELOG.md: current release must have one dated section and no stray Unreleased heading")
    for stale in ("Command-first", "Agent-first", "~/.codex/skills/agile-iteration-method"):
        if stale in index or stale in readme:
            errors.append(f"public front door contains stale marker: {stale}")

    required_features = (
        "Delivery loop", "Audience-context integrity", "Control and cost", "Repository knowledge",
        "AIM UI", "Reflect",
        "Project specialists", "Adapters and commands",
        "Installation and upgrades", "Validation and release safety",
    )
    for marker in required_features:
        if marker not in features:
            errors.append(f"docs/product/features.md: missing feature group {marker!r}")

    installation_contract = {
        "docs/workflow/codex-skill-onboarding.md": (
            "npx skills add joneri/agile-iteration-method",
            "/aim calibrate-repo",
            "/aim configure-agents",
            "adaptive installer",
        ),
        "docs/workflow/operating-modes.md": (
            "two maintained distribution paths",
            "public portable Agent Skill",
            "adaptive guided installer",
        ),
        "docs/workflow/aim-adapter-guidance.md": (
            "portable public Agent Skill",
            "adaptive guided installer",
            "npx skills add joneri/agile-iteration-method",
        ),
        "docs/workflow/install-aim-2.0.md": (
            "npx skills add joneri/agile-iteration-method",
            "One guided adaptive installer",
            "Public Agent Skill distribution",
        ),
        "docs/workflow/quick-start-aim-2.0.md": (
            "public Agent Skill",
            "/aim calibrate-repo",
            "/aim configure-agents",
            "does not claim those project files already exist",
        ),
    }
    for relative_path, markers in installation_contract.items():
        content = _text(repo_root / relative_path)
        normalized = " ".join(content.split())
        for marker in markers:
            if marker not in normalized:
                errors.append(
                    f"{relative_path}: missing installation-path marker {marker!r}"
                )

    security_guidance_paths = (
        "README.md",
        "index.html",
        "docs/product/getting-started.md",
        "docs/product/platforms-and-adoption.md",
        "docs/workflow/codex-skill-onboarding.md",
        "docs/workflow/install-aim-2.0.md",
        "docs/workflow/release-publication-model.md",
        "docs/workflow/version-and-installation.md",
    )
    for relative_path in security_guidance_paths:
        content = _text(repo_root / relative_path)
        if "| bash" in content:
            errors.append(
                f"{relative_path}: remote pipe-to-shell installation is forbidden"
            )

    if "Collision protection" in index:
        errors.append(
            "index.html: internal installer jargon must not appear: "
            "'Collision protection'"
        )
    if "Preview before changes" not in index:
        errors.append(
            "index.html: missing plain-language setup benefit "
            "'Preview before changes'"
        )

    markdown_files = [repo_root / "README.md", *sorted((repo_root / "docs").rglob("*.md"))]
    for path in markdown_files:
        for target in LINK_RE.findall(_text(path)):
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean or "://" in clean or clean.startswith(("mailto:", "/")):
                continue
            if not (path.parent / clean).resolve().exists():
                errors.append(f"{path.relative_to(repo_root)}: broken link {target}")

    parser = StructureParser()
    parser.feed(index)
    parser.close()
    errors.extend(f"index.html: {error}" for error in parser.errors)
    if parser.stack:
        errors.append("index.html: unclosed structural tags: " + ", ".join(parser.stack))
    return errors

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
        "Delivery loop", "Control and cost", "Repository knowledge",
        "Project specialists", "Adapters and commands",
        "Installation and upgrades", "Validation and release safety",
    )
    for marker in required_features:
        if marker not in features:
            errors.append(f"docs/product/features.md: missing feature group {marker!r}")

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

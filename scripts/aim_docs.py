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
    unreadable: set[Path] = set()

    def read(path: Path) -> str:
        try:
            return _text(path)
        except OSError as exc:
            if path not in unreadable:
                errors.append(f"{path.relative_to(repo_root)}: cannot read required surface ({type(exc).__name__})")
                unreadable.add(path)
            return ""

    version = read(repo_root / "VERSION").strip()
    readme = read(repo_root / "README.md")
    changelog = read(repo_root / "CHANGELOG.md")
    index = read(repo_root / "index.html")
    features = read(repo_root / "docs/product/features.md")

    required_version_markers = {
        "README.md": "[VERSION](VERSION)",
        "CHANGELOG.md": f"release v{version}",
        "index.html": f'"softwareVersion": "{version}"',
    }
    contents = {"README.md": readme, "CHANGELOG.md": changelog, "index.html": index}
    for path, marker in required_version_markers.items():
        if marker not in contents[path]:
            errors.append(f"{path}: missing current release marker {marker!r}")

    if len(readme.splitlines()) > 180:
        errors.append("README.md: public front door exceeds 180 lines")
    release_heading = rf"^## \d{{4}}-\d{{2}}-\d{{2}} - AIM release v{re.escape(version)}[ \t]*$"
    if "# Unreleased" in changelog or len(re.findall(release_heading, changelog, re.MULTILINE)) != 1:
        errors.append("CHANGELOG.md: current release must have one dated section and no stray Unreleased heading")
    for stale in ("Command-first", "Agent-first", "~/.codex/skills/agile-iteration-method"):
        if stale in index or stale in readme:
            errors.append(f"public front door contains stale marker: {stale}")

    required_features = (
        "Delivery loop", "Audience-context integrity", "Control and cost", "Repository knowledge",
        "AIM UI", "Discuss", "Shared learning",
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
        content = read(repo_root / relative_path)
        normalized = " ".join(content.split())
        for marker in markers:
            if marker not in normalized:
                errors.append(
                    f"{relative_path}: missing installation-path marker {marker!r}"
                )

    # Check current claims locally; historical release and capture labels stay intact.
    release_url = f"https://github.com/joneri/agile-iteration-method/releases/tag/v{version}"
    current_publication = {
        "index.html": (release_url, f"AIM {version} is available now."),
        "docs/product/platforms-and-adoption.md": (release_url,),
        "github-pages/assets/press/aim-4-press-kit.txt": (f"Release version: {version}\n", release_url),
        "github-pages/assets/press/launch-copy-en.txt": (f"AIM {version} ·",),
        "github-pages/assets/press/launch-copy-sv.txt": (f"AIM {version} ·",),
    }
    for relative, markers in current_publication.items():
        content = read(repo_root / relative)
        for marker in markers:
            if marker not in content:
                errors.append(f"{relative}: stale current release claim; expected {marker!r}")

    for relative in ("docs/product/README.md", "docs/product/what-is-aim.md", "docs/product/features.md"):
        content = read(repo_root / relative)
        for feature in ("Ship", "Loop", "Graph"):
            if not re.search(rf"\b{feature}\b", content):
                errors.append(f"{relative}: missing current delivery feature {feature!r}")

    routing_guides = (
        "docs/workflow/agile-iteration-method.md",
        "docs/workflow/aim-adapter-guidance.md",
        "docs/workflow/adapter-skill-bootstrap.md",
        "docs/workflow/repo-awareness.md",
        "docs/workflow/working-state-boundaries.md",
        "docs/workflow/troubleshoot-aim-2.0.md",
        "docs/workflow/epic-closure-truth-audit.md",
        "docs/workflow/project-agent-configuration.md",
        *(f".claude/commands/{command}-aim.md" for command in ("continue", "status", "config", "mode", "cost")),
    )
    for relative in routing_guides:
        if not (repo_root / relative).is_file():
            errors.append(f"{relative}: missing runtime source routing guide")
            continue
        if "adapter-command-contract.md#runtime-source-routing" not in read(repo_root / relative):
            errors.append(f"{relative}: missing current/legacy runtime source routing contract")

    onboarding = read(repo_root / "docs/workflow/codex-skill-onboarding.md")
    if re.search(r"scripts/aim_install\.py\s+--target\s+['\"]?\.['\"]?(?=\s|$)", onboarding):
        errors.append("docs/workflow/codex-skill-onboarding.md: source checkout cannot install into itself")

    contract = read(repo_root / "docs/workflow/adapter-command-contract.md")
    required_commands = set(re.findall(r"^\| `/aim ([a-z-]+)(?:[^`]*?)` \|", contract, re.MULTILINE))
    for relative in ("docs/workflow/adapter-entry-model.md", "docs/workflow/adapter-skill-bootstrap.md"):
        commands = set(re.findall(r"`/aim ([a-z-]+)`", read(repo_root / relative)))
        missing = sorted(required_commands - commands)
        if missing:
            errors.append(f"{relative}: incomplete command family; missing {', '.join(missing)}")

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
        content = read(repo_root / relative_path)
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
        for target in LINK_RE.findall(read(path)):
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

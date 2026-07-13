"""Resolve required canonical-document references for adapter packages."""

from __future__ import annotations

import re
from pathlib import Path


WORKFLOW_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])(docs/workflow/[A-Za-z0-9._/-]+\.md)"
)
PACKAGE_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])(references/[A-Za-z0-9._/-]+\.md)"
)


def _references(path: Path, pattern: re.Pattern[str]) -> set[str]:
    if not path.is_file():
        return set()
    content = path.read_text(encoding="utf-8", errors="replace")
    return {match.group(1) for match in pattern.finditer(content)}


def adapter_surface_files(
    source_root: Path, adapter: str, include_optional: bool
) -> list[Path]:
    """Return the files installed as the selected adapter's instruction surface."""

    if adapter == "codex":
        base = source_root / "adapters/codex/agile-iteration-method"
        return sorted(
            (path for path in base.rglob("*") if path.is_file()),
            key=lambda path: path.as_posix(),
        )
    if adapter == "claude":
        files = [
            path
            for subdir in ("agents", "commands")
            for path in (source_root / ".claude" / subdir).glob("*.md")
            if path.is_file()
        ]
        files.extend(
            path
            for path in (source_root / ".claude" / "skills").rglob("*")
            if path.is_file()
        )
        return sorted(files, key=lambda path: path.as_posix())
    if adapter == "copilot":
        files = list((source_root / ".github/agents").glob("aim*.agent.md"))
        files.extend(
            path
            for path in (source_root / ".github" / "skills" / "aim").rglob("*")
            if path.is_file()
        )
        if include_optional:
            files.extend((source_root / ".github/prompts").glob("*.prompt.md"))
        return sorted(
            (path for path in files if path.is_file()),
            key=lambda path: path.as_posix(),
        )
    return []


def required_workflow_docs(
    source_root: Path, adapter: str, include_optional: bool
) -> set[str]:
    """Return canonical source docs directly required by installed instructions."""

    required: set[str] = set()
    for path in adapter_surface_files(source_root, adapter, include_optional):
        required.update(_references(path, WORKFLOW_REFERENCE_RE))
        if adapter == "codex":
            required.update(
                f"docs/workflow/{Path(reference).name}"
                for reference in _references(path, PACKAGE_REFERENCE_RE)
            )
    return required


def package_reference_for(source_doc: str) -> str:
    """Map a canonical workflow source to its Codex package-local reference."""

    return f"references/{Path(source_doc).name}"

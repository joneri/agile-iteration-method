"""Compute a dry-run install plan from manifest + source/target inspection.

The plan is read-only: it never writes to the target repository. Each action
carries explicit ``source``, ``destination``, and ``reason`` fields so the
later apply/rollback increment can act on the same structure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import Manifest
from . import guidance, seed


PLAN_SCHEMA_VERSION = "1"

# Generic root files AIM must never create, modify, or read in a target repo.
GENERIC_ROOT_FILES = ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md")

CLASSIFICATIONS = ("create", "modify", "untouched", "collision")
CATEGORIES = ("file", "bootstrap", "ignore", "package")


class PlanError(ValueError):
    """Raised when an unsafe or impossible plan is requested."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _classify_copy(source_path: Path, dest_path: Path) -> str:
    if not dest_path.exists():
        return "create"
    try:
        if source_path.read_bytes() == dest_path.read_bytes():
            return "untouched"
    except OSError:
        return "collision"
    return "collision"


def _classify_content(dest_path: Path, desired: str) -> str:
    if not dest_path.exists():
        return "create"
    if dest_path.read_text(encoding="utf-8") == desired:
        return "untouched"
    return "collision"


def _classify_gitignore(target_root: Path, fragments: list[str]) -> str:
    dest_path = target_root / ".gitignore"
    if not dest_path.exists():
        return "create"
    existing = dest_path.read_text(encoding="utf-8").splitlines()
    existing_stripped = {line.strip() for line in existing}
    missing = [f for f in fragments if f not in existing_stripped]
    return "untouched" if not missing else "modify"


def _action(
    *,
    action_id: str,
    category: str,
    classification: str,
    source: str | None,
    destination: str,
    reason: str,
    adapter: str,
    optional: bool,
    scope: str = "repo",
) -> dict[str, Any]:
    return {
        "id": action_id,
        "category": category,
        "classification": classification,
        "source": source,
        "destination": destination,
        "reason": reason,
        "adapter": adapter,
        "optional": optional,
        "scope": scope,
        "stale": classification == "collision",
    }


def _sorted_glob(base: Path, pattern: str) -> list[Path]:
    return sorted(base.glob(pattern), key=lambda p: p.name)


def _canonical_doc_actions(source_root: Path, target_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    docs_dir = source_root / "docs" / "workflow"
    for doc in _sorted_glob(docs_dir, "*.md"):
        rel = f"docs/workflow/{doc.name}"
        actions.append(
            _action(
                action_id=rel,
                category="file",
                classification=_classify_copy(doc, target_root / rel),
                source=rel,
                destination=rel,
                reason="Canonical AIM workflow documentation (target-owned)",
                adapter="core",
                optional=False,
            )
        )
    return actions


def _copilot_actions(
    source_root: Path, target_root: Path, include_optional: bool
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for agent in _sorted_glob(source_root / ".github" / "agents", "aim*.agent.md"):
        rel = f".github/agents/{agent.name}"
        actions.append(
            _action(
                action_id=rel,
                category="file",
                classification=_classify_copy(agent, target_root / rel),
                source=rel,
                destination=rel,
                reason="Copilot AIM agent package",
                adapter="copilot",
                optional=False,
            )
        )
    if not include_optional:
        return actions
    for prompt in _sorted_glob(source_root / ".github" / "prompts", "*.prompt.md"):
        rel = f".github/prompts/{prompt.name}"
        actions.append(
            _action(
                action_id=rel,
                category="file",
                classification=_classify_copy(prompt, target_root / rel),
                source=rel,
                destination=rel,
                reason="Copilot AIM prompt helpers (optional secondary surface)",
                adapter="copilot",
                optional=True,
            )
        )
    return actions


def _claude_actions(source_root: Path, target_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for subdir in ("agents", "commands"):
        source_dir = source_root / ".claude" / subdir
        for item in _sorted_glob(source_dir, "*.md"):
            rel = f".claude/{subdir}/{item.name}"
            actions.append(
                _action(
                    action_id=rel,
                    category="package",
                    classification=_classify_copy(item, target_root / rel),
                    source=rel,
                    destination=rel,
                    reason="Claude AIM package (agents/commands)",
                    adapter="claude",
                    optional=False,
                )
            )
    return actions


def _codex_actions(source_root: Path, home_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    base = source_root / "adapters" / "codex" / "agile-iteration-method"
    dest_base = home_root / ".codex" / "skills" / "agile-iteration-method"
    for item in sorted(base.rglob("*"), key=lambda p: p.as_posix()):
        if not item.is_file():
            continue
        rel = item.relative_to(base).as_posix()
        dest = dest_base / rel
        actions.append(
            _action(
                action_id=f"codex:{rel}",
                category="package",
                classification=_classify_copy(item, dest),
                source=item.relative_to(source_root).as_posix(),
                destination=str(dest),
                reason="Codex skill package (user-home install)",
                adapter="codex",
                optional=False,
                scope="home",
            )
        )
    return actions


def _bootstrap_actions(
    target_root: Path, manifest: Manifest, committed: bool
) -> list[dict[str, Any]]:
    bootstrap = manifest.repo_awareness_bootstrap
    shared_profile = str(bootstrap.get("sharedProfile", "aim.profile.yaml"))
    if not committed:
        # Personal mode: repo-awareness lives in local personal hints, not the repo.
        return []
    return [
        _action(
            action_id=shared_profile,
            category="bootstrap",
            classification=_classify_content(
                target_root / shared_profile, seed.shared_profile_seed()
            ),
            source=None,
            destination=shared_profile,
            reason="Seed shared repo-awareness profile (needs calibration, not 'ready')",
            adapter="core",
            optional=False,
        )
    ]


def _ignore_actions(
    target_root: Path, manifest: Manifest, fragments: list[str]
) -> list[dict[str, Any]]:
    fragments = fragments or manifest.gitignore_fragments or manifest.runtime_exclusions
    return [
        _action(
            action_id=".gitignore",
            category="ignore",
            classification=_classify_gitignore(target_root, fragments),
            source=None,
            destination=".gitignore",
            reason="Ignore AIM runtime state (" + ", ".join(fragments) + ")",
            adapter="core",
            optional=False,
        )
    ]


def _root_file_exclusions(manifest: Manifest) -> list[dict[str, str]]:
    reasons = {
        str(e["path"]): str(e.get("reason", "AIM root-file exclusion"))
        for e in manifest.target_exclusions
        if "path" in e
    }
    excluded: list[dict[str, str]] = []
    seen: set[str] = set()
    for name in list(GENERIC_ROOT_FILES) + manifest.excluded_root_files:
        if name in seen:
            continue
        seen.add(name)
        excluded.append(
            {
                "path": name,
                "reason": reasons.get(
                    name, "Generic root file: AIM must never create/modify/read it"
                ),
            }
        )
    return excluded


def _assert_root_files_untouched(
    actions: list[dict[str, Any]], excluded: list[dict[str, str]]
) -> None:
    forbidden = {entry["path"] for entry in excluded}
    for action in actions:
        for field in ("source", "destination"):
            value = action.get(field)
            if value and Path(value).name in forbidden:
                raise PlanError(
                    f"plan would touch excluded root file via {field}: {value}"
                )


def _summarize(actions: list[dict[str, Any]]) -> dict[str, Any]:
    by_classification = {c: 0 for c in CLASSIFICATIONS}
    by_category = {c: 0 for c in CATEGORIES}
    for action in actions:
        by_classification[action["classification"]] = (
            by_classification.get(action["classification"], 0) + 1
        )
        by_category[action["category"]] = by_category.get(action["category"], 0) + 1
    return {
        "total": len(actions),
        "byClassification": by_classification,
        "byCategory": by_category,
    }


def compute_plan(
    *,
    source_root: Path,
    target_root: Path,
    mode: str,
    adapters: list[str],
    manifest: Manifest,
    validator_result: dict[str, object],
    home_root: Path | None = None,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    """Build the dry-run install plan dictionary."""

    blockers = list(blockers or [])
    home_root = home_root or Path.home()
    mode_profile = manifest.mode_profile(mode)
    committed = bool(mode_profile.get("committedSharedProfile", True))
    include_optional = bool(mode_profile.get("includeOptionalSurfaces", True))
    enterprise_safe = bool(mode_profile.get("enterpriseSafe", False))
    mode_fragments = [str(f) for f in mode_profile.get("gitignore", [])]

    actions: list[dict[str, Any]] = []
    actions.extend(_canonical_doc_actions(source_root, target_root))
    if "copilot" in adapters:
        actions.extend(_copilot_actions(source_root, target_root, include_optional))
    if "claude" in adapters:
        actions.extend(_claude_actions(source_root, target_root))
    if "codex" in adapters:
        actions.extend(_codex_actions(source_root, home_root))
    actions.extend(_bootstrap_actions(target_root, manifest, committed))
    fragments = mode_fragments or manifest.gitignore_fragments or manifest.runtime_exclusions
    actions.extend(_ignore_actions(target_root, manifest, fragments))

    excluded = _root_file_exclusions(manifest)
    _assert_root_files_untouched(actions, excluded)

    bootstrap = manifest.repo_awareness_bootstrap
    plan = {
        "planSchemaVersion": PLAN_SCHEMA_VERSION,
        "manifestVersion": manifest.version,
        "generatedAt": _now_iso(),
        "operation": "dry-run",
        "mode": mode,
        "modeProfile": {
            "committedSharedProfile": committed,
            "includeOptionalSurfaces": include_optional,
            "enterpriseSafe": enterprise_safe,
        },
        "gitignoreFragments": fragments,
        "adapters": adapters,
        "source": str(source_root),
        "target": str(target_root),
        "validator": validator_result,
        "bootstrap": {
            "status": "needs_calibration",
            "storage": "committed-shared-profile" if committed else "personal-local-only",
            "readyRequiresCalibration": bool(
                bootstrap.get("readyRequiresCalibration", True)
            ),
            "sharedProfile": str(bootstrap.get("sharedProfile", "aim.profile.yaml")),
            "personalHints": str(
                bootstrap.get(
                    "personalHints",
                    "~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml",
                )
            ),
            "calibrationCommand": str(
                bootstrap.get("calibrationCommand", "/aim calibrate-repo")
            ),
            "note": "Bootstrap never reports 'ready'; run calibration after install.",
        },
        "rootFileExclusions": excluded,
        "actions": actions,
        "summary": _summarize(actions),
        "stalePackages": [
            a["id"]
            for a in actions
            if a["category"] == "package" and a["stale"]
        ],
        "blockers": blockers,
        "applyAllowed": False,
    }
    plan["guidance"] = guidance.build_guidance(plan)
    plan["installState"] = plan["guidance"]["installState"]
    return plan

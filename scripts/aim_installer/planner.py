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
from . import closure, guidance, seed


PLAN_SCHEMA_VERSION = "2"

# Generic root files AIM must never create, modify, or read in a target repo.
GENERIC_ROOT_FILES = ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md")

CLASSIFICATIONS = ("create", "modify", "untouched", "collision")
CATEGORIES = ("file", "bootstrap", "ignore", "package")
EXTERNAL_DISTRIBUTION_DEST = ".aim/installs/agile-iteration-method"


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


def _selected_canonical_doc_actions(
    source_root: Path,
    target_root: Path,
    required_docs: set[str],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for rel in sorted(required_docs):
        source_path = source_root / rel
        if not source_path.is_file():
            raise PlanError(f"required adapter contract is missing: {rel}")
        actions.append(
            _action(
                action_id=rel,
                category="file",
                classification=_classify_copy(source_path, target_root / rel),
                source=rel,
                destination=rel,
                reason="Required canonical contract for selected AIM adapter",
                adapter="core",
                optional=False,
            )
        )
    return actions


def _schema_actions(source_root: Path, target_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    schemas_dir = source_root / "schemas"
    for schema in _sorted_glob(schemas_dir, "*.schema.json"):
        rel = f"schemas/{schema.name}"
        actions.append(
            _action(
                action_id=rel,
                category="file",
                classification=_classify_copy(schema, target_root / rel),
                source=rel,
                destination=rel,
                reason="AIM machine-readable structural contract",
                adapter="core",
                optional=False,
            )
        )
    return actions


def _license_actions(source_root: Path, target_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    license_paths = (
        ("LICENSE", "docs/aim/LICENSE"),
        ("docs/LICENSE-DOCS", "docs/aim/LICENSE-DOCS"),
    )
    for source_rel, destination_rel in license_paths:
        source_path = source_root / source_rel
        if not source_path.is_file():
            raise PlanError(
                f"required distribution license is missing: {source_rel}"
            )
        actions.append(
            _action(
                action_id=destination_rel,
                category="file",
                classification=_classify_copy(
                    source_path, target_root / destination_rel
                ),
                source=source_rel,
                destination=destination_rel,
                reason="AIM distribution license and attribution metadata",
                adapter="core",
                optional=False,
            )
        )
    return actions


def _external_distribution_actions(source_root: Path, home_root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    dest_base = home_root / EXTERNAL_DISTRIBUTION_DEST
    include_roots = (
        source_root / "docs" / "workflow",
        source_root / "schemas",
        source_root / "adapters",
    )
    include_files = [
        source_root / "LICENSE",
        source_root / "docs" / "LICENSE-DOCS",
        source_root / "install" / "aim-install-manifest.yaml",
    ]
    for base in include_roots:
        for item in sorted(base.rglob("*"), key=lambda p: p.as_posix()):
            if not item.is_file():
                continue
            rel = item.relative_to(source_root).as_posix()
            actions.append(
                _action(
                    action_id=f"external:{rel}",
                    category="package",
                    classification=_classify_copy(item, dest_base / rel),
                    source=rel,
                    destination=str(dest_base / rel),
                    reason="External AIM distribution package (home-scope install)",
                    adapter="core",
                    optional=False,
                    scope="home",
                )
            )
    for item in include_files:
        if not item.is_file():
            raise PlanError(f"required external distribution file is missing: {item}")
        rel = item.relative_to(source_root).as_posix()
        actions.append(
            _action(
                action_id=f"external:{rel}",
                category="package",
                classification=_classify_copy(item, dest_base / rel),
                source=rel,
                destination=str(dest_base / rel),
                reason="External AIM distribution package (home-scope install)",
                adapter="core",
                optional=False,
                scope="home",
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
    for source_doc in sorted(
        closure.required_workflow_docs(source_root, "codex", include_optional=True)
    ):
        source_path = source_root / source_doc
        if not source_path.is_file():
            raise PlanError(f"required Codex contract is missing: {source_doc}")
        package_reference = closure.package_reference_for(source_doc)
        dest = dest_base / package_reference
        actions.append(
            _action(
                action_id=f"codex:{package_reference}",
                category="package",
                classification=_classify_copy(source_path, dest),
                source=source_doc,
                destination=str(dest),
                reason="Codex package-local canonical contract",
                adapter="codex",
                optional=False,
                scope="home",
            )
        )
    return actions


def _bootstrap_actions(
    target_root: Path, manifest: Manifest, committed: bool, mode: str
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
                target_root / shared_profile, seed.shared_profile_seed(mode)
            ),
            source=None,
            destination=shared_profile,
            reason="Seed repo-awareness profile (needs calibration, not 'ready')",
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
    footprint: str,
    footprint_explicit: bool,
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
    footprint_profile = manifest.footprint_profile(footprint)
    if not footprint_profile:
        raise PlanError(f"unknown or unconfigured footprint: {footprint}")

    include_optional = bool(mode_profile.get("includeOptionalSurfaces", True))
    enterprise_safe = bool(mode_profile.get("enterpriseSafe", False))
    mode_fragments = [str(f) for f in mode_profile.get("gitignore", [])]
    embedded_docs = bool(footprint_profile.get("embeddedDocs", False))
    external_docs = bool(footprint_profile.get("externalDocs", False))
    footprint_description = str(footprint_profile.get("description", footprint))
    repo_adapters = bool(footprint_profile.get("repoAdapters", False))
    repo_ignore = bool(footprint_profile.get("repoIgnore", False))
    home_adapters = bool(footprint_profile.get("homeAdapters", True))
    shared_profile_rule = footprint_profile.get("sharedProfile", False)
    shared_profile = bool(
        shared_profile_rule is True
        or (shared_profile_rule == "team-default" and mode == "team")
    )

    actions: list[dict[str, Any]] = []
    required_repo_docs: set[str] = set()
    if external_docs:
        actions.extend(_external_distribution_actions(source_root, home_root))
    if embedded_docs:
        actions.extend(_canonical_doc_actions(source_root, target_root))
        actions.extend(_schema_actions(source_root, target_root))
        actions.extend(_license_actions(source_root, target_root))
    elif repo_adapters:
        for adapter in adapters:
            if adapter not in {"claude", "copilot"}:
                continue
            required_repo_docs.update(
                closure.required_workflow_docs(
                    source_root, adapter, include_optional=include_optional
                )
            )
        actions.extend(
            _selected_canonical_doc_actions(
                source_root, target_root, required_repo_docs
            )
        )
    if repo_adapters and "copilot" in adapters:
        actions.extend(_copilot_actions(source_root, target_root, include_optional))
    if repo_adapters and "claude" in adapters:
        actions.extend(_claude_actions(source_root, target_root))
    if home_adapters and "codex" in adapters:
        actions.extend(_codex_actions(source_root, home_root))
    actions.extend(_bootstrap_actions(target_root, manifest, shared_profile, mode))
    fragments = mode_fragments or manifest.gitignore_fragments or manifest.runtime_exclusions
    if repo_ignore:
        actions.extend(_ignore_actions(target_root, manifest, fragments))

    excluded = _root_file_exclusions(manifest)
    _assert_root_files_untouched(actions, excluded)
    repo_actions = [a for a in actions if a.get("scope") != "home"]
    local_actions = [a for a in actions if a.get("scope") == "home"]
    skipped_adapters = [
        adapter
        for adapter in adapters
        if adapter in {"copilot", "claude"} and not repo_adapters
    ]
    approval_notes: list[str] = []
    default_footprint = str(mode_profile.get("defaultFootprint", "local"))
    if footprint_explicit and footprint != default_footprint:
        approval_notes.append(
            f"Explicit footprint '{footprint}' overrides the {mode} default "
            f"'{default_footprint}'."
        )
    if mode == "enterprise" and repo_actions:
        approval_notes.append(
            "Enterprise repository mutation is present only because a broader "
            "repo-writing footprint was explicitly selected."
        )
    local_policy = {
        "personal": [
            "User-level personal hints remain outside the repository",
            "Runtime state is created later; keeping or committing it is the solo user's choice",
        ],
        "team": [
            "Personal hints remain user-level",
            "Runtime state stays local by default unless the team chooses otherwise",
        ],
        "enterprise": [
            "AIM package, runtime state, and repo-awareness memory stay outside the repository by default",
            "Use repo-writing footprints only when the repo owner explicitly wants shared AIM surfaces",
        ],
    }.get(mode, [])

    bootstrap = manifest.repo_awareness_bootstrap
    codex_package_docs = (
        sorted(
            closure.package_reference_for(source_doc)
            for source_doc in closure.required_workflow_docs(
                source_root, "codex", include_optional=True
            )
        )
        if home_adapters and "codex" in adapters
        else []
    )
    plan = {
        "planSchemaVersion": PLAN_SCHEMA_VERSION,
        "manifestVersion": manifest.version,
        "generatedAt": _now_iso(),
        "operation": "dry-run",
        "mode": mode,
        "footprint": footprint,
        "footprintDescription": footprint_description,
        "footprintExplicit": footprint_explicit,
        "defaultFootprint": default_footprint,
        "modeProfile": {
            "includeOptionalSurfaces": include_optional,
            "enterpriseSafe": enterprise_safe,
        },
        "footprintProfile": {
            "embeddedDocs": embedded_docs,
            "externalDocs": external_docs,
            "repoAdapters": repo_adapters,
            "sharedProfile": shared_profile,
            "repoIgnore": repo_ignore,
            "homeAdapters": home_adapters,
        },
        "gitignoreFragments": fragments,
        "adapters": adapters,
        "source": str(source_root),
        "target": str(target_root),
        "validator": validator_result,
        "adapterClosure": {
            "rule": str(manifest.adapter_closure.get("rule", "")),
            "requiredRepoDocs": sorted(required_repo_docs),
            "packageLocalDocs": {"codex": codex_package_docs},
            "fullWorkflowLibrary": embedded_docs,
        },
        "bootstrap": {
            "status": "needs_calibration",
            "storage": (
                "committed-shared-profile"
                if shared_profile
                else "external-repo-awareness"
                if footprint_profile.get("externalRepoAwareness")
                else "local-or-no-profile"
            ),
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
            "enterpriseMemory": str(
                bootstrap.get(
                    "enterpriseMemory",
                    "~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml",
                )
            ),
            "enterpriseMemoryDocs": str(
                bootstrap.get(
                    "enterpriseMemoryDocs",
                    "~/.aim/repo-awareness/<repo-fingerprint>/docs/",
                )
            ),
            "calibrationCommand": str(
                bootstrap.get("calibrationCommand", "/aim calibrate-repo")
            ),
            "note": "Bootstrap never reports 'ready'; run calibration after install.",
            "enterpriseExternal": bool(
                footprint_profile.get("externalRepoAwareness", False)
            ),
        },
        "rootFileExclusions": excluded,
        "actions": actions,
        "scopeSummary": {
            "repoActionCount": len(repo_actions),
            "localActionCount": len(local_actions),
            "repoDestinations": [a["destination"] for a in repo_actions],
            "localDestinations": [a["destination"] for a in local_actions],
            "staysLocal": local_policy,
            "skippedAdapters": skipped_adapters,
            "explicitApproval": approval_notes,
        },
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

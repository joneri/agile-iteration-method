"""Cross-surface product-coherence probes for AIM 2.0."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from aim_installer import planner
from aim_installer.manifest import ManifestError, load_manifest

from .reporting import make_finding


MODE_CONTRACT_FILES = (
    "docs/workflow/operating-modes.md",
    "docs/workflow/install-aim-2.0.md",
    "docs/product/platforms-and-adoption.md",
    "README.md",
)

ADAPTER_CLAIM_FILES = (
    "README.md",
    "docs/product/platforms-and-adoption.md",
    "docs/workflow/adapter-entry-model.md",
    "docs/workflow/adapter-command-contract.md",
)

CANONICAL_COMMANDS = (
    "/aim start",
    "/aim continue",
    "/aim status",
    "/aim validate",
    "/aim help",
    "/aim config",
    "/aim calibrate-repo",
    "/aim remember-repo",
    "/aim forget-repo",
    "/aim upgrade",
    "/aim mode",
    "/aim cost",
    "/aim replan",
)


def _read(repo_root: Path, relative_path: str) -> str:
    path = repo_root / relative_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _contradictory_mode_claims(repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    patterns = (
        (
            "Enterprise",
            re.compile(
                r"enterprise(?: aim)?[^.\n]{0,80}"
                r"(?:defaults? to|by default)[^.\n]{0,80}"
                r"(?:broad repo(?:sitory)? mutation|full footprint|adapter footprint|writes repo files)",
                re.IGNORECASE,
            ),
            "Enterprise is documented as broad or repo-writing by default",
            "Enterprise defaults to a protected local footprint; repo mutation requires an explicit footprint.",
        ),
        (
            "Personal",
            re.compile(
                r"personal(?: aim)?[^.\n]{0,80}"
                r"(?:defaults? to|must remain|is)[^.\n]{0,60}"
                r"(?:local-first|zero[- ]footprint|minimal footprint|non-invasive by default)",
                re.IGNORECASE,
            ),
            "Personal is documented as a constrained local-only mode",
            "Personal is freedom mode; local, profile, adapters, and full are user choices.",
        ),
        (
            "Team",
            re.compile(
                r"team(?: aim)?[^.\n]{0,80}"
                r"(?:defaults? to|by default)[^.\n]{0,60}"
                r"(?:local-only|no shared profile|zero[- ]footprint)",
                re.IGNORECASE,
            ),
            "Team is documented without its intentional shared setup",
            "Team defaults to reviewed shared repo-awareness and selected adapter surfaces.",
        ),
    )
    for relative_path in MODE_CONTRACT_FILES:
        content = _read(repo_root, relative_path)
        for mode, pattern, rule, action in patterns:
            match = pattern.search(content)
            if not match:
                continue
            findings.append(
                make_finding(
                    "contradictory",
                    relative_path,
                    rule,
                    action,
                    tier="Product coherence",
                    category="Contradiction",
                    release_impact="fail",
                    evidence=f"{mode} claim: {match.group(0).strip()}",
                )
            )
    return findings


def _generate_default_plans(
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    plans: dict[str, dict[str, Any]] = {}
    try:
        manifest = load_manifest(repo_root)
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as home:
            for mode in ("personal", "team", "enterprise"):
                footprint = str(
                    manifest.mode_profile(mode).get("defaultFootprint", "")
                )
                plans[mode] = planner.compute_plan(
                    source_root=repo_root,
                    target_root=Path(target),
                    mode=mode,
                    footprint=footprint,
                    footprint_explicit=False,
                    adapters=["copilot", "claude", "codex"],
                    manifest=manifest,
                    validator_result={"resultClass": "healthy", "exitCode": 0},
                    home_root=Path(home),
                )
    except (ManifestError, planner.PlanError, OSError, KeyError) as exc:
        findings.append(
            make_finding(
                "blocked",
                "install/aim-install-manifest.yaml",
                f"representative mode plans could not be generated: {exc}",
                "Repair the manifest and planner before claiming coherent mode behavior.",
                tier="Behavioral",
                category="Error",
                release_impact="fail",
            )
        )
    return plans, findings


def _mode_plan_findings(
    plans: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if set(plans) != {"personal", "team", "enterprise"}:
        return findings

    personal = plans["personal"]
    personal_destinations = set(personal["scopeSummary"]["repoDestinations"])
    if (
        personal["footprint"] != "adapters"
        or "aim.profile.yaml" in personal_destinations
        or not any(
            path.startswith((".github/agents/", ".claude/"))
            for path in personal_destinations
        )
        or any(path.startswith("docs/workflow/") for path in personal_destinations)
    ):
        findings.append(
            make_finding(
                "contradictory",
                "Personal docs ↔ generated installer plan",
                "Personal freedom-mode default is not the documented practical adapter setup",
                "Restore the adapters default without forcing a shared profile or embedded docs.",
                tier="Product coherence",
                category="Contradiction",
                release_impact="fail",
                evidence=(
                    f"footprint={personal['footprint']}, "
                    f"repoActions={personal['scopeSummary']['repoActionCount']}"
                ),
            )
        )

    team = plans["team"]
    team_destinations = set(team["scopeSummary"]["repoDestinations"])
    if (
        team["footprint"] != "adapters"
        or "aim.profile.yaml" not in team_destinations
        or ".gitignore" not in team_destinations
        or any(path.startswith("docs/workflow/") for path in team_destinations)
    ):
        findings.append(
            make_finding(
                "contradictory",
                "Team docs ↔ generated installer plan",
                "Team default does not match the documented reviewed shared setup",
                "Generate the shared profile, ignore policy, and selected adapters without embedded docs.",
                tier="Product coherence",
                category="Contradiction",
                release_impact="fail",
                evidence=(
                    f"footprint={team['footprint']}, "
                    f"repoActions={team['scopeSummary']['repoActionCount']}"
                ),
            )
        )

    enterprise = plans["enterprise"]
    if (
        enterprise["footprint"] != "local"
        or enterprise["scopeSummary"]["repoActionCount"] != 0
    ):
        findings.append(
            make_finding(
                "contradictory",
                "Enterprise docs ↔ generated installer plan",
                "Enterprise is documented as non-invasive but its default plan writes repository files",
                "Restore the local default and require explicit footprint approval for every repo write.",
                tier="Product coherence",
                category="Contradiction",
                release_impact="fail",
                evidence=(
                    f"footprint={enterprise['footprint']}, "
                    f"repoActions={enterprise['scopeSummary']['repoActionCount']}"
                ),
            )
        )
    return findings


def _adapter_claim_findings(repo_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    public_claims = "\n".join(_read(repo_root, path) for path in ADAPTER_CLAIM_FILES)
    claims_native_support = all(
        platform in public_claims for platform in ("Codex", "Claude", "GitHub Copilot")
    )
    if not claims_native_support:
        return findings

    surfaces = {
        "Codex": _read(
            repo_root, "adapters/codex/agile-iteration-method/SKILL.md"
        ),
        "GitHub Copilot": _read(repo_root, ".github/agents/aim.agent.md"),
    }
    for adapter, content in surfaces.items():
        missing = [command for command in CANONICAL_COMMANDS if command not in content]
        if missing:
            findings.append(
                make_finding(
                    "contradictory",
                    f"public native-support claim ↔ {adapter}",
                    f"{adapter} is publicly supported but lacks command intents: {', '.join(missing)}",
                    "Restore command coverage or narrow the public native-support claim.",
                    tier="Product coherence",
                    category="Contradiction",
                    release_impact="fail",
                )
            )

    claude_dir = repo_root / ".claude/commands"
    claude_content = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(claude_dir.glob("*.md"))
    ) if claude_dir.is_dir() else ""
    missing_claude = [
        command for command in CANONICAL_COMMANDS if command not in claude_content
    ]
    if missing_claude:
        findings.append(
            make_finding(
                "contradictory",
                "public native-support claim ↔ Claude",
                "Claude is publicly supported but its command package lacks intents: "
                + ", ".join(missing_claude),
                "Restore native command files or narrow the public native-support claim.",
                tier="Product coherence",
                category="Contradiction",
                release_impact="fail",
            )
        )

    if "/aim upgrade" in public_claims:
        upgrade_surfaces = {
            "canonical contract": _read(
                repo_root, "docs/workflow/adapter-command-contract.md"
            ),
            "Codex": surfaces["Codex"],
            "GitHub Copilot": surfaces["GitHub Copilot"],
            "Claude": _read(repo_root, ".claude/commands/upgrade-aim.md"),
        }
        for surface, content in upgrade_surfaces.items():
            required = ("/aim upgrade", "--dry-run", "--apply", "rollback", ".aim")
            missing = [marker for marker in required if marker not in content]
            if missing:
                findings.append(
                    make_finding(
                        "contradictory",
                        f"public /aim upgrade claim ↔ {surface}",
                        "Upgrade is advertised but the supporting surface is incomplete: "
                        + ", ".join(missing),
                        "Restore the reviewed upgrade contract or remove the unsupported claim.",
                        tier="Product coherence",
                        category="Contradiction",
                        release_impact="fail",
                    )
                )
    validate_surfaces = {
        "canonical contract": _read(
            repo_root, "docs/workflow/adapter-command-contract.md"
        ),
        "Codex": surfaces["Codex"],
        "GitHub Copilot": surfaces["GitHub Copilot"],
        "Claude": _read(repo_root, ".claude/commands/validate-aim.md"),
    }
    for surface, content in validate_surfaces.items():
        normalized = " ".join(content.lower().split())
        missing = [
            marker
            for marker in ("product coherence", "release readiness")
            if marker not in normalized
        ]
        if missing:
            findings.append(
                make_finding(
                    "contradictory",
                    f"/aim validate contract ↔ {surface}",
                    "Validation is advertised without the product-coherence tiers: "
                    + ", ".join(missing),
                    "Align the adapter validation surface with the canonical tiered report.",
                    tier="Product coherence",
                    category="Contradiction",
                    release_impact="fail",
                )
            )

    stale_version_pattern = re.compile(
        r"""aimVersion["']?\s*[:=]\s*["']?1\.""",
        re.IGNORECASE,
    )
    adapter_paths = [
        repo_root / "adapters/codex/agile-iteration-method/SKILL.md",
        repo_root / ".github/agents/aim.agent.md",
        *sorted((repo_root / ".claude").rglob("*.md")),
    ]
    for path in adapter_paths:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        match = stale_version_pattern.search(content)
        if not match:
            continue
        findings.append(
            make_finding(
                "contradictory",
                f"AIM 2.0 public claim ↔ {path.relative_to(repo_root).as_posix()}",
                "AIM 2.0 adapter support contains an AIM 1.x state-version example",
                "Use the current AIM 2.0 state version across every adapter surface.",
                tier="Product coherence",
                category="Contradiction",
                release_impact="fail",
                evidence=match.group(0),
            )
        )
    return findings


def _release_claim_findings(repo_root: Path) -> list[dict[str, Any]]:
    public_front_door = "\n".join(
        _read(repo_root, path)
        for path in ("README.md", "docs/product/README.md", "docs/product/getting-started.md")
    )
    if "AIM 2.0" not in public_front_door:
        return []

    stale_release_pattern = re.compile(
        r"AIM 2\.0 is not released as (?:a )?final runtime(?: yet)?",
        re.IGNORECASE,
    )
    findings: list[dict[str, Any]] = []
    workflow_root = repo_root / "docs/workflow"
    for path in sorted(workflow_root.glob("*.md")):
        content = path.read_text(encoding="utf-8", errors="replace")
        match = stale_release_pattern.search(content)
        if not match:
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        findings.append(
            make_finding(
                "contradictory",
                f"public AIM 2.0 product surface ↔ {relative_path}",
                "public onboarding presents AIM 2.0 while canonical workflow docs say the runtime is not released",
                "Remove the stale release-status claim or narrow the public onboarding surface.",
                tier="Release readiness",
                category="Contradiction",
                release_impact="fail",
                evidence=match.group(0),
            )
        )
    return findings


def evaluate_product_coherence(
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    findings = _contradictory_mode_claims(repo_root)
    plans, plan_findings = _generate_default_plans(repo_root)
    findings.extend(plan_findings)
    findings.extend(_mode_plan_findings(plans))
    findings.extend(_adapter_claim_findings(repo_root))
    findings.extend(_release_claim_findings(repo_root))

    evidence: list[str] = []
    for mode in ("personal", "team", "enterprise"):
        if mode not in plans:
            continue
        plan = plans[mode]
        evidence.append(
            f"{mode}: footprint={plan['footprint']}, "
            f"repoActions={plan['scopeSummary']['repoActionCount']}, "
            f"localActions={plan['scopeSummary']['localActionCount']}"
        )
    evidence.append("adapter command family: Codex, Claude, and Copilot checked")
    evidence.append("upgrade contract: canonical and adapter surfaces checked")
    evidence.append("public claims: native support and upgrade evidence checked")
    evidence.append("release claims: public and canonical status checked")
    return findings, evidence

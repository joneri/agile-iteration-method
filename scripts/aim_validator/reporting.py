"""Typed findings and release-readiness reporting for AIM validation."""

from __future__ import annotations

from typing import Any


RESULT_ORDER = {
    "healthy": 0,
    "recoverable": 1,
    "blocked": 2,
    "contradictory": 3,
}

TIER_NAMES = (
    "Structural",
    "Behavioral",
    "Product coherence",
    "Release readiness",
)


def _infer_tier(artifact: str, rule: str) -> str:
    combined = f"{artifact} {rule}".lower()
    if any(
        marker in combined
        for marker in (
            "contradict",
            "drift",
            "differs from canonical",
            "public product",
            "product document",
            "mode footprint",
            "command coverage",
            "upgrade behavior",
            "native support",
        )
    ):
        return "Product coherence"
    if any(
        marker in combined
        for marker in (
            "planner",
            "install manifest",
            "installer",
            "adapter",
            ".claude/",
            ".github/agents/",
            "codex",
        )
    ):
        return "Behavioral"
    return "Structural"


def _infer_category(result: str) -> str:
    if result == "contradictory":
        return "Contradiction"
    if result == "recoverable":
        return "Warning"
    return "Error"


def make_finding(
    result: str,
    artifact: str,
    rule: str,
    action: str,
    *,
    tier: str | None = None,
    category: str | None = None,
    release_impact: str | None = None,
    evidence: str | None = None,
) -> dict[str, Any]:
    resolved_category = category or _infer_category(result)
    resolved_impact = release_impact
    if resolved_impact is None:
        resolved_impact = "conditional" if result == "recoverable" else "fail"
    return {
        "result": result,
        "artifact": artifact,
        "rule": rule,
        "action": action,
        "tier": tier or _infer_tier(artifact, rule),
        "category": resolved_category,
        "releaseImpact": resolved_impact,
        "evidence": evidence or "",
    }


def summarize_result(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "healthy"
    return max(findings, key=lambda item: RESULT_ORDER[item["result"]])["result"]


def release_readiness(findings: list[dict[str, Any]]) -> str:
    if any(item["releaseImpact"] == "fail" for item in findings):
        return "FAIL"
    if any(item["releaseImpact"] == "conditional" for item in findings):
        return "CONDITIONAL"
    return "PASS"


def tier_statuses(findings: list[dict[str, Any]]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for tier in TIER_NAMES:
        if tier == "Release readiness":
            statuses[tier] = release_readiness(findings)
            continue
        tier_findings = [item for item in findings if item["tier"] == tier]
        if any(item["releaseImpact"] == "fail" for item in tier_findings):
            statuses[tier] = "FAIL"
        elif tier_findings:
            statuses[tier] = "CONDITIONAL"
        else:
            statuses[tier] = "PASS"
    return statuses


def findings_by_category(
    findings: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        category: [item for item in findings if item["category"] == category]
        for category in ("Error", "Warning", "Contradiction")
    }

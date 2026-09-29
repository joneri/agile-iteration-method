"""Propose role skills from explicit requirements; hypotheses stay hypotheses."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .files import read_evidence

ROLES = ("po", "tdo", "dev", "reviewer")
BASE_SKILLS = {role: f"aim-{role}-engineering" for role in ROLES}
BUNDLE_ROOT = Path(__file__).resolve().parents[2]
# These are capability searches, never fabricated installed skill names.
CAPABILITIES = (
    ("web-interface", r"\b(browser|web|react|vue|html|webbläsare|gränssnitt)\b",
     ("po", "tdo", "dev", "reviewer"), "UI composition, accessibility and browser interaction"),
    ("search-performance", r"\b(search|solver|sökning|knäckning|latency|performance|prestanda)\b",
     ("tdo", "dev", "reviewer"), "Algorithm complexity, profiling and bounded resource use"),
    ("security", r"\b(auth|authentication|password|payment|secret|personuppgifter|inloggning|säkerhet)\b",
     ROLES, "Threat modeling and applicable security verification controls"),
    ("domain-oracle", r"\b(enigma|crypto|cryptography|kryptering|simulation|mathematics)\b",
     ("tdo", "dev", "reviewer"), "Independent domain references and known-answer validation"),
)


def role_skill_issues(root: Path, profile: dict) -> list[str]:
    """Check claimed availability, without importing or executing any skill.

    Legacy profiles inherit the bundled skill. Project skills need an actual
    contained instruction file; inferred and unavailable skills cannot be
    silently promoted to verified expertise.
    """
    issues = []
    roles = profile.get("aimProjectRoles", {}).get("roles", {})
    if not isinstance(roles, dict):
        return ["roles must be a mapping"]
    for role in ROLES:
        config = roles.get(role, {})
        if not isinstance(config, dict):
            continue  # The schema reports this structural error.
        bindings = config.get("skills", [{"id": BASE_SKILLS[role], "source": "bundled", "status": "available"}])
        if not isinstance(bindings, list):
            continue
        seen = set()
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            identifier = binding.get("id")
            if not isinstance(identifier, str):
                continue
            if identifier in seen:
                issues.append(f"{role}: duplicate skill {identifier}")
            seen.add(identifier)
            status = binding.get("status")
            if status == "unavailable":
                if not isinstance(binding.get("fallback"), str) or not binding["fallback"].strip():
                    issues.append(f"{role}: unavailable skill {identifier} needs a fallback")
                continue
            if status not in {"available", "verified"}:
                continue
            instruction_root = root
            if binding.get("source") == "bundled":
                if identifier != BASE_SKILLS[role]:
                    issues.append(f"{role}: unknown bundled skill {identifier}")
                    continue
                paths = [f"docs/workflow/role-skill-{role}.md", f"references/role-skill-{role}.md"]
                # Bundled instructions belong to this running AIM package, not
                # to the consuming project's docs directory.
                instruction_root = BUNDLE_ROOT
            else:
                path = binding.get("path")
                if not isinstance(path, str) or not path:
                    issues.append(f"{role}: available project skill {identifier} needs an instruction path")
                    continue
                paths = [path]
            for path in paths:
                try:
                    if read_evidence(instruction_root, path).strip():
                        break
                except (OSError, ValueError):
                    pass
            else:
                issues.append(f"{role}: skill {identifier} instructions are missing, empty or unsafe")
    return issues


def suggest_skills(root: Path, requirements: list[str] | None = None) -> dict:
    """Inspect only named files, or at most eight conventional root PRD files.

    No framework is chosen from prose, no code is executed and no external skill
    is installed. A match is a reviewable capability hypothesis with provenance.
    """
    if requirements is None:
        requirements = sorted({p.name for pattern in ("*prd*.md", "*PRD*.md", "requirements.md")
                               for p in root.glob(pattern)})[:8]
    if len(requirements) > 16:
        raise ValueError("at most 16 explicit requirement files are supported")
    roles = {role: {"skills": [{"id": BASE_SKILLS[role], "source": "bundled",
                               "status": "available"}], "candidates": []} for role in ROLES}
    sources, diagnostics = [], []
    for relative in dict.fromkeys(requirements):
        try:
            payload = read_evidence(root, relative)
            content = payload.decode("utf-8")
            source = {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}
        except (OSError, ValueError, UnicodeError) as exc:
            diagnostics.append({"path": relative, "error": str(exc)})
            continue
        sources.append(source)
        for capability, pattern, applicable, purpose in CAPABILITIES:
            match = re.search(pattern, content, re.IGNORECASE)
            if match is None:
                continue
            for role in applicable:
                roles[role]["candidates"].append({
                    "capability": capability, "purpose": purpose,
                    "status": "inferred", "confidence": "low", "source": relative,
                    "line": content.count("\n", 0, match.start()) + 1,
                    "nextAction": "Match an available skill, inspect its instructions, then confirm relevance.",
                })
    return {"version": 1, "roles": roles, "sources": sources, "diagnostics": diagnostics,
            "verifiedProjectExpertise": False}

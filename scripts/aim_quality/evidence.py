"""Check freshness of attributed knowledge; hashes do not prove semantic truth."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .files import read_evidence


def check_claims(root: Path, document: dict) -> dict:
    """Validate each claim's document and source fingerprints once per call.

    Cache lifetime is one invocation: no stale facts survive a later check.
    Commands in evidence are data and are never executed.
    """
    if not isinstance(document, dict) or document.get("version") != 1:
        raise ValueError("knowledge evidence version must be 1")
    claims = document.get("claims")
    if not isinstance(claims, list) or not claims or len(claims) > 256:
        raise ValueError("claims must contain between 1 and 256 entries")
    cache: dict[str, str | Exception] = {}
    results = []
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("each claim must be an object")
        identifier = claim.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError("claim ids must be nonempty and unique")
        seen.add(identifier)
        problems = []
        sources = claim.get("sources")
        if not isinstance(sources, list) or not sources or len(sources) > 32:
            raise ValueError(f"{identifier}: sources must contain 1 to 32 file references")
        if not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
            raise ValueError(f"{identifier}: claim text is required")
        for reference in [claim.get("document"), *sources]:
            if not isinstance(reference, dict):
                raise ValueError(f"{identifier}: document and sources require path and sha256")
            path, expected = reference.get("path"), reference.get("sha256")
            if not isinstance(path, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError(f"{identifier}: invalid path or SHA-256")
            if path not in cache:
                try:
                    cache[path] = hashlib.sha256(read_evidence(root, path)).hexdigest()
                except (OSError, ValueError) as exc:
                    cache[path] = exc
            actual = cache[path]
            if isinstance(actual, Exception):
                problems.append({"path": path, "reason": "missing or unsafe evidence"})
            elif actual != expected:
                problems.append({"path": path, "reason": "changed since review"})
        results.append({"id": identifier, "freshness": "stale" if problems else "unchanged",
                        "problems": problems})
    return {"version": 1, "claims": results, "filesChecked": len(cache),
            "fresh": all(item["freshness"] == "unchanged" for item in results),
            "semanticTruthVerified": False}

"""Read-only review freshness, coverage and declared-provenance boundary.

API: check_review(root, document, changed_paths, *, require_independent=True,
                  allowed_exceptions=()) -> JSON-serializable report.
Malformed evidence or caller policy raises ValueError. A well-shaped review
that fails a boundary returns eligible=False and diagnostics; no commands run.

Version 1 document (all listed fields required except exception):
  {"version": 1, "sources": [{"path": "src.py", "sha256": "<64 hex>"}],
   "implementers": [{"id": "author", "session": "implementation-session"}],
   "reviewer": {"id": "reviewer", "session": "review-session"},
   "reviewMode": "independent",  # independent | self | unavailable
   "findings": [{"id": "F1", "severity": "material", "status": "resolved",
                 "description": "Boundary validated."}],
   "exception": {"kind": "trivial", "reason": "Explicit scope justification"}}
An empty findings list is valid. Severity is material/advisory; status is
open/resolved. Unavailable mode requires reviewer=null. Implementer IDs and
sessions must each be unique. Paths are canonical relative POSIX paths.

The caller supplies a nonempty changed_paths list, independently of evidence.
Every changed path must have a source fingerprint; extra reviewed sources are
also checked. A deleted source uses {"path": "old.py", "absent": true}, mutually
exclusive with sha256. Absence checks reject symlink/non-directory ancestors
and existing final entries, including dangling links. Directory-relative reads
are required for absence checks; unsupported platforms fail closed. No Git
state, directory discovery, or commands from evidence are consulted.

Independent mode requires reviewer ID AND session distinct from ALL authors.
An inconsistent independent declaration cannot be waived. Self mode requires
either require_independent=False or a declared trivial exception explicitly in
allowed_exceptions. Unavailable mode always requires a declared unavailable
exception explicitly in allowed_exceptions. Exceptions never waive stale files,
missing coverage, or unresolved material findings, and never establish review
independence. An inapplicable/unpermitted exception makes evidence ineligible.

eligible means these bounded checks pass, not that code is correct. Provenance
is supplied data, never authenticated identity or verified session isolation.
Freshness describes the bytes read during this call, not an atomic repository
snapshot; callers must rerun after changes and supply the complete changed set.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .files import fingerprint


def _text(value, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be nonempty text of at most {maximum} characters")
    return value


def _path(value) -> str:
    path = _text(value, "source path", 1024)
    if (path.startswith("/") or "\\" in path or ":" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or any(ord(char) < 32 or ord(char) == 127 for char in path)):
        raise ValueError("source paths must be canonical, relative and contained")
    return path


def _list(value, label: str, minimum: int, maximum: int = 256) -> list:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{label} must contain {minimum} to {maximum} entries")
    return value


def _identity(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} requires id and session")
    result = {key: _text(value.get(key), f"{label} {key}", 256) for key in ("id", "session")}
    if any(text != text.strip() or any(ord(char) < 32 for char in text)
           for text in result.values()):
        raise ValueError(f"{label} identifiers must not contain surrounding whitespace or controls")
    return result


def _absent(root: Path, relative: str) -> bool:
    """Check absence under safe directory descriptors; never open source bytes.

    A missing ancestor establishes absence at inspection time. Like fingerprint
    reads, this is not a lock against later mutations or an atomic tree snapshot.
    """
    if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
        raise ValueError("safe absence inspection is unavailable on this platform")
    descriptor = os.open(root.resolve(), os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = relative.split("/")
        for component in parts[:-1]:
            try:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=descriptor)
            except FileNotFoundError:
                return True
            os.close(descriptor)
            descriptor = child
        try:
            os.stat(parts[-1], dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return True
        return False
    finally:
        os.close(descriptor)


def check_review(root: Path, document: dict, changed_paths: list[str], *,
                 require_independent: bool = True, allowed_exceptions=()) -> dict:
    """Validate bounded evidence, then compare each source using the safe reader."""
    if type(require_independent) is not bool:
        raise ValueError("require_independent must be a boolean")
    if (not isinstance(allowed_exceptions, (list, tuple))
            or any(not isinstance(kind, str) or kind not in ("trivial", "unavailable")
                   for kind in allowed_exceptions)
            or len(set(allowed_exceptions)) != len(allowed_exceptions)):
        raise ValueError("allowed_exceptions must contain distinct trivial/unavailable names")
    changed = [_path(path) for path in _list(changed_paths, "changed_paths", 1)]
    if len(set(changed)) != len(changed):
        raise ValueError("changed_paths must be unique")
    if (not isinstance(document, dict) or type(document.get("version")) is not int
            or document["version"] != 1):
        raise ValueError("review evidence version must be 1")
    sources = {}
    for source in _list(document.get("sources"), "sources", 1):
        if not isinstance(source, dict):
            raise ValueError("each source requires path and sha256")
        path, digest = _path(source.get("path")), source.get("sha256")
        if "absent" in source:
            if source["absent"] is not True or "sha256" in source:
                raise ValueError("absent sources require absent=true and no sha256")
        elif not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("each source requires a lowercase SHA-256 or absent=true")
        if path in sources:
            raise ValueError("source paths must be unique")
        sources[path] = digest
    implementers = [_identity(value, "implementer")
                    for value in _list(document.get("implementers"), "implementers", 1, 32)]
    for field in ("id", "session"):
        if len({value[field] for value in implementers}) != len(implementers):
            raise ValueError(f"implementer {field} values must be unique")
    mode = document.get("reviewMode")
    if not isinstance(mode, str) or mode not in ("independent", "self", "unavailable"):
        raise ValueError("reviewMode must be independent, self or unavailable")
    reviewer = document.get("reviewer")
    if mode == "unavailable":
        if "reviewer" not in document or reviewer is not None:
            raise ValueError("unavailable review requires reviewer=null")
    else:
        reviewer = _identity(reviewer, "reviewer")
    unresolved, finding_ids = [], set()
    for finding in _list(document.get("findings"), "findings", 0):
        if not isinstance(finding, dict):
            raise ValueError("each finding must be an object")
        identifier = _text(finding.get("id"), "finding id", 256)
        if identifier in finding_ids:
            raise ValueError("finding ids must be unique")
        finding_ids.add(identifier)
        _text(finding.get("description"), "finding description")
        if finding.get("severity") not in ("material", "advisory"):
            raise ValueError("finding severity must be material or advisory")
        if finding.get("status") not in ("open", "resolved"):
            raise ValueError("finding status must be open or resolved")
        if finding["severity"] == "material" and finding["status"] == "open":
            unresolved.append(identifier)
    exception = document.get("exception")
    if "exception" in document:
        if not isinstance(exception, dict) or exception.get("kind") not in ("trivial", "unavailable"):
            raise ValueError("exception requires a trivial/unavailable kind and reason")
        _text(exception.get("reason"), "exception reason")

    diagnostics = []
    missing = [path for path in changed if path not in sources]
    diagnostics.extend(f"Changed path is not covered: {path}" for path in missing)
    stale = []
    for path, expected in sources.items():
        try:
            matches = (_absent(root, path) if expected is None
                       else fingerprint(root, path)["sha256"] == expected)
        except (OSError, ValueError):
            stale.append(path)
            diagnostics.append(f"Source is missing or unsafe: {path}")
        else:
            if not matches:
                stale.append(path)
                diagnostics.append(f"Source changed since review: {path}")
    diagnostics.extend(f"Unresolved material finding: {identifier}" for identifier in unresolved)
    exception_permitted = bool(exception and exception["kind"] in allowed_exceptions
                               and (mode, exception["kind"]) in
                               (("self", "trivial"), ("unavailable", "unavailable")))
    if exception and not exception_permitted:
        diagnostics.append("Review exception is not permitted or does not match review mode")
    separate = bool(reviewer and all(reviewer[field] != author[field]
                                    for author in implementers for field in ("id", "session")))
    provenance = {"status": "declared-" + mode, "identityAuthenticated": False,
                  "independenceVerified": False, "implementers": implementers,
                  "reviewer": reviewer}
    if mode == "independent":
        if separate:
            provenance["status"] = "declared-separate"
        else:
            provenance["status"] = "conflicting-declaration"
            diagnostics.append("Independent reviewer must differ from every implementer ID and session")
    elif mode == "self" and require_independent and not exception_permitted:
        diagnostics.append("Self-review requires an explicitly permitted trivial exception")
    elif mode == "unavailable" and not exception_permitted:
        diagnostics.append("Unavailable review requires an explicitly permitted unavailable exception")
    return {"version": 1, "eligible": not diagnostics, "fresh": not stale,
            "coverageComplete": not missing, "missingChangedPaths": missing,
            "stalePaths": stale, "filesChecked": len(sources),
            "unresolvedMaterialFindings": unresolved, "reviewMode": mode,
            "independentReviewDeclared": mode == "independent" and separate,
            "provenance": provenance, "exceptionApplied": exception_permitted,
            "exception": ({"kind": exception["kind"], "reason": exception["reason"]}
                          if exception else None),
            "correctnessVerified": False, "diagnostics": diagnostics}

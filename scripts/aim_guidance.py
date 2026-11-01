"""Check release-specific editorial review of the website and school.

Fingerprints detect changed review inputs. They do not perform an editorial
review, authenticate its author, or prove that public claims are correct.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


REVIEW_PATH = "github-pages/assets/aim-guidance-review.json"
GUIDANCE_PAGES = ("index.html", "school.html")
GUIDANCE_SOURCES = (
    "CHANGELOG.md",
    "adapters/portable/agile-iteration-method/SKILL.md",
    "docs/workflow/user-stories.md",
    "docs/workflow/native-orchestration.md",
    "docs/workflow/skill-command-runtime.md",
    "docs/workflow/adapter-command-contract.md",
    "docs/workflow/version-and-installation.md",
    "docs/workflow/cost-control-mode.md",
    "docs/features/aim-enigma-evaluation.md",
)
GUIDANCE_TOPICS = (
    "installationAndStart",
    "deliveryModes",
    "orchestration",
    "delegatedDecisions",
    "resourceUse",
    "verificationAndAcceptance",
    "modelsAndEvidence",
)


class GuidanceError(ValueError):
    """Public guidance has no complete, current review record."""


class _SchoolEdition(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.version = None
        self.in_note = False
        self.in_date = False
        self.note = ""
        self.date = None
        self.date_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "body":
            self.version = values.get("data-aim-version")
        if tag == "p" and "edition-note" in values.get("class", "").split():
            self.in_note = True
        if self.in_note and tag == "time":
            self.in_date = True
            self.date = values.get("datetime")

    def handle_data(self, text: str) -> None:
        if self.in_note:
            self.note += text
        if self.in_date:
            self.date_text += text

    def handle_endtag(self, tag: str) -> None:
        if tag == "time":
            self.in_date = False
        if tag == "p":
            self.in_note = False


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise GuidanceError(f"duplicate review key: {key}")
        result[key] = value
    return result


def _text(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise GuidanceError(f"{relative}: cannot read guidance input: {exc}") from exc


def _bindings(root: Path, rows: object, expected: tuple[str, ...], *, check_bytes: bool) -> None:
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise GuidanceError(f"{REVIEW_PATH}: review must cover exactly: {', '.join(expected)}")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            raise GuidanceError(f"{REVIEW_PATH}: each review input needs path and sha256")
        path, fingerprint = row["path"], row["sha256"]
        if not isinstance(path, str) or path not in expected or path in seen:
            raise GuidanceError(f"{REVIEW_PATH}: unknown or duplicate review input: {path!r}")
        seen.add(path)
        if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
            raise GuidanceError(f"{REVIEW_PATH}: invalid fingerprint for {path}")
        if check_bytes:
            try:
                actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
            except OSError as exc:
                raise GuidanceError(f"{path}: missing guidance review input") from exc
            if actual != fingerprint:
                raise GuidanceError(
                    f"{path}: guidance review is stale; review affected instructions and claims "
                    "before refreshing its fingerprint"
                )


def validate_guidance(root: Path, *, source: bool = True) -> dict:
    """Validate source review, or page freshness in a source-less Pages artifact.

    Artifact checks retain the declared source bindings but cannot reread files
    that are intentionally absent from the publication tree. The builder checks
    those inputs in the source checkout before copying the review record.
    """
    root = root.resolve()
    try:
        review = json.loads(_text(root, REVIEW_PATH), object_pairs_hook=_unique_object)
    except ValueError as exc:
        raise GuidanceError(f"{REVIEW_PATH}: invalid review JSON: {exc}") from exc
    required = {"guidanceReviewVersion", "productVersion", "reviewedOn", "pages", "sources", "assessments"}
    if not isinstance(review, dict) or set(review) != required:
        raise GuidanceError(f"{REVIEW_PATH}: missing or unsupported review fields")
    if type(review["guidanceReviewVersion"]) is not int or review["guidanceReviewVersion"] != 1:
        raise GuidanceError(f"{REVIEW_PATH}: unsupported guidanceReviewVersion")
    version = _text(root, "VERSION").strip()
    if review["productVersion"] != version:
        raise GuidanceError(f"{REVIEW_PATH}: review website and school for AIM {version}")
    reviewed_on = review["reviewedOn"]
    try:
        if not isinstance(reviewed_on, str) or len(reviewed_on) != 10:
            raise ValueError("use YYYY-MM-DD")
        date.fromisoformat(reviewed_on)
    except ValueError as exc:
        raise GuidanceError(f"{REVIEW_PATH}: reviewedOn must be an actual ISO review date") from exc
    assessments = review["assessments"]
    if not isinstance(assessments, dict) or set(assessments) != set(GUIDANCE_TOPICS):
        raise GuidanceError(f"{REVIEW_PATH}: assess all seven public-guidance topics")
    for topic, assessment in assessments.items():
        if (not isinstance(assessment, dict) or set(assessment) != {"conclusion", "summary"}
                or assessment["conclusion"] not in ("current", "updated")
                or not isinstance(assessment["summary"], str)
                or not assessment["summary"].strip() or len(assessment["summary"]) > 1200):
            raise GuidanceError(f"{REVIEW_PATH}: {topic} needs a current/updated conclusion and review summary")
    _bindings(root, review["pages"], GUIDANCE_PAGES, check_bytes=True)
    _bindings(root, review["sources"], GUIDANCE_SOURCES, check_bytes=source)
    edition = _SchoolEdition()
    edition.feed(_text(root, "school.html"))
    edition.close()
    if edition.version != version or f"For AIM {version} ·" not in " ".join(edition.note.split()):
        raise GuidanceError("school.html: visible edition and data-aim-version must match VERSION")
    reviewed_date = date.fromisoformat(reviewed_on)
    months = ("January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December")
    visible_date = f"{reviewed_date.day} {months[reviewed_date.month - 1]} {reviewed_date.year}"
    if edition.date != reviewed_on or " ".join(edition.date_text.split()) != visible_date:
        raise GuidanceError("school.html: visible review date must match the actual guidance review date")
    return review

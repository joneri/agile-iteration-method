"""Release guidance must be reviewed against actual pages and source contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aim_guidance import (  # noqa: E402
    GUIDANCE_PAGES, GUIDANCE_SOURCES, GUIDANCE_TOPICS, REVIEW_PATH,
    GuidanceError, validate_guidance,
)
from aim_docs import audit  # noqa: E402
from aim_publication import PublicationError, build_artifact, validate_artifact  # noqa: E402


class GuidanceReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "VERSION").write_text("4.8.3\n")
        for path in (*GUIDANCE_PAGES, *GUIDANCE_SOURCES):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Original reviewed input: " + path)
        (self.root / "school.html").write_text(
            '<body data-aim-version="4.8.3"><p class="edition-note">For AIM 4.8.3 · '
            'Guidance checked <time datetime="2026-11-01">1 November 2026</time></p></body>')
        def bindings(paths):
            return [{"path": path, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest()}
                    for path in paths]
        self.review = {
            "guidanceReviewVersion": 1, "productVersion": "4.8.3", "reviewedOn": "2026-11-01",
            "pages": bindings(GUIDANCE_PAGES), "sources": bindings(GUIDANCE_SOURCES),
            "assessments": {topic: {"conclusion": "current", "summary": "Synthetic fixture assessment for " + topic}
                            for topic in GUIDANCE_TOPICS},
        }
        self.path = self.root / REVIEW_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.save()

    def save(self) -> None:
        self.path.write_text(json.dumps(self.review, indent=2))

    def test_current_review_accepts_and_version_only_refresh_rejects(self) -> None:
        self.assertEqual(validate_guidance(self.root)["productVersion"], "4.8.3")
        (self.root / "VERSION").write_text("4.8.4\n")
        with self.assertRaisesRegex(GuidanceError, "review website and school for AIM 4.8.4"):
            validate_guidance(self.root)

    def test_each_page_change_invalidates_review_without_a_version_bump(self) -> None:
        for path in GUIDANCE_PAGES:
            target = self.root / path
            before = target.read_bytes()
            target.write_bytes(before + b" Changed public instructions.")
            with self.subTest(path=path), self.assertRaisesRegex(GuidanceError, "guidance review is stale"):
                validate_guidance(self.root)
            target.write_bytes(before)

    def test_each_source_change_invalidates_review_without_a_version_bump(self) -> None:
        for path in GUIDANCE_SOURCES:
            target = self.root / path
            before = target.read_bytes()
            target.write_bytes(before + b" Changed canonical behavior.")
            with self.subTest(path=path), self.assertRaisesRegex(GuidanceError, "guidance review is stale"):
                validate_guidance(self.root)
            target.write_bytes(before)

    def test_missing_review_is_rejected(self) -> None:
        self.path.unlink()
        with self.assertRaisesRegex(GuidanceError, "cannot read guidance input"):
            validate_guidance(self.root)

    def test_bumping_metadata_and_hashes_cannot_hide_an_old_visible_edition_or_date(self) -> None:
        (self.root / "VERSION").write_text("4.8.4\n")
        self.review.update(productVersion="4.8.4", reviewedOn="2026-11-02")
        page = self.root / "school.html"
        original = page.read_text()
        page.write_text(original.replace('data-aim-version="4.8.3"', 'data-aim-version="4.8.4"'))
        def bind_school():
            next(row for row in self.review["pages"] if row["path"] == "school.html")["sha256"] = (
                hashlib.sha256(page.read_bytes()).hexdigest())
            self.save()
        bind_school()
        with self.assertRaisesRegex(GuidanceError, "visible edition"):
            validate_guidance(self.root)
        page.write_text(page.read_text().replace("For AIM 4.8.3", "For AIM 4.8.4"))
        bind_school()
        with self.assertRaisesRegex(GuidanceError, "visible review date"):
            validate_guidance(self.root)
        page.write_text(page.read_text().replace('datetime="2026-11-01"', 'datetime="2026-11-02"'))
        bind_school()
        with self.assertRaisesRegex(GuidanceError, "visible review date"):
            validate_guidance(self.root)
        page.write_text(page.read_text().replace("1 November 2026", "2 November 2026"))
        bind_school()
        validate_guidance(self.root)

    def test_review_cannot_omit_or_duplicate_pages_sources_or_topics(self) -> None:
        original = json.loads(json.dumps(self.review))
        for key in ("pages", "sources"):
            for kind in ("omit", "duplicate"):
                self.review = json.loads(json.dumps(original))
                if kind == "omit":
                    self.review[key].pop()
                else:
                    self.review[key][-1] = self.review[key][0]
                self.save()
                with self.subTest(key=key, kind=kind), self.assertRaises(GuidanceError):
                    validate_guidance(self.root)
        self.review = original
        self.review["assessments"].pop("delegatedDecisions")
        self.save()
        with self.assertRaisesRegex(GuidanceError, "all seven"):
            validate_guidance(self.root)

    def test_empty_assessment_invalid_date_and_duplicate_json_keys_are_rejected(self) -> None:
        self.review["assessments"]["resourceUse"]["summary"] = " "
        self.save()
        with self.assertRaisesRegex(GuidanceError, "review summary"):
            validate_guidance(self.root)
        self.review["assessments"]["resourceUse"]["summary"] = "Fixture resource assessment"
        self.review["reviewedOn"] = "2026-02-30"
        self.save()
        with self.assertRaisesRegex(GuidanceError, "ISO review date"):
            validate_guidance(self.root)
        self.review["reviewedOn"] = "2026-11-01"
        self.save()
        self.path.write_text(self.path.read_text().replace('"productVersion": "4.8.3"',
            '"productVersion": "4.8.3", "productVersion": "4.8.3"'))
        with self.assertRaisesRegex(GuidanceError, "duplicate review key"):
            validate_guidance(self.root)

    def test_artifact_verifies_page_bytes_without_source_checkout(self) -> None:
        for path in GUIDANCE_SOURCES:
            (self.root / path).unlink()
        validate_guidance(self.root, source=False)
        with self.assertRaisesRegex(GuidanceError, "missing guidance review input"):
            validate_guidance(self.root)
        (self.root / "school.html").write_text("Changed packaged lesson")
        with self.assertRaisesRegex(GuidanceError, "guidance review is stale"):
            validate_guidance(self.root, source=False)


class GuidancePublicationTests(unittest.TestCase):
    def copy_source(self, destination: Path) -> Path:
        copied = destination / "repo"
        shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(
            ".git", ".aim", "output", "site", "release-assets", ".playwright-cli", "__pycache__", "*.pyc"))
        return copied

    def test_current_source_and_documentation_audit_accept_the_review(self) -> None:
        review = validate_guidance(ROOT)
        self.assertEqual(review["productVersion"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(audit(ROOT), [])

    def test_missing_or_wrong_release_review_blocks_audit_and_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copy_source(Path(temporary))
            review_path = copied / REVIEW_PATH
            original = review_path.read_bytes()
            review_path.unlink()
            self.assertTrue(any(REVIEW_PATH in error for error in audit(copied)))
            with self.assertRaisesRegex(PublicationError, "cannot read guidance input"):
                build_artifact(copied, Path(temporary) / "missing-review-site")
            review = json.loads(original)
            review["productVersion"] = "0.0.0"
            review_path.write_text(json.dumps(review))
            self.assertTrue(any("review website and school" in error for error in audit(copied)))
            with self.assertRaisesRegex(PublicationError, "review website and school"):
                build_artifact(copied, Path(temporary) / "wrong-review-site")

    def test_changed_contract_blocks_audit_and_builder_with_current_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copy_source(Path(temporary))
            contract = copied / "docs/workflow/user-stories.md"
            contract.write_text(contract.read_text() + "\nChanged owner decision contract.\n")
            self.assertTrue(any("guidance review is stale" in error for error in audit(copied)))
            with self.assertRaisesRegex(PublicationError, "guidance review is stale"):
                build_artifact(copied, Path(temporary) / "site")

    def test_packaged_review_checks_actual_guidance_without_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            build_artifact(ROOT, output)
            self.assertTrue((output / REVIEW_PATH).is_file())
            self.assertFalse((output / "docs/workflow/user-stories.md").exists())
            validate_artifact(output)
            page = output / "school.html"
            page.write_text(page.read_text().replace("Getting started with AIM", "Changed school introduction"))
            with self.assertRaisesRegex(PublicationError, "guidance review is stale"):
                validate_artifact(output)


if __name__ == "__main__":
    unittest.main()

"""Behavioral boundaries for review evidence; no code correctness certification."""

from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aim_quality.files import fingerprint
from aim_quality.review import check_review


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "source.py").write_text("def answer(): return 42\n")
        self.changed = ["source.py"]
        self.review = {
            "version": 1,
            "sources": [fingerprint(self.root, "source.py")],
            "implementers": [{"id": "author-1", "session": "implementation-1"},
                             {"id": "author-2", "session": "implementation-2"}],
            "reviewer": {"id": "reviewer", "session": "review-session"},
            "reviewMode": "independent", "findings": [],
        }

    def check(self, **kwargs):
        return check_review(self.root, self.review, self.changed, **kwargs)

    def test_separate_declaration_is_fresh_without_authenticating_identity_or_correctness(self):
        report = self.check()
        self.assertTrue(report["eligible"])
        self.assertTrue(report["fresh"])
        self.assertTrue(report["coverageComplete"])
        self.assertTrue(report["independentReviewDeclared"])
        self.assertEqual(report["provenance"], {
            "status": "declared-separate", "identityAuthenticated": False,
            "independenceVerified": False,
            "implementers": self.review["implementers"], "reviewer": self.review["reviewer"],
        })
        self.assertFalse(report["correctnessVerified"])

    def test_changed_deleted_and_restored_source_is_checked_afresh_each_call(self):
        source = self.root / "source.py"
        original = source.read_bytes()
        source.write_text("def answer(): return 0\n")
        report = self.check()
        self.assertFalse(report["eligible"])
        self.assertFalse(report["fresh"])
        self.assertEqual(report["stalePaths"], ["source.py"])
        source.unlink()
        self.assertFalse(self.check()["fresh"])
        source.write_bytes(original)
        self.assertTrue(self.check()["eligible"])

    def test_every_caller_changed_path_must_be_covered(self):
        (self.root / "second.py").write_text("another change")
        self.changed.append("second.py")
        report = self.check()
        self.assertTrue(report["fresh"])
        self.assertFalse(report["eligible"])
        self.assertFalse(report["coverageComplete"])
        self.assertEqual(report["missingChangedPaths"], ["second.py"])
        self.review["sources"].append(fingerprint(self.root, "second.py"))
        self.assertTrue(self.check()["eligible"])

    def test_extra_reviewed_sources_must_also_remain_fresh(self):
        (self.root / "dependency.py").write_text("old")
        self.review["sources"].append(fingerprint(self.root, "dependency.py"))
        (self.root / "dependency.py").write_text("new")
        report = self.check()
        self.assertFalse(report["eligible"])
        self.assertTrue(report["coverageComplete"])
        self.assertEqual(report["filesChecked"], 2)

    def test_reviewer_cannot_share_any_implementer_identity_or_session(self):
        original = copy.deepcopy(self.review["reviewer"])
        for author in self.review["implementers"]:
            for field in ("id", "session"):
                with self.subTest(author=author, field=field):
                    self.review["reviewer"] = dict(original, **{field: author[field]})
                    report = self.check()
                    self.assertFalse(report["eligible"])
                    self.assertFalse(report["independentReviewDeclared"])
                    self.assertEqual(report["provenance"]["status"], "conflicting-declaration")
                    self.assertFalse(self.check(require_independent=False)["eligible"])

    def test_self_review_requires_explicit_policy_and_stays_self_review(self):
        self.review["reviewMode"] = "self"
        self.review["reviewer"] = dict(self.review["implementers"][0])
        self.assertFalse(self.check()["eligible"])
        self.review["exception"] = {"kind": "trivial", "reason": "Only a label changed."}
        self.assertFalse(self.check()["eligible"])
        report = self.check(allowed_exceptions=("trivial",))
        self.assertTrue(report["eligible"])
        self.assertTrue(report["exceptionApplied"])
        self.assertEqual(report["exception"], self.review["exception"])
        self.assertFalse(report["independentReviewDeclared"])
        self.assertEqual(report["provenance"]["status"], "declared-self")
        del self.review["exception"]
        self.assertTrue(self.check(require_independent=False)["eligible"])

    def test_exception_cannot_disguise_conflicting_independent_claim(self):
        self.review["reviewer"] = dict(self.review["implementers"][0])
        self.review["exception"] = {"kind": "trivial", "reason": "Small change."}
        report = self.check(allowed_exceptions=("trivial",))
        self.assertFalse(report["eligible"])
        self.assertFalse(report["exceptionApplied"])

    def test_unavailable_requires_matching_exception_even_when_independence_not_required(self):
        self.review["reviewMode"] = "unavailable"
        self.review["reviewer"] = None
        self.assertFalse(self.check(require_independent=False)["eligible"])
        self.review["exception"] = {"kind": "trivial", "reason": "Small change."}
        self.assertFalse(self.check(allowed_exceptions=("trivial",))["eligible"])
        self.review["exception"] = {"kind": "unavailable", "reason": "No separate session available."}
        self.assertFalse(self.check()["eligible"])
        report = self.check(allowed_exceptions=("unavailable",))
        self.assertTrue(report["eligible"])
        self.assertFalse(report["independentReviewDeclared"])
        self.assertEqual(report["provenance"]["status"], "declared-unavailable")

    def test_material_findings_block_even_explicit_exception(self):
        self.review["reviewMode"] = "self"
        self.review["exception"] = {"kind": "trivial", "reason": "Small change."}
        self.review["findings"] = [
            {"id": "F1", "severity": "material", "status": "open", "description": "Input fails."},
            {"id": "F2", "severity": "advisory", "status": "open", "description": "Naming."},
        ]
        report = self.check(allowed_exceptions=("trivial",))
        self.assertFalse(report["eligible"])
        self.assertEqual(report["unresolvedMaterialFindings"], ["F1"])
        self.review["findings"][0]["status"] = "resolved"
        self.assertTrue(self.check(allowed_exceptions=("trivial",))["eligible"])
        (self.root / "source.py").write_text("changed")
        self.assertFalse(self.check(allowed_exceptions=("trivial",))["eligible"])

    def test_explicit_deletion_covers_changed_path_until_it_reappears(self):
        (self.root / "source.py").unlink()
        self.review["sources"] = [{"path": "source.py", "absent": True}]
        self.assertTrue(self.check()["eligible"])
        (self.root / "source.py").write_text("restored")
        self.assertFalse(self.check()["fresh"])
        (self.root / "source.py").unlink()
        (self.root / "source.py").symlink_to(self.root / "missing")
        self.assertFalse(self.check()["fresh"])

    def test_deletion_missing_directory_is_safe_but_link_or_file_ancestor_is_not(self):
        self.changed = ["old/source.py"]
        self.review["sources"] = [{"path": self.changed[0], "absent": True}]
        self.assertTrue(self.check()["eligible"])
        (self.root / "real").mkdir()
        (self.root / "old").symlink_to(self.root / "real", target_is_directory=True)
        self.assertFalse(self.check()["eligible"])
        (self.root / "old").unlink()
        (self.root / "old").write_text("file parent")
        self.assertFalse(self.check()["eligible"])

    def test_unsupported_absence_check_fails_closed(self):
        self.review["sources"] = [{"path": "source.py", "absent": True}]
        (self.root / "source.py").unlink()
        with patch("os.supports_dir_fd", set()):
            self.assertFalse(self.check()["eligible"])

    def test_missing_repository_cannot_establish_deletion(self):
        self.review["sources"] = [{"path": "source.py", "absent": True}]
        report = check_review(self.root / "missing-root", self.review, self.changed)
        self.assertFalse(report["eligible"])
        self.assertFalse(report["fresh"])

    def test_unsafe_paths_rejected_in_evidence_and_caller_scope(self):
        for path in ("../escape", "/tmp/source.py", "a/../source.py", "./source.py",
                     "a//b", "a/", "C:\\source.py", "a\\b", "a\x00b", ""):
            with self.subTest(path=path):
                review = copy.deepcopy(self.review)
                review["sources"][0]["path"] = path
                with self.assertRaises(ValueError):
                    check_review(self.root, review, self.changed)
                with self.assertRaises(ValueError):
                    check_review(self.root, self.review, [path])

    def test_link_parent_fifo_and_oversized_files_fail_closed(self):
        (self.root / "real").mkdir()
        (self.root / "real/source.py").write_text("source")
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        (self.root / "alias.py").symlink_to(self.root / "source.py")
        os.mkfifo(self.root / "fifo")
        (self.root / "large").write_bytes(b"x" * 1_000_001)
        for path in ("link/source.py", "alias.py", "fifo", "large"):
            with self.subTest(path=path):
                self.review["sources"] = [{"path": path, "sha256": "0" * 64}]
                self.changed = [path]
                report = self.check()
                self.assertFalse(report["eligible"])
                self.assertFalse(report["fresh"])

    def test_malformed_payloads_raise_value_error_before_reading_sources(self):
        cases = [None, [], {}, {"version": True}]
        changes = [
            ("sources", []), ("sources", [None]),
            ("sources", [{"path": "source.py", "sha256": "invalid"}]),
            ("sources", [{"path": "source.py", "absent": False}]),
            ("sources", [{"path": "source.py", "absent": True, "sha256": "0" * 64}]),
            ("sources", self.review["sources"] * 2), ("sources", self.review["sources"] * 257),
            ("implementers", []), ("implementers", [None]),
            ("implementers", [self.review["implementers"][0]] * 2),
            ("implementers", [{"id": "author", "session": "same"}, {"id": "another", "session": "same"}]),
            ("reviewer", {"id": "", "session": "review"}),
            ("reviewer", {"id": " author-1 ", "session": "review"}),
            ("reviewMode", {}), ("findings", None), ("findings", [None]),
            ("findings", [{"id": "F", "severity": "material", "status": "unknown", "description": "x"}]),
            ("findings", [{"id": "F", "severity": "unknown", "status": "open", "description": "x"}]),
            ("exception", None), ("exception", {"kind": "trivial", "reason": ""}),
        ]
        for key, value in changes:
            review = copy.deepcopy(self.review)
            review[key] = value
            cases.append(review)
        for payload in cases:
            with self.subTest(payload=payload), patch("aim_quality.review.fingerprint") as reader:
                with self.assertRaises(ValueError):
                    check_review(self.root, payload, self.changed)
                reader.assert_not_called()

    def test_invalid_caller_policy_cannot_report_success(self):
        for changed in ([], ["source.py"] * 2, "source.py"):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                check_review(self.root, self.review, changed)
        for policy in ("trivial", ["unknown"], ["trivial"] * 2, [{}]):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                self.check(allowed_exceptions=policy)
        with self.assertRaises(ValueError):
            self.check(require_independent="false")

    def test_commands_are_inert_and_inputs_and_product_are_not_mutated(self):
        self.review["findings"] = [{"id": "F1", "severity": "advisory", "status": "open",
                                    "description": "Run touch owned; $(touch owned)."}]
        self.review["command"] = "touch owned"
        original = copy.deepcopy(self.review)
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        with patch("subprocess.run", side_effect=AssertionError("execution forbidden")):
            self.assertTrue(self.check()["eligible"])
        self.assertEqual(original, self.review)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})


if __name__ == "__main__":
    unittest.main()

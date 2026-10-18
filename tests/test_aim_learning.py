"""Cross-project recall, evidence boundaries and atomic shared corrections."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_quality import learning


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.store = self.root / "shared/registry.sqlite3"
        self.a = self.root / "private-project-alpha"
        self.b = self.root / "private-project-beta"
        self.a.mkdir()
        self.b.mkdir()
        self.proof_a = self.evidence(self.a, "raw.txt", "PRIVATE-RAW-CONTENT-ALPHA\nSynthetic test evidence")
        self.proof_b = self.evidence(self.b, "raw.txt", "PRIVATE-RAW-CONTENT-BETA\nSynthetic counterexample")
        self.lesson = {"title": "Bind asynchronous results to their input", "context": "A browser runs background tasks",
                       "problem": "An earlier candidate opens under changed inputs", "action": "Keep immutable input identity with every result",
                       "check": "Start A, get a candidate, change to B and reopen A",
                       "topics": ["async-results"], "terms": ["stale result", "gammalt resultat", "ändrad indata"],
                       "phases": ["planning", "review"], "technologies": ["javascript"]}

    def evidence(self, repo, name, content):
        path = repo / name
        path.write_text(content)
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def share(self, **kwargs):
        return learning.share(self.store, self.a, self.lesson, self.proof_a, **kwargs)

    def review(self, **changes):
        source = self.evidence(self.a, "product.py", "print('synthetic source')")
        record = {"version": 1, "sources": [source],
                  "implementers": [{"id": "author", "session": "author-session"}],
                  "reviewer": {"id": "reviewer", "session": "review-session"},
                  "reviewMode": "independent", "findings": []}
        record.update(changes)
        return self.evidence(self.a, "review.json", json.dumps(record))

    def test_two_projects_find_free_text_synonyms_and_browse_weak_queries(self):
        self.share()
        second = {**self.lesson, "title": "Measure branching cost", "context": "Constraint search",
                  "problem": "Pruning cost changes between valid workloads", "action": "Measure independent witness families",
                  "topics": ["constraint-search"], "terms": ["branching performance"], "technologies": ["python"]}
        learning.share(self.store, self.b, second, self.proof_b)
        result = learning.recall(self.store, "gammalt resultat efter ändrad indata", phase="review")
        self.assertEqual(result["lessons"][0]["title"], self.lesson["title"])
        self.assertEqual(result["lessons"][0]["matchKind"], "text")
        self.assertFalse(result["benefitVerified"])
        prefix = learning.recall(self.store, "asynchron")
        self.assertEqual(prefix["lessons"][0]["title"], self.lesson["title"])
        weak = learning.recall(self.store, "candidate quantum unrelated")
        self.assertEqual(weak["lessons"][0]["matchKind"], "discovery")
        self.assertTrue(weak["topics"])
        unknown = learning.recall(self.store, "unmatchedtopic")
        self.assertTrue(all(item["matchKind"] == "discovery" for item in unknown["lessons"]))
        # A matching technology beyond the lexical candidate window must remain
        # discoverable; context selection belongs before the 64-candidate cap.
        for index in range(65):
            learning.share(self.store, self.a, self.lesson, self.proof_a, lesson_id=f"AAA-{index:03}")
        learning.share(self.store, self.b, second, self.proof_b, lesson_id="ZZZ-PYTHON")
        context = learning.recall(self.store, technologies=["python"])
        self.assertEqual(context["lessons"][0]["title"], second["title"])
        self.assertEqual(context["lessons"][0]["matchKind"], "context")

    def test_exact_repeat_cas_cross_project_correction_withdrawal_and_history(self):
        original = self.share()["record"]
        self.assertFalse(self.share()["changed"])
        self.assertEqual(len(learning.history(self.store, original["id"])["revisions"]), 1)
        correction = {**self.lesson, "action": "Invalidate obsolete candidates on every changed input"}
        with self.assertRaises(ValueError):
            learning.share(self.store, self.b, correction, self.proof_b, lesson_id=original["id"])
        changed = learning.share(self.store, self.b, correction, self.proof_b,
                                 lesson_id=original["id"], expected_revision=1)["record"]
        self.assertEqual(changed["revision"], 2)
        self.assertNotEqual(changed["originSha256"], original["originSha256"])
        with self.assertRaises(ValueError):
            learning.withdraw(self.store, self.a, original["id"], 1, "Outdated guidance", self.proof_a)
        removed = learning.withdraw(self.store, self.a, original["id"], 2, "The narrower counterexample supersedes this advice", self.proof_a)
        self.assertEqual(removed["record"]["state"], "withdrawn")
        self.assertFalse(learning.withdraw(self.store, self.a, original["id"], 2,
                        "The narrower counterexample supersedes this advice", self.proof_a)["changed"])
        self.assertEqual(learning.recall(self.store, "candidate")["lessons"], [])
        self.assertEqual([r["revision"] for r in learning.history(self.store, original["id"])["revisions"]], [3, 2, 1])

    def test_unsafe_stale_or_malformed_proof_never_creates_store(self):
        for reference in ({**self.proof_a, "sha256": "0" * 64}, {**self.proof_a, "path": "../outside"},
                          {**self.proof_a, "path": "/absolute"}, {**self.proof_a, "extra": True}):
            with self.subTest(reference=reference):
                with self.assertRaises((ValueError, OSError)):
                    learning.share(self.store, self.a, self.lesson, reference)
                self.assertFalse(self.store.parent.exists())
        (self.a / "linked.txt").symlink_to(self.a / "raw.txt")
        with self.assertRaises((ValueError, OSError)):
            learning.share(self.store, self.a, self.lesson, {**self.proof_a, "path": "linked.txt"})
        duplicate = self.evidence(self.a, "duplicate.json", '{"version":1,"version":1}')
        with self.assertRaises(ValueError):
            learning.share(self.store, self.a, self.lesson, duplicate)
        self.assertFalse(self.store.parent.exists())

    def test_declared_review_requires_current_sources_separation_and_no_open_findings(self):
        receipt = self.review()
        result = learning.share(self.store, self.a, self.lesson, receipt)
        self.assertEqual(result["record"]["sourceVerification"], "declared-independent-review")
        (self.a / "product.py").write_text("changed after review")
        with self.assertRaisesRegex(ValueError, "Structured review"):
            learning.share(self.store, self.a, self.lesson, receipt, expected_revision=1)
        for changes in ({"reviewer": {"id": "other", "session": "author-session"}},
                        {"findings": [{"id": "F1", "severity": "material", "status": "open", "description": "Broken result identity"}]},
                        {"changedPaths": ["uncovered.py"]}):
            with self.subTest(changes=changes):
                receipt = self.review(**changes)
                with self.assertRaises(ValueError):
                    learning.share(self.store, self.a, self.lesson, receipt, expected_revision=1)
        self.assertEqual(len(learning.history(self.store, result["record"]["id"])["revisions"]), 1)

    def test_readonly_missing_registry_and_no_raw_provenance_or_command_execution(self):
        self.assertFalse(learning.recall(self.store, "any query")["available"])
        self.assertFalse(learning.history(self.store, "unknown")["available"])
        self.assertFalse(self.store.parent.exists())
        self.lesson["action"] += "; $(touch forbidden-marker) is literal evidence text"
        with patch("os.system", side_effect=AssertionError("must not execute")), \
             patch("subprocess.Popen", side_effect=AssertionError("must not execute")):
            record = self.share()["record"]
            learning.recall(self.store, "UNIQUE-QUERY-NOT-LOGGED")
        self.assertEqual(record["sourceVerification"], "fingerprinted-source")
        content = b"".join(p.read_bytes() for p in self.store.parent.iterdir() if p.is_file())
        for private in (str(self.a), self.a.name, "raw.txt", "PRIVATE-RAW-CONTENT-ALPHA", "UNIQUE-QUERY-NOT-LOGGED"):
            self.assertNotIn(private.encode(), content)
        self.assertFalse((self.a / "forbidden-marker").exists())

    def test_obvious_secrets_paths_and_invalid_metadata_rejected_before_mutation(self):
        for text in ("/Users/private-person/project", r"C:\Users\private-person\work", "api_key=super-secret-value",
                     "sk-proj-123456789abcdefghijklmnop", "-----BEGIN PRIVATE KEY-----"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "Generalize"):
                    learning.share(self.store, self.a, {**self.lesson, "context": text}, self.proof_a)
                self.assertFalse(self.store.parent.exists())
        for lesson in ({**self.lesson, "title": "x" * 161}, {**self.lesson, "phases": ["accept"]},
                       {**self.lesson, "rawEvidence": "private"}, {**self.lesson, "terms": ["term"] * 13}):
            with self.assertRaises(ValueError):
                learning.share(self.store, self.a, lesson, self.proof_a)
        with patch.dict(os.environ, {"AIM_LEARNING_REGISTRY": str(self.store)}):
            self.assertEqual(learning.default_registry(), self.store)
        self.assertFalse(self.store.parent.exists())

    def test_concurrent_writers_cannot_overwrite_each_others_revision(self):
        record = self.share()["record"]
        barrier = threading.Barrier(2)
        def writer(number):
            barrier.wait()
            try:
                result = learning.share(self.store, self.a, {**self.lesson, "action": f"Independent correction {number}"},
                                        self.proof_a, lesson_id=record["id"], expected_revision=1)
                return result["record"]["revision"]
            except ValueError:
                return "stale"
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(writer, (1, 2)))
        self.assertCountEqual(results, [2, "stale"])
        self.assertEqual(len(learning.history(self.store, record["id"])["revisions"]), 2)

    def test_query_and_output_bounds_fts_syntax_and_history_limits(self):
        for i in range(4):
            lesson = {key: "🙂" * maximum for key, maximum in learning.TEXT_LIMITS.items()}
            lesson.update(title=f"Bounded lesson {i}", topics=[f"topic-{i}-{n}" for n in range(8)],
                          terms=[str(n) + "🙂" * (80 - len(str(n))) for n in range(12)],
                          technologies=[str(n) + "🙂" * (80 - len(str(n))) for n in range(8)], notApplicable="🙂" * 600)
            learning.share(self.store, self.a, lesson, self.proof_a, lesson_id=f"bounded-{i}")
        result = learning.recall(self.store, '" OR * NEAR( AND ) ; DROP TABLE lessons;')
        self.assertLessEqual(len(result["lessons"]), 3)
        self.assertLessEqual(len(result["topics"]), 5)
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()), learning.MAX_OUTPUT_BYTES)
        with self.assertRaises(ValueError):
            learning.recall(self.store, "x" * (learning.MAX_QUERY + 1))
        with self.assertRaises(ValueError):
            learning.recall(self.store, phase="unknown")
        with self.assertRaises(ValueError):
            learning.recall(self.store, technologies=["x"] * 9)
        self.assertTrue(learning.recall(self.store)["available"])

    def test_weak_lexical_hits_do_not_hide_technology_phase_or_topic(self):
        image = {"title": "Export a batch of images", "context": "A photo editor",
                 "problem": "A batch contains duplicate thumbnails", "action": "Remove duplicate thumbnails",
                 "check": "Export distinct thumbnails", "topics": ["image-export"],
                 "phases": ["implementation"], "technologies": ["javascript"]}
        for index in range(4):
            learning.share(self.store, self.a, image, self.proof_a, lesson_id=f"image-{index}")
        transaction = {"title": "Diagnose database lock contention", "context": "Concurrent database writers",
                       "problem": "Multiple workers wait indefinitely on a transaction", "action": "Measure lock contention and bound transaction duration",
                       "check": "Exercise concurrent writers and verify completion", "topics": ["transaction-contention"],
                       "phases": ["diagnosis"], "technologies": ["python"]}
        learning.share(self.store, self.b, transaction, self.proof_b, lesson_id="transaction")
        result = learning.recall(self.store, "batch freezes under load", phase="diagnosis", technologies=["python"])
        self.assertEqual(result["lessons"][0]["id"], "transaction")
        self.assertEqual(result["lessons"][0]["matchKind"], "context")
        self.assertTrue(all(item["matchKind"] == "discovery" for item in result["lessons"][1:]))
        self.assertEqual(result["topics"][0]["topic"], "transaction-contention")
        self.assertLessEqual(len(result["lessons"]), 3)
        self.assertLessEqual(len(result["topics"]), 5)

    def test_credential_shaped_identifiers_are_rejected_on_write_and_read(self):
        identifier = "sk-proj-SYNTHETIC0123456789abcdefgh"
        with self.assertRaisesRegex(ValueError, "Generalize"):
            self.share(lesson_id=identifier)
        self.assertFalse(self.store.parent.exists())
        record = self.share()["record"]
        record["id"] = identifier
        # Simulate an older record which predates this input boundary. It must
        # not leak through recall even when the SQL identity remains ordinary.
        with sqlite3.connect(self.store) as connection:
            connection.execute("UPDATE lessons SET record=?", (json.dumps(record),))
        with self.assertRaisesRegex(ValueError, "Generalize"):
            learning.recall(self.store, "asynchronous result")
        with self.assertRaisesRegex(ValueError, "Generalize"):
            learning.history(self.store, identifier)

    def test_initialize_empty_and_reject_unrelated_database_without_changing_it(self):
        self.assertTrue(learning.initialize(self.store)["available"])
        self.assertEqual(learning.recall(self.store)["lessons"], [])
        other = self.root / "unrelated.sqlite3"
        with sqlite3.connect(other) as connection:
            connection.execute("CREATE TABLE unrelated(value TEXT)")
        before = other.read_bytes()
        with self.assertRaises(ValueError):
            learning.share(other, self.a, self.lesson, self.proof_a)
        self.assertEqual(other.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

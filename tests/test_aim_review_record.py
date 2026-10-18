"""Native review preparation preserves reviewer statements and bound sources."""
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_aim_stories as fixture
import aim_stories as stories


class ReviewRecordTests(unittest.TestCase):
    artifact = fixture.StoryDeliveryTests.artifact
    mutate = fixture.StoryDeliveryTests.mutate
    plan = fixture.StoryDeliveryTests.plan
    authority = fixture.StoryDeliveryTests.authority
    approve = fixture.StoryDeliveryTests.approve

    def setUp(self):
        fixture.StoryDeliveryTests.setUp(self)
        self.approve()
        self.mutate("review", {"deliveryId": "DI-1", "sourcePaths": ["app.py"]})
        self.review_input = {
            "deliveryId": "DI-1", "reviewMode": "independent", "findings": [],
            "implementer": {"id": "fixture-author", "session": "fixture-implementation"},
            "reviewer": {"id": "fixture-reviewer", "session": "fixture-review"},
            "notes": "Synthetic reviewer observations, not authenticated identities.",
            "observations": ["The independent expected recovery case passes."]}

    def record(self, request=None, expected=None):
        return stories.review_record(self.repo, self.review_input if request is None else request,
                                     self.token if expected is None else expected)

    def cli(self, request=None, *, raw=None, expected=None):
        command = [sys.executable, str(fixture.ROOT / "scripts/aim_stories.py"),
                   "--repo", str(self.repo), "review-record", "--compact"]
        if expected is None:
            expected = self.token
        if expected:
            command += ["--expected-sha256", expected]
        return subprocess.run(command, input=raw if raw is not None else json.dumps(
            self.review_input if request is None else request), text=True, capture_output=True)

    def test_cli_compact_report_is_consumed_by_native_validate(self):
        request = copy.deepcopy(self.review_input)
        request["implementers"] = [request.pop("implementer"),
                                    {"id": "fixture-author-2", "session": "fixture-implementation-2"}]
        output = self.cli(request)
        self.assertEqual(output.returncode, 0, output.stderr)
        record = json.loads(output.stdout)
        self.assertEqual(record["version"], 1)
        self.assertNotIn("document", record)
        self.assertEqual(record["sources"], self.document["deliveries"][0]["productBindings"])
        self.assertEqual(record["scopeSha256"], self.document["deliveries"][0]["scopeSha256"])
        for field in ("findings", "reviewer", "implementers", "observations", "notes"):
            self.assertEqual(record[field], request[field])
        reference = self.artifact("review.json", output.stdout)
        result = stories.execute(self.repo, "validate", {"deliveryId": "DI-1", "evidence": [reference]}, self.token)
        self.assertEqual(result["document"]["deliveries"][0]["status"], "validation")

    def test_record_is_read_only_and_expands_single_implementer(self):
        before = {p.relative_to(self.repo): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.repo.rglob("*") if p.is_file()}
        record = self.record()
        after = {p.relative_to(self.repo): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(record["implementers"], [self.review_input["implementer"]])
        self.assertEqual(record["findings"], [])
        self.assertNotIn("eligible", record)
        self.assertNotIn("passed", record)

    def test_stale_receipt_source_or_wrong_phase_blocks_output(self):
        for expected in ("0" * 64, ""):
            output = self.cli(expected=expected)
            self.assertNotEqual(output.returncode, 0)
            self.assertEqual(output.stdout, "")
        source = self.repo / "app.py"
        original = source.read_bytes()
        for contents in (b"changed product\n", None):
            if contents is None:
                source.unlink()
            else:
                source.write_bytes(contents)
            with self.assertRaisesRegex(stories.StoryError, "Source"):
                self.record()
        source.write_bytes(original)
        result = stories.execute(self.repo, "rework", {"deliveryId": "DI-1", "reason": "Fixture correction"}, self.token)
        with self.assertRaisesRegex(stories.StoryError, "in review"):
            self.record(expected=result["storeSha256"])

    def test_format_and_identity_conflicts_are_rejected_before_stdout(self):
        changes = [
            {"implementers": self.review_input["implementer"]},
            {"reviewer": self.review_input["implementer"]},
            {"reviewer": {"id": "other", "session": "fixture-implementation"}},
            {"reviewMode": "self"},
            {"observations": ["extra"] * 33},
            {"notes": "x" * 4097},
            {"sources": [{"path": "/absolute/method/path", "sha256": "0" * 64}]},
            {"findings": [{"id": "F1", "severity": "critical", "status": "open", "description": "Bad schema"}]},
        ]
        for change in changes:
            with self.subTest(change=change):
                request = {**self.review_input, **change}
                if "implementers" in change:
                    request.pop("implementer")
                output = self.cli(request)
                self.assertNotEqual(output.returncode, 0)
                self.assertEqual(output.stdout, "")

    def test_open_material_finding_is_preserved_and_still_blocks_validate(self):
        finding = {"id": "F1", "severity": "material", "status": "open", "description": "Recovery loses an order."}
        record = self.record({**self.review_input, "findings": [finding]})
        self.assertEqual(record["findings"], [finding])
        reference = self.artifact("open-review.json", json.dumps(record))
        before = (self.repo / stories.FILE).read_bytes()
        with self.assertRaisesRegex(stories.StoryError, "Unresolved material finding: F1"):
            stories.execute(self.repo, "validate", {"deliveryId": "DI-1", "evidence": [reference]}, self.token)
        self.assertEqual((self.repo / stories.FILE).read_bytes(), before)

    def test_single_source_read_and_concurrent_change_detection(self):
        original = stories.read_evidence
        reads = []
        def read(repo, path, maximum):
            reads.append(path)
            return original(repo, path, maximum)
        with patch.object(stories, "read_evidence", side_effect=read):
            self.record()
        self.assertEqual(reads.count("app.py"), 1)
        self.assertEqual(reads.count(stories.FILE), 1)
        check = stories.check_review
        def change_after_check(*args, **kwargs):
            result = check(*args, **kwargs)
            (self.repo / "app.py").write_text("changed after source check")
            return result
        with patch.object(stories, "check_review", side_effect=change_after_check):
            with self.assertRaisesRegex(stories.StoryError, "changed during verification"):
                self.record()

    def test_findings_and_review_mode_are_never_invented(self):
        for missing in ("findings", "reviewer", "reviewMode", "implementer"):
            request = copy.deepcopy(self.review_input)
            request.pop(missing)
            with self.subTest(missing=missing):
                with self.assertRaises(stories.StoryError):
                    self.record(request)
        raw = json.dumps(self.review_input)[:-1] + ', "findings": []}'
        output = self.cli(raw=raw)
        self.assertNotEqual(output.returncode, 0)
        self.assertEqual(output.stdout, "")
        self.assertIn("duplicate JSON keys", output.stderr)

    def test_complete_source_set_above_64_reaches_native_validation(self):
        self.mutate('rework', {'deliveryId':'DI-1', 'reason':'Include the complete source set.'})
        paths = ['app.py']
        for number in range(64):
            name = f'part-{number}.py'
            (self.repo/name).write_text(f'value = {number}\n')
            paths.append(name)
        before = (self.repo/stories.FILE).read_bytes()
        with self.assertRaisesRegex(stories.StoryError, '1–256 source paths'):
            stories.execute(self.repo, 'review', {'deliveryId':'DI-1',
                'sourcePaths':paths + [f'extra-{n}' for n in range(192)]}, self.token)
        self.assertEqual((self.repo/stories.FILE).read_bytes(), before)
        self.mutate('review', {'deliveryId':'DI-1', 'sourcePaths':paths})
        record = self.record()
        self.assertEqual({s['path'] for s in record['sources']}, set(paths))
        ref = self.artifact('complete-review.json', json.dumps(record))
        result = stories.execute(self.repo, 'validate', {'deliveryId':'DI-1',
            'evidence':[ref]}, self.token)
        self.assertEqual(len(result['document']['deliveries'][0]['productBindings']), 65)


if __name__ == "__main__":
    unittest.main()

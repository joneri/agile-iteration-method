"""Independent numeric and adversarial checks for delivery quality goals."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_quality.goals import assess, validate_goals
from aim_validator.schema_subset import unsupported_keywords, validate


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


class QualityGoalTests(unittest.TestCase):
    def test_raw_observation_schema_enforces_property_count_boundaries(self):
        schema = json.loads((ROOT / "schemas/aim-product-backlog.schema.json").read_text())
        definition = {"$ref": "#/$defs/qualityCheck"}
        check = {"id": "QC-OBSERVATIONS", "criteria": ["US-EXAMPLE/AC-1"], "kind": "behavior", "stage": "core",
                 "workload": "single result", "environment": "isolated fixture", "method": "read raw result",
                 "expected": {}, "goalIds": [], "observation": {}}
        # Validate through the published definition, including its local references.
        envelope = {"$defs": schema["$defs"], **definition}
        self.assertTrue(any("at least 1 properties" in issue.message for issue in validate(check, envelope)))
        for count, accepted in ((1, True), (32, True), (33, False)):
            check["observation"] = {str(i): {"pointer": "/result"} for i in range(count)}
            self.assertEqual(not validate(check, envelope), accepted)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        (self.repo / ".aim").mkdir()
        (self.repo / "product.py").write_text("original product\n")
        self.bindings = [self.ref("product.py")]
        self.goal = {"id": "KPI-LATENCY", "outcome": "Complete search promptly",
                     "workload": "1000 items, complete correct results", "environment": "reference host",
                     "method": "benchmark search", "unit": "s", "owner": "Dev",
                     "action": "Profile and correct within scope", "source": "Engineering target in plan",
                     "threshold": 0.5, "operator": "<=", "aggregation": "median", "minSamples": 3}
        self.measurement = {"goalId": "KPI-LATENCY", **{key: self.goal[key] for key in
                           ("workload", "environment", "method", "unit")},
                           "samples": [0.4, 0.5, 0.6], "productBindingsSha256": digest(self.bindings)}

    def ref(self, path):
        return {"path": path, "sha256": hashlib.sha256((self.repo / path).read_bytes()).hexdigest()}

    def evidence(self, records=None, name="measurement.json"):
        path = ".aim/" + name
        (self.repo / path).write_text(json.dumps({"qualityMeasurementVersion": "1.0",
                                               "measurements": records or [self.measurement]}))
        return self.ref(path)

    def result(self, records=None):
        return assess(self.repo, [self.goal], [self.evidence(records)], self.bindings)[0]

    def test_legacy_empty_goals_and_unmeasured_goals(self):
        self.assertEqual(assess(self.repo, [], [], []), [])
        self.assertEqual(assess(self.repo, [self.goal], [], [])[0]["state"], "unmeasured")

    def test_median_boundary_and_failures_use_raw_samples(self):
        self.assertEqual(self.result()["state"], "passed")
        self.measurement["samples"] = [0.49, 14, 14]
        result = self.result()
        self.assertEqual((result["state"], result["value"], result["sampleCount"]), ("failed", 14, 3))
        self.measurement["samples"] = [0.2, 0.4, 0.6, 100]
        self.assertEqual(self.result()["value"], 0.5)

    def test_min_max_and_greater_than_or_equal(self):
        for aggregate, operator, expected in (("min", "<=", "passed"), ("max", "<=", "failed"),
                                               ("min", ">=", "failed"), ("max", ">=", "passed")):
            with self.subTest(aggregation=aggregate, operator=operator):
                self.goal.update(aggregation=aggregate, operator=operator)
                self.assertEqual(self.result()["state"], expected)

    def test_large_finite_even_median_does_not_overflow(self):
        self.goal["threshold"] = 1e308
        self.measurement["samples"] = [1e308] * 4
        self.assertEqual(self.result()["state"], "passed")

    def test_even_integer_median_compares_exactly_above_float_precision(self):
        boundary = 2 ** 53
        self.measurement["samples"] = [boundary, boundary, boundary + 1, boundary + 1]
        for operator, threshold, state in (("<=", boundary, "failed"),
                                            (">=", boundary + 1, "failed"),
                                            (">=", boundary, "passed"),
                                            ("<=", boundary + 1, "passed")):
            with self.subTest(operator=operator, threshold=threshold):
                self.goal.update(operator=operator, threshold=threshold)
                result = self.result()
                self.assertEqual(result["state"], state)
                self.assertIn("18014398509481985/2", result["detail"])
                json.dumps(result, allow_nan=False)

    def test_trusted_reader_can_drop_product_payload_and_preserve_freshness(self):
        reference = self.evidence()
        payload = (self.repo / reference["path"]).read_bytes()
        calls = []

        def reader(repo, ref):
            self.assertEqual(repo, self.repo)
            calls.append(ref["path"])
            return (payload, True) if ref == reference else (None, True)

        with patch("aim_quality.goals.read_evidence", side_effect=AssertionError("unexpected duplicate read")):
            result = assess(self.repo, [self.goal], [reference], self.bindings, read_reference=reader)
        self.assertEqual(result[0]["state"], "passed")
        self.assertEqual(calls, [reference["path"], "product.py"])

        def stale_source(repo, ref):
            return (payload, True) if ref == reference else (None, False)

        self.assertEqual(assess(self.repo, [self.goal], [reference], self.bindings,
                                read_reference=stale_source)[0]["state"], "stale")
        with self.assertRaisesRegex(ValueError, "changed"):
            assess(self.repo, [self.goal], [reference], self.bindings,
                   read_reference=lambda repo, ref: (payload, False))

    def test_fewer_samples_and_context_mismatch_never_pass(self):
        self.measurement["samples"] = [0.1, 0.1]
        self.assertEqual(self.result()["state"], "unmeasured")
        self.measurement["samples"] = [0.1] * 3
        for field in ("workload", "environment", "method", "unit"):
            original = self.measurement[field]
            self.measurement[field] = "different"
            self.assertEqual(self.result()["state"], "mismatch")
            self.measurement[field] = original

    def test_stale_binding_digest_and_changed_product_never_pass(self):
        self.measurement["productBindingsSha256"] = "0" * 64
        self.assertEqual(self.result()["state"], "stale")
        self.measurement["productBindingsSha256"] = digest(self.bindings)
        (self.repo / "product.py").write_text("changed product\n")
        self.assertEqual(self.result()["state"], "stale")
        self.bindings = [self.ref("product.py")]
        self.assertEqual(self.result()["state"], "stale")

    def test_missing_product_binding_never_passes(self):
        self.bindings = []
        self.measurement["productBindingsSha256"] = digest([])
        self.assertEqual(self.result()["state"], "stale")

    def test_consolidated_measurements_are_read_once(self):
        second = copy.deepcopy(self.goal)
        second["id"] = "KPI-MEMORY"
        second["unit"] = "MB"
        measurement = {**self.measurement, "goalId": "KPI-MEMORY", "unit": "MB"}
        reference = self.evidence([self.measurement, measurement])
        from aim_quality.files import read_evidence
        with patch("aim_quality.goals.read_evidence", wraps=read_evidence) as reader:
            result = assess(self.repo, [self.goal, second], [reference], self.bindings)
        self.assertEqual([item["state"] for item in result], ["passed", "passed"])
        self.assertEqual(reader.call_count, 2)  # One result file plus one source file.

    def test_nonfinite_boolean_and_non_numeric_goals_rejected(self):
        for value in (True, False, float("nan"), float("inf"), -float("inf"), "0.5", None, 10 ** 1000):
            with self.subTest(value=str(value)[:25]):
                goal = {**self.goal, "threshold": value}
                with self.assertRaises(ValueError):
                    validate_goals([goal])

    def test_nonfinite_boolean_and_non_numeric_samples_rejected(self):
        for value in (True, float("nan"), float("inf"), "0.1", None):
            with self.subTest(value=value):
                self.measurement["samples"] = [0.1, 0.1, value]
                with self.assertRaises(ValueError):
                    self.result()

    def test_goal_shape_bounds_and_duplicates(self):
        variants = [{**self.goal, "minSamples": item} for item in (True, 2, 1001, 3.0)]
        variants += [{**self.goal, field: ""} for field in ("outcome", "source", "action", "method")]
        variants += [{**self.goal, "id": "kpi-invalid"}, {**self.goal, "operator": "=="},
                     {**self.goal, "aggregation": "average"}, {**self.goal, "passed": True}]
        for goal in variants:
            with self.subTest(goal=goal):
                with self.assertRaises(ValueError):
                    validate_goals([goal])
        for values in (None, {}, [self.goal] * 33, [self.goal, self.goal]):
            with self.assertRaises(ValueError):
                validate_goals(values)

    def test_measurement_cannot_assert_pass_or_unknown_fields(self):
        self.measurement["passed"] = True
        with self.assertRaisesRegex(ValueError, "exactly"):
            self.result()

    def test_duplicate_or_unknown_goal_records_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate measurement"):
            self.result([self.measurement, self.measurement])
        self.measurement["goalId"] = "KPI-OTHER"
        with self.assertRaisesRegex(ValueError, "unknown goal"):
            self.result()

    def test_malformed_duplicate_keys_and_deep_json_rejected(self):
        path = self.repo / ".aim/measurement.json"
        for content in (b"broken", b"\xff", b'{"measurements":[],"measurements":[]}', b"[" * 1500 + b"]" * 1500):
            path.write_bytes(content)
            with self.assertRaises(ValueError):
                assess(self.repo, [self.goal], [self.ref(".aim/measurement.json")], self.bindings)

    def test_missing_changed_oversized_or_nonregular_measurement_rejected(self):
        reference = self.evidence()
        path = self.repo / reference["path"]
        path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            assess(self.repo, [self.goal], [reference], self.bindings)
        path.unlink()
        with self.assertRaises(ValueError):
            assess(self.repo, [self.goal], [reference], self.bindings)
        path.write_bytes(b" " * 1_000_001)
        reference = self.ref(reference["path"])
        with self.assertRaisesRegex(ValueError, "size limit"):
            assess(self.repo, [self.goal], [reference], self.bindings)
        path.unlink()
        path.mkdir()
        with self.assertRaises(ValueError):
            assess(self.repo, [self.goal], [reference], self.bindings)

    def test_unsafe_paths_and_symlinks_rejected(self):
        reference = self.evidence()
        for path in ("../outside.json", ".aim/../outside.json", ".aim//measurement.json",
                     ".aim/./measurement.json", "/tmp/measurement.json", "outside.json",
                     ".aim/product-backlog.json", ".aim/\\bad.json", ".aim/\x00.json"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    assess(self.repo, [self.goal], [{**reference, "path": path}], self.bindings)
        (self.repo / ".aim/link.json").symlink_to(self.repo / reference["path"])
        with self.assertRaises(ValueError):
            assess(self.repo, [self.goal], [{**reference, "path": ".aim/link.json"}], self.bindings)
        (self.repo / ".aim/linkdir").symlink_to(self.repo / ".aim", target_is_directory=True)
        with self.assertRaises(ValueError):
            assess(self.repo, [self.goal], [{**reference, "path": ".aim/linkdir/measurement.json"}], self.bindings)

    def test_hardlink_to_backlog_rejected(self):
        reference = self.evidence()
        os.link(self.repo / reference["path"], self.repo / ".aim/product-backlog.json")
        with self.assertRaisesRegex(ValueError, "file identity"):
            assess(self.repo, [self.goal], [reference], self.bindings)

    def test_reference_and_sample_bounds_rejected(self):
        reference = self.evidence()
        for refs in ([reference] * 33, [reference, reference], None):
            with self.assertRaises(ValueError):
                assess(self.repo, [self.goal], refs, self.bindings)
        for samples in ([], [0.1] * 1001):
            self.measurement["samples"] = samples
            with self.assertRaises(ValueError):
                self.result()
        with self.assertRaises(ValueError):
            self.result([self.measurement] * 33)

    def test_goal_schema_uses_supported_keywords(self):
        schema = json.loads((ROOT / "schemas/aim-product-backlog.schema.json").read_text())
        self.assertEqual(unsupported_keywords(schema), [])
        self.assertEqual(validate(self.goal, schema["$defs"]["qualityGoal"]), [])
        self.assertTrue(validate({**self.goal, "threshold": True}, schema["$defs"]["qualityGoal"]))


if __name__ == "__main__":
    unittest.main()

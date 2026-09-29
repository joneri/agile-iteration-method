"""Actual interval arithmetic and public CLI behavior, not wording checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_quality.timing import summarize_timing


class TimingTests(unittest.TestCase):
    def record(self):
        return {"version": 1, "intervals": [
            {"id": "calibrate", "activity": "calibration", "start": "2026-09-29T10:00:00Z", "end": "2026-09-29T10:01:00Z"},
            {"id": "build", "activity": "implementation", "start": "2026-09-29T12:01:30+02:00", "end": "2026-09-29T12:03:00+02:00"},
            {"id": "test", "activity": "verification", "start": "2026-09-29T10:03:00Z", "end": "2026-09-29T10:03:20.5Z"},
        ]}

    def test_separates_improvement_work_and_missing_time_across_timezones(self):
        record = self.record()
        original = copy.deepcopy(record)
        report = summarize_timing(record)
        self.assertEqual(report["secondsByCategory"]["repositoryImprovement"], 60)
        self.assertEqual(report["secondsByCategory"]["implementation"], 90)
        self.assertEqual(report["secondsByCategory"]["verification"], 20.5)
        self.assertEqual(report["recordedSeconds"], 170.5)
        self.assertEqual(report["elapsedSeconds"], 200.5)
        self.assertEqual(report["unattributedSeconds"], 30)
        self.assertFalse(report["activityIndependentlyVerified"])
        self.assertEqual(record, original)

    def test_unsorted_intervals_do_not_change_accounting(self):
        original = self.record()
        reordered = copy.deepcopy(original)
        reordered["intervals"].reverse()
        self.assertEqual(summarize_timing(original), summarize_timing(reordered))

    def test_setup_through_public_cli_stays_separate_from_improvement(self):
        record = {"version": 1, "intervals": [
            {"id": "startup", "activity": "setup", "start": "2026-09-29T10:00:00Z", "end": "2026-09-29T10:00:15Z"},
            {"id": "calibrate", "activity": "calibration", "start": "2026-09-29T10:00:20Z", "end": "2026-09-29T10:00:40Z"},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = json.dumps(record)
            path = root / "timing.json"
            path.write_text(payload)
            for entry in (ROOT / "scripts/aim_engineering.py",
                          ROOT / "skills/agile-iteration-method/scripts/aim_engineering.py"):
                with self.subTest(entry=entry):
                    run = subprocess.run([sys.executable, "-S", str(entry), "--repo", str(root),
                                          "timing", "timing.json"], cwd=root, capture_output=True,
                                         text=True, timeout=10)
                    self.assertEqual(run.returncode, 0, run.stderr or run.stdout)
                    report = json.loads(run.stdout)
                    self.assertEqual(report["secondsByActivity"]["setup"], 15)
                    self.assertEqual(report["secondsByCategory"]["setup"], 15)
                    self.assertEqual(report["secondsByCategory"]["repositoryImprovement"], 20)
                    self.assertEqual(report["recordedSeconds"], 35)
                    self.assertEqual(report["elapsedSeconds"], 40)
                    self.assertEqual(report["unattributedSeconds"], 5)
                    self.assertFalse(report["activityIndependentlyVerified"])
                    self.assertEqual(path.read_text(), payload)
                    self.assertEqual(list(root.iterdir()), [path])

    def test_overlap_is_not_counted_twice_even_with_different_zones(self):
        record = self.record()
        record["intervals"][1]["start"] = "2026-09-29T12:00:30+02:00"
        with self.assertRaisesRegex(ValueError, "overlap"):
            summarize_timing(record)

    def test_bad_versions_shapes_ids_and_activities_rejected(self):
        for value in (None, [], {"version": True}, {"version": 1.0}, {"version": 2}, {"version": 1, "intervals": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize_timing(value)
        for key, value in (("id", []), ("id", ""), ("activity", []), ("activity", "optimized")):
            record = self.record(); record["intervals"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                summarize_timing(record)
        record = self.record(); record["intervals"].append(copy.deepcopy(record["intervals"][0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize_timing(record)
        with self.assertRaisesRegex(ValueError, "4096"):
            summarize_timing({"version": 1, "intervals": [None] * 4097})

    def test_invalid_calendar_naive_zone_and_reverse_time_rejected(self):
        for value in (None, "2026-02-30T10:00:00Z", "2026-09-29T10:00:00", "2026-09-29T10:00:00-00:00", "2026-09-29T10:00:00+24:00", "2026-09-29T10:00:00+00:60", "2026-09-29T10:00:00Z\n", "2026-09-29T09:59:59Z"):
            record = self.record(); record["intervals"][0]["end"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize_timing(record)

    def test_microseconds_waiting_and_adjacent_boundaries(self):
        record = {"version": 1, "intervals": [
            {"id": "wait", "activity": "waiting", "start": "2026-09-29T10:00:00.123456Z", "end": "2026-09-29T10:00:01.123456Z"},
            {"id": "learn", "activity": "knowledge-maintenance", "start": "2026-09-29T10:00:01.123456Z", "end": "2026-09-29T10:00:02.123457Z"},
        ]}
        report = summarize_timing(record)
        self.assertEqual(report["secondsByCategory"]["waiting"], 1)
        self.assertEqual(report["secondsByCategory"]["repositoryImprovement"], 1.000001)
        self.assertEqual(report["unattributedSeconds"], 0)

    def test_packaged_cli_outside_repo_is_read_only_and_rejects_unsafe_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = json.dumps(self.record())
            (root / "timing.json").write_text(payload)
            command = [sys.executable, "-S", str(ROOT / "skills/agile-iteration-method/scripts/aim_engineering.py"), "--repo", str(root), "timing"]
            run = subprocess.run(command + ["timing.json"], cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["unattributedSeconds"], 30)
            self.assertEqual((root / "timing.json").read_text(), payload)
            self.assertEqual(len(list(root.iterdir())), 1)
            run = subprocess.run(command + ["../outside.json"], cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2)


if __name__ == "__main__":
    unittest.main()

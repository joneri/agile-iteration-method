"""AIM UI first-class lifecycle tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import aim_ui_control as control  # noqa: E402
from aim_ui import build_board  # noqa: E402


class AimUiControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "new-repo"
        self.repo.mkdir()
        self.previous_state_root = os.environ.get(control.STATE_ENV)
        os.environ[control.STATE_ENV] = str(self.root / "instances")
        self.addCleanup(self._restore_environment)
        self.addCleanup(self._stop_instance)

    def _restore_environment(self) -> None:
        if self.previous_state_root is None:
            os.environ.pop(control.STATE_ENV, None)
        else:
            os.environ[control.STATE_ENV] = self.previous_state_root

    def _stop_instance(self) -> None:
        try:
            control.stop(self.repo.resolve())
        except OSError:
            pass

    def test_empty_repository_projects_truthful_onboarding_without_writes(self) -> None:
        board = build_board(self.repo)
        self.assertEqual(board["source"]["kind"], "uninitialized")
        self.assertEqual(board["epics"], [])
        self.assertEqual(board["onboarding"]["nextAction"], "/aim calibrate-repo")
        self.assertEqual(board["recovery"]["kind"], "empty_repository")
        self.assertEqual(
            board["recovery"]["recommendedAction"]["intent"],
            "/aim calibrate-repo",
        )
        self.assertEqual(
            board["recovery"]["alternatives"][0]["intent"], "/aim to-backlog"
        )
        self.assertFalse(board["roadmap"]["configured"])
        self.assertFalse((self.repo / ".aim").exists())

    def test_calibrated_repository_routes_to_discuss_before_roadmap_promotion(self) -> None:
        (self.repo / "aim.profile.yaml").write_text(
            "aimRepoProfile:\n  calibration:\n    status: ready\n",
            encoding="utf-8",
        )
        board = build_board(self.repo)
        self.assertTrue(board["source"]["calibrated"])
        self.assertTrue(board["onboarding"]["nextAction"].startswith("/aim discuss"))
        self.assertTrue(
            board["recovery"]["recommendedAction"]["intent"].startswith(
                "/aim discuss"
            )
        )
        self.assertEqual(
            board["recovery"]["alternatives"][0]["intent"], "/aim to-backlog"
        )

    def test_unrelated_ready_status_does_not_claim_repository_is_calibrated(self) -> None:
        (self.repo / "aim.profile.yaml").write_text(
            "status: ready\naimRepoProfile:\n  calibration:\n"
            "    evidence:\n      status: ready\n    status: pending\n",
            encoding="utf-8",
        )

        board = build_board(self.repo)

        self.assertFalse(board["source"]["calibrated"])
        self.assertEqual(board["onboarding"]["nextAction"], "/aim calibrate-repo")

    def test_start_reuses_statuses_and_stops_one_repo_bound_instance(self) -> None:
        repo = self.repo.resolve()
        first = control.start(repo, open_browser=False)
        self.assertEqual(first["status"], "running")
        self.assertFalse(first["reused"])
        self.assertEqual(first["productVersion"], "3.0.4")
        with urlopen(f"{first['url']}api/board", timeout=2) as response:
            board = json.loads(response.read().decode("utf-8"))
        self.assertEqual(board["source"]["kind"], "uninitialized")
        self.assertEqual(board["product"]["version"], "3.0.4")
        self.assertIn(
            board["backgroundControl"]["status"], {"connected", "view_only"}
        )

        second = control.start(repo, open_browser=False)
        self.assertTrue(second["reused"])
        self.assertEqual(second["pid"], first["pid"])
        self.assertEqual(control.status(repo)["status"], "running")

        stopped = control.stop(repo)
        self.assertTrue(stopped["stopped"])
        self.assertEqual(control.status(repo)["status"], "stopped")
        self.assertFalse((repo / ".aim").exists())

    def test_stale_metadata_is_removed_without_signalling_the_named_pid(self) -> None:
        repo = self.repo.resolve()
        path = control.metadata_path(repo)
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "instanceVersion": "1.0",
                    "instanceId": "not-a-server-instance-0000000000",
                    "repo": str(repo),
                    "pid": os.getpid(),
                    "port": 9,
                    "url": "http://127.0.0.1:9/",
                    "startedAt": "2026-08-22T10:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        result = control.stop(repo)
        self.assertFalse(result["stopped"])
        self.assertTrue(result["staleMetadataRemoved"])
        self.assertFalse(path.exists())

    def test_missing_repository_fails_with_an_actionable_error(self) -> None:
        with self.assertRaisesRegex(control.AimUiControlError, "was not found"):
            control.resolve_repo(self.root / "missing")

    def test_cli_controls_the_same_instance_across_processes(self) -> None:
        launcher = REPO_ROOT / "scripts/aim_ui_control.py"
        environment = {**os.environ, control.STATE_ENV: str(self.root / "cli-instances")}
        start = subprocess.run(
            [sys.executable, str(launcher), "--json", "start", str(self.repo), "--no-browser"],
            capture_output=True,
            text=True,
            timeout=10,
            env=environment,
        )
        self.assertEqual(start.returncode, 0, start.stderr)
        started = json.loads(start.stdout)
        self.assertEqual(started["status"], "running")
        try:
            status = subprocess.run(
                [sys.executable, str(launcher), "--json", "status", str(self.repo)],
                capture_output=True,
                text=True,
                timeout=10,
                env=environment,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(json.loads(status.stdout)["pid"], started["pid"])
        finally:
            stopped = subprocess.run(
                [sys.executable, str(launcher), "--json", "stop", str(self.repo)],
                capture_output=True,
                text=True,
                timeout=10,
                env=environment,
            )
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            self.assertTrue(json.loads(stopped.stdout)["stopped"])

    def test_concurrent_cli_starts_converge_on_one_instance(self) -> None:
        launcher = REPO_ROOT / "scripts/aim_ui_control.py"
        environment = {
            **os.environ,
            control.STATE_ENV: str(self.root / "race-instances"),
        }
        command = [
            sys.executable,
            str(launcher),
            "--json",
            "start",
            str(self.repo),
            "--no-browser",
        ]
        first = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        second = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        first_stdout, first_stderr = first.communicate(timeout=10)
        second_stdout, second_stderr = second.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, first_stderr)
        self.assertEqual(second.returncode, 0, second_stderr)
        first_result = json.loads(first_stdout)
        second_result = json.loads(second_stdout)
        self.assertEqual(first_result["pid"], second_result["pid"])
        self.assertEqual(
            {first_result["reused"], second_result["reused"]}, {False, True}
        )
        stopped = subprocess.run(
            [sys.executable, str(launcher), "--json", "stop", str(self.repo)],
            capture_output=True,
            text=True,
            timeout=10,
            env=environment,
        )
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertTrue(json.loads(stopped.stdout)["stopped"])

    def test_payload_change_reports_stale_and_replaces_verified_pid(self) -> None:
        payload = self.root / "payload"
        shutil.copytree(REPO_ROOT / "scripts", payload / "scripts")
        shutil.copytree(REPO_ROOT / "aim-ui", payload / "aim-ui")
        shutil.copy2(REPO_ROOT / "VERSION", payload / "VERSION")
        launcher = payload / "scripts/aim_ui_control.py"
        environment = {
            **os.environ,
            control.STATE_ENV: str(self.root / "upgrade-instances"),
        }
        command = [
            sys.executable,
            str(launcher),
            "--json",
            "start",
            str(self.repo),
            "--no-browser",
        ]
        first = subprocess.run(
            command, capture_output=True, text=True, timeout=10, env=environment
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        original = json.loads(first.stdout)
        self.assertTrue(original["compatible"])
        self.assertEqual(len(original["payloadFingerprint"]), 64)
        try:
            app = payload / "aim-ui/app.js"
            app.write_text(
                app.read_text(encoding="utf-8") + "\n// upgraded payload fixture\n",
                encoding="utf-8",
            )
            status = subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "--json",
                    "status",
                    str(self.repo),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                env=environment,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            stale = json.loads(status.stdout)
            self.assertEqual(stale["status"], "stale")
            self.assertFalse(stale["compatible"])
            self.assertEqual(
                stale["observedPayloadFingerprint"], original["payloadFingerprint"]
            )
            self.assertNotEqual(
                stale["expectedPayloadFingerprint"], original["payloadFingerprint"]
            )

            second = subprocess.run(
                command, capture_output=True, text=True, timeout=10, env=environment
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            replacement = json.loads(second.stdout)
            self.assertFalse(replacement["reused"])
            self.assertTrue(replacement["replacedIncompatible"])
            self.assertTrue(replacement["compatible"])
            self.assertNotEqual(replacement["pid"], original["pid"])
            self.assertNotEqual(
                replacement["payloadFingerprint"], original["payloadFingerprint"]
            )
        finally:
            subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "--json",
                    "stop",
                    str(self.repo),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                env=environment,
            )


if __name__ == "__main__":
    unittest.main()

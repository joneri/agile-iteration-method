"""Prevent wrong-instance and CLI transport errors from becoming product proof."""

from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_aim_ui as verification


class ProductVerificationTests(unittest.TestCase):
    def test_doctor_rejects_old_payload_even_when_process_identity_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve()
            receipt = dict(status="running", reused=False, repo=str(repo), pid=123,
                           instanceId="owned-instance-0123456789", port=43210,
                           url="http://127.0.0.1:43210/", bindingFingerprint=None,
                           productVersion=verification.control.resolve_product_version(),
                           payloadFingerprint=verification.control.payload_fingerprint(),
                           protocolVersion=verification.control.UI_PROTOCOL_VERSION)
            health = dict(receipt, status="ok", readOnly=True, repositoryReadOnly=True)
            self.assertEqual(verification.verify_doctor(repo, receipt, health)["status"], "passed")
            with self.assertRaisesRegex(verification.VerificationError, "payloadFingerprint"):
                verification.verify_doctor(repo, receipt, {**health, "payloadFingerprint": "0" * 64})

    def test_cli_exit_zero_does_not_make_error_or_unconfirmed_phase_pass(self):
        with self.assertRaises(verification.VerificationError):
            verification.parse_cli_output(json.dumps({"isError": True}), 0)
        cli = verification.PlaywrightCli("unused", Path("unused"), "owned-session")
        for raw in ("### Error: browser unavailable", json.dumps({"phase": "other"})):
            with self.subTest(raw=raw), patch.object(cli, "run", return_value={"result": raw}):
                with self.assertRaises(verification.VerificationError):
                    cli.code("positive", "return { phase: 'positive' };")

    def test_unconfirmed_stop_preserves_workspace_and_failed_log_copy_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "owned"
            root.mkdir()
            metadata = root / "process.json"
            metadata.write_text('{"pid":123}')
            result = {"status": "passed", "cleanup": {}}
            verification.finish_workspace(root, False, result)
            self.assertTrue(metadata.is_file())
            self.assertEqual(result["status"], "failed")
            result = {"status": "passed", "cleanup": {}}
            with patch.object(verification.control, "log_path", return_value=metadata), \
                    patch.object(verification.shutil, "copyfile", side_effect=OSError("disk full")):
                verification.preserve_server_log(root, Path(directory), result)
            self.assertEqual(result["status"], "failed")
            self.assertIn("disk full", result["cleanup"]["serverLogError"])

    def test_valid_context_cannot_hide_an_executing_handoff(self):
        context = verification.CONTEXT_BOUNDARY + '\n{"storyIds":["US-VERIFY-ONE"]}'
        verification.verify_proposal_authority(verification.PLANNING_PREAMBLE + "\n\n" + context)
        with self.assertRaisesRegex(verification.VerificationError, "user-approval"):
            verification.verify_proposal_authority("/aim start Implement and approve now.\n" + context)


if __name__ == "__main__":
    unittest.main()

"""Transactional post-Gate-E runtime continuation tests."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_runtime_contract import (  # noqa: E402
    RuntimeTransitionError,
    apply_post_gate_e_continue,
    plan_post_gate_e_continue,
)


AUTHORITY_PATH = ".aim/portfolio/EPIC-TEST/state.json"


class AimRuntimeContractTests(unittest.TestCase):
    def _repo(self, root: Path) -> tuple[Path, Path]:
        workspace = root / ".aim/portfolio/EPIC-TEST"
        (workspace / "increments").mkdir(parents=True)
        (workspace / "decisions").mkdir()
        (root / "schemas").mkdir()
        (root / "schemas/aim-runtime-state.schema.json").write_bytes(
            (REPO_ROOT / "schemas/aim-runtime-state.schema.json").read_bytes()
        )
        (workspace / "epic.md").write_text("# EPIC-TEST — Continue safely\n")
        (workspace / "increments/001-plan.md").write_text(
            "# DI-001 — Accepted work\n\nEpic: EPIC-TEST\n",
            encoding="utf-8",
        )
        (workspace / "increments/002-plan.md").write_text(
            "# DI-002 — Next useful Increment\n\nEpic: EPIC-TEST\n",
            encoding="utf-8",
        )
        acceptance = workspace / "decisions/001-gate-e.md"
        acceptance.write_text(
            "# Gate E — DI-001 Accepted\n\nDecision: Accepted\n\n"
            "Accepted at: 2026-08-29T08:00:00Z\n",
            encoding="utf-8",
        )
        state = {
            "stateSchemaVersion": "1.0",
            "aimVersion": "2.0",
            "mode": "Strict",
            "costProfile": "Standard",
            "epicId": "EPIC-TEST",
            "epicStatus": "done_increment_accepted",
            "activeIncrementId": None,
            "previousIncrementId": "DI-001",
            "previousIncrementStatus": "accepted",
            "gateEAcceptance": acceptance.relative_to(root).as_posix(),
            "currentRole": "PO",
            "lastGatePassed": "Gate E",
            "platform": "test",
            "parallelSupport": {
                "available": False,
                "enabled": False,
                "policy": "sequential_fallback",
            },
            "commitMode": "optional",
            "updatedAt": "2026-08-29T08:01:00Z",
        }
        state_path = workspace / "state.json"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        return root, state_path

    def test_preview_and_apply_publish_only_canonical_gate_b_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            preview = plan_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:02:00Z",
            )
            before = state_path.read_bytes()
            self.assertEqual(preview["result"], "planned")
            self.assertEqual(before, state_path.read_bytes())
            self.assertEqual(preview["candidate"]["epicStatus"], "gate_b_pending")
            self.assertEqual(preview["candidate"]["activeIncrementId"], "DI-002")
            self.assertEqual(preview["candidate"]["lastGatePassed"], "Gate A")

            result = apply_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:02:00Z",
                expected_state_sha256=preview["sourceStateSha256"],
            )
            written = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(result["result"], "applied")
        self.assertEqual(written["epicStatus"], "gate_b_pending")
        self.assertEqual(written["activeIncrementId"], "DI-002")
        self.assertEqual(written["currentRole"], "TDO")
        self.assertEqual(written["lastGatePassed"], "Gate A")
        self.assertEqual(written["previousIncrementId"], "DI-001")
        self.assertEqual(written["previousIncrementStatus"], "accepted")
        self.assertEqual(written["uiDecision"]["visibility"], "ready")

    def test_schema_rejection_preserves_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            invalid = json.loads(state_path.read_text(encoding="utf-8"))
            invalid["mode"] = "Unbounded"
            state_path.write_text(json.dumps(invalid, indent=2) + "\n", encoding="utf-8")
            untrusted_schema_path = repo / "schemas/aim-runtime-state.schema.json"
            untrusted_schema = json.loads(
                untrusted_schema_path.read_text(encoding="utf-8")
            )
            untrusted_schema["properties"]["mode"]["enum"].append("Unbounded")
            untrusted_schema_path.write_text(
                json.dumps(untrusted_schema), encoding="utf-8"
            )
            before = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "schema validation"):
                plan_post_gate_e_continue(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    increment_id="DI-002",
                    updated_at="2026-08-29T08:02:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_stale_apply_preserves_newer_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            preview = plan_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:02:00Z",
            )
            newer = json.loads(state_path.read_text(encoding="utf-8"))
            newer["updatedAt"] = "2026-08-29T08:01:30Z"
            state_path.write_text(json.dumps(newer, indent=2) + "\n", encoding="utf-8")
            newer_payload = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "changed since preview"):
                apply_post_gate_e_continue(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    increment_id="DI-002",
                    updated_at="2026-08-29T08:02:00Z",
                    expected_state_sha256=preview["sourceStateSha256"],
                )
            self.assertEqual(newer_payload, state_path.read_bytes())
            self.assertNotEqual(
                hashlib.sha256(newer_payload).hexdigest(), preview["sourceStateSha256"]
            )

    def test_containment_and_missing_plan_fail_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "authorityStatePath"):
                plan_post_gate_e_continue(
                    repo,
                    authority_state_path=".aim/../outside/state.json",
                    increment_id="DI-002",
                    updated_at="2026-08-29T08:02:00Z",
                )
            with self.assertRaisesRegex(RuntimeTransitionError, "plan is invalid"):
                plan_post_gate_e_continue(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    increment_id="DI-003",
                    updated_at="2026-08-29T08:02:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())


if __name__ == "__main__":
    unittest.main()

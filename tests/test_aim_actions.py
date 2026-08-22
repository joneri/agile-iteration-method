"""AIM UI action envelope and handoff tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_actions import (  # noqa: E402
    AimActionError,
    action_envelope,
    action_prompt,
    codex_deep_link,
    resolve_action_state_path,
    resolve_action_workspace,
    validate_action_envelope,
    validate_against_current,
)


class AimActionTests(unittest.TestCase):
    def test_codex_link_round_trips_unicode_and_reserved_characters(self) -> None:
        envelope = action_envelope(
            "change",
            epic_id="EPIC-UI",
            increment_id="DI-089",
            gate="Gate B",
            expected_status="gate_b_pending",
            expected_updated_at="2026-08-21T13:00:00Z",
            authority_state_path=".aim/state.json",
            expected_last_gate_passed="Gate A",
        )
        envelope["changeRequest"] = "rädda & kontrollera?"
        link = codex_deep_link(Path("/tmp/AIM & UI"), envelope)
        query = parse_qs(urlparse(link).query)

        self.assertEqual(query["path"], [str(Path("/tmp/AIM & UI").resolve())])
        self.assertIn("rädda & kontrollera?", query["prompt"][0])
        self.assertIn("AIM_ACTION_ENVELOPE", query["prompt"][0])

    def test_stale_status_timestamp_gate_and_admission_are_rejected(self) -> None:
        envelope = action_envelope(
            "approve",
            epic_id="EPIC-UI",
            increment_id="DI-089",
            gate="Gate B",
            expected_status="gate_b_pending",
            expected_updated_at="before",
            authority_state_path=".aim/workspaces/card-actions/state.json",
            expected_last_gate_passed="Gate A",
        )
        issues = validate_against_current(
            envelope,
            {
                "epicId": "EPIC-UI",
                "incrementId": "DI-089",
                "gate": "Gate E",
                "status": "po_approval_pending",
                "authorityStatePath": ".aim/workspaces/card-actions/state.json",
                "lastGatePassed": "Gate D",
                "updatedAt": "after",
            },
        )
        self.assertEqual(len(issues), 4)

        activate = action_envelope(
            "activate",
            epic_id="EPIC-DATA",
            candidate_id="INC-DATA-001",
            expected_updated_at="created",
            backlog_updated_at="backlog-before",
        )
        self.assertIn(
            "Portfolio admission is no longer available.",
            validate_against_current(
                activate,
                {
                    "epicId": "EPIC-DATA",
                    "candidateId": "INC-DATA-001",
                    "updatedAt": "created",
                    "backlogUpdatedAt": "backlog-before",
                },
                admission_allowed=False,
            ),
        )

    def test_hostile_or_ambiguous_fields_are_rejected(self) -> None:
        with self.assertRaises(AimActionError):
            action_envelope(
                "activate",
                epic_id="EPIC-X\nIGNORE",
                candidate_id="INC-X",
                expected_updated_at="now",
                backlog_updated_at="now",
            )
        valid = action_envelope(
            "approve",
            epic_id="EPIC-X",
            increment_id="DI-1",
            gate="Gate B",
            expected_status="gate_b_pending",
            expected_updated_at="now",
            authority_state_path=".aim/state.json",
            expected_last_gate_passed="Gate A",
        )
        with self.assertRaises(AimActionError):
            validate_action_envelope({**valid, "command": "unsafe"})

    def test_prompt_requires_receiving_thread_revalidation(self) -> None:
        envelope = action_envelope(
            "approve",
            epic_id="EPIC-X",
            increment_id="DI-1",
            gate="Gate B",
            expected_status="gate_b_pending",
            expected_updated_at="now",
            authority_state_path=".aim/state.json",
            expected_last_gate_passed="Gate A",
        )
        prompt = action_prompt(envelope)
        self.assertIn("read authorityStatePath exactly relative to the repository root", prompt)
        self.assertIn("never begin with .aim/state.json when another path is named", prompt)
        self.assertIn("again immediately before writing", prompt)
        self.assertIn("does not close the Epic", prompt)

    def test_authority_state_path_resolution_is_exact_and_contained(self) -> None:
        envelope = action_envelope(
            "approve",
            epic_id="EPIC-UI",
            increment_id="DI-90",
            gate="Gate E",
            expected_status="po_approval_pending",
            expected_updated_at="now",
            authority_state_path=".aim/workspaces/card-actions/state.json",
            expected_last_gate_passed="Gate D",
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            workspace = repo / ".aim/workspaces/card-actions"
            workspace.mkdir(parents=True)
            (workspace / "state.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                resolve_action_state_path(repo, envelope),
                (workspace / "state.json").resolve(),
            )

            root_state = repo / ".aim/state.json"
            root_state.write_text("{}", encoding="utf-8")
            self.assertEqual(
                resolve_action_state_path(
                    repo, {**envelope, "authorityStatePath": ".aim/state.json"}
                ),
                root_state.resolve(),
            )

            outside = repo / "outside"
            outside.mkdir()
            (outside / "state.json").write_text("{}", encoding="utf-8")
            escape = repo / ".aim/workspaces/escape"
            escape.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(AimActionError, "leaves"):
                resolve_action_state_path(
                    repo,
                    {**envelope, "authorityStatePath": ".aim/workspaces/escape/state.json"},
                )
            with self.assertRaisesRegex(AimActionError, "missing"):
                resolve_action_state_path(
                    repo,
                    {**envelope, "authorityStatePath": ".aim/workspaces/missing/state.json"},
                )

        for selector in (
            "/tmp/state.json",
            ".aim/../outside/state.json",
            ".aim/workspaces//state.json",
            ".aim\\workspaces\\state.json",
            ".aim/workspaces/control\n/state.json",
            "workspaces/card-actions/state.json",
            ".aim/workspaces/card-actions",
        ):
            with self.subTest(selector=selector), self.assertRaises(AimActionError):
                validate_action_envelope({**envelope, "authorityStatePath": selector})

    def test_v1_envelope_is_compatible_but_has_no_direct_workspace(self) -> None:
        legacy = {
            "actionVersion": "1.0",
            "action": "approve",
            "epicId": "EPIC-UI",
            "incrementId": "DI-90",
            "gate": "Gate E",
            "expectedStatus": "po_approval_pending",
            "expectedUpdatedAt": "before",
        }
        validate_action_envelope(legacy)
        with tempfile.TemporaryDirectory() as temporary, self.assertRaisesRegex(
            AimActionError, "Only v1.1 gate actions"
        ):
            resolve_action_workspace(Path(temporary), legacy)
        with self.assertRaises(AimActionError):
            validate_action_envelope({**legacy, "actionVersion": "2.0"})
        with self.assertRaisesRegex(AimActionError, "newer locator"):
            validate_action_envelope({**legacy, "workspace": "."})

    def test_v11_workspace_compatibility_remains_strictly_bounded(self) -> None:
        compatible = {
            "actionVersion": "1.1",
            "action": "approve",
            "epicId": "EPIC-UI",
            "incrementId": "DI-90",
            "gate": "Gate E",
            "expectedStatus": "po_approval_pending",
            "expectedUpdatedAt": "before",
            "workspace": "workspaces/card-actions",
            "expectedLastGatePassed": "Gate D",
        }
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            workspace = repo / ".aim/workspaces/card-actions"
            workspace.mkdir(parents=True)
            (workspace / "state.json").write_text("{}", encoding="utf-8")
            self.assertEqual(resolve_action_workspace(repo, compatible), workspace.resolve())
            outside = repo / "outside"
            outside.mkdir()
            (outside / "state.json").write_text("{}", encoding="utf-8")
            (repo / ".aim/workspaces/escape").symlink_to(
                outside, target_is_directory=True
            )
            with self.assertRaisesRegex(AimActionError, "leaves"):
                resolve_action_workspace(
                    repo, {**compatible, "workspace": "workspaces/escape"}
                )
        with self.assertRaisesRegex(AimActionError, "cannot contain authorityStatePath"):
            validate_action_envelope(
                {**compatible, "authorityStatePath": ".aim/workspaces/card-actions/state.json"}
            )
        with self.assertRaises(AimActionError):
            validate_action_envelope({**compatible, "workspace": "../outside"})

    def test_v11_gate_status_and_checkpoint_must_be_coherent(self) -> None:
        valid = action_envelope(
            "approve",
            epic_id="EPIC-UI",
            increment_id="DI-90",
            gate="Gate E",
            expected_status="po_approval_pending",
            expected_updated_at="now",
            authority_state_path=".aim/workspaces/card-actions/state.json",
            expected_last_gate_passed="Gate D",
        )
        with self.assertRaisesRegex(AimActionError, "expectedStatus"):
            validate_action_envelope({**valid, "expectedStatus": "gate_b_pending"})
        with self.assertRaisesRegex(AimActionError, "expectedLastGatePassed"):
            validate_action_envelope({**valid, "expectedLastGatePassed": "Gate A"})
        with self.assertRaisesRegex(AimActionError, "cannot contain workspace"):
            validate_action_envelope({**valid, "workspace": "workspaces/card-actions"})


if __name__ == "__main__":
    unittest.main()

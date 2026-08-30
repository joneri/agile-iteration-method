"""Runtime-state schema and read-only compatibility regression tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_validator.runtime_state import (  # noqa: E402
    RUNTIME_STATE_SCHEMA_PATH,
    SUPPORTED_STATE_SCHEMA_VERSION,
    load_runtime_state,
)
from aim_validator.schema_subset import unsupported_keywords  # noqa: E402


def canonical_state() -> dict[str, object]:
    return {
        "stateSchemaVersion": "1.0",
        "aimVersion": "2.0",
        "mode": "Strict",
        "costProfile": "Standard",
        "epicId": "EPIC-TEST",
        "epicStatus": "gate_b_pending",
        "activeIncrementId": "DI-001",
        "currentRole": "TDO",
        "lastGatePassed": "Gate A",
        "platform": "test",
        "parallelSupport": {
            "available": False,
            "enabled": False,
            "policy": "sequential_fallback",
        },
        "commitMode": "optional",
        "updatedAt": "2026-08-21T00:00:00Z",
    }


class RuntimeStateSchemaTests(unittest.TestCase):
    def _repo(self, root: Path, state: dict[str, object]) -> Path:
        (root / ".aim/decisions").mkdir(parents=True)
        (root / "schemas").mkdir()
        (root / RUNTIME_STATE_SCHEMA_PATH).write_text(
            (REPO_ROOT / RUNTIME_STATE_SCHEMA_PATH).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / ".aim/state.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )
        (root / ".aim/decisions/001-gate-b.md").write_text(
            "Mode: Strict\n\nCost profile: Standard\n", encoding="utf-8"
        )
        return root

    def test_public_schema_is_supported_draft_2020_12(self) -> None:
        schema = json.loads(
            (REPO_ROOT / RUNTIME_STATE_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertEqual(schema["properties"]["stateSchemaVersion"]["const"], "1.0")
        self.assertTrue(schema["additionalProperties"])
        self.assertEqual(unsupported_keywords(schema), [])

    def test_current_state_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(
                self._repo(Path(temporary), canonical_state())
            )
        self.assertEqual(result.classification, "current")
        self.assertEqual(result.findings, ())

    def test_optional_accepted_history_contract_validates(self) -> None:
        state = canonical_state()
        state.update(
            {
                "epicStatus": "epic_complete",
                "activeIncrementId": None,
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "previousIncrementId": "DI-042",
                "previousIncrementStatus": "accepted",
                "gateEAcceptance": ".aim/portfolio/EPIC-TEST/decisions/gate-e-accepted.md",
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(self._repo(Path(temporary), state))
        self.assertEqual(result.classification, "current")
        self.assertEqual(result.findings, ())

    def test_modern_closure_bindings_must_be_complete_and_terminal(self) -> None:
        completed = canonical_state()
        completed.update(
            {
                "epicStatus": "epic_complete",
                "activeIncrementId": None,
                "currentRole": "PO",
                "lastGatePassed": "Gate E",
                "epicClosureEvidence": ".aim/decisions/closure.json",
                "epicClosureEvidenceSha256": "a" * 64,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            partial = load_runtime_state(self._repo(Path(temporary), completed))
        self.assertEqual(partial.classification, "contradictory")
        self.assertTrue(any("partial closure" in item.rule for item in partial.findings))

        premature = canonical_state()
        premature.update(
            {
                "epicClosureEvidence": ".aim/decisions/closure.json",
                "epicClosureEvidenceSha256": "a" * 64,
                "epicClosureEvidenceSetSha256": "b" * 64,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(self._repo(Path(temporary), premature))
        self.assertEqual(result.classification, "contradictory")
        self.assertTrue(
            any("before epic_complete" in item.rule for item in result.findings)
        )

    def test_portfolio_start_may_reserve_canonical_increment_before_gate_b(self) -> None:
        state = canonical_state()
        state.update(
            {
                "epicStatus": "gate_a_pending",
                "activeIncrementId": None,
                "plannedIncrementId": "DI-042",
                "currentRole": "PO",
                "lastGatePassed": None,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(self._repo(Path(temporary), state))
        self.assertEqual(result.classification, "current")
        self.assertEqual(result.findings, ())

    def test_legacy_aliases_normalize_without_writing(self) -> None:
        state = canonical_state()
        del state["stateSchemaVersion"]
        state["cost"] = state.pop("costProfile")
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), state)
            state_path = repo / ".aim/state.json"
            before = state_path.read_bytes()
            result = load_runtime_state(repo)
            after = state_path.read_bytes()
        self.assertEqual(result.classification, "legacy-compatible")
        self.assertEqual(result.normalized["stateSchemaVersion"], SUPPORTED_STATE_SCHEMA_VERSION)
        self.assertEqual(result.normalized["costProfile"], "Standard")
        self.assertEqual(before, after)

    def test_conflicting_alias_is_contradictory(self) -> None:
        state = canonical_state()
        state["cost"] = "Deep"
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(self._repo(Path(temporary), state))
        self.assertEqual(result.classification, "contradictory")
        self.assertTrue(any("conflicts" in item.rule for item in result.findings))

    def test_unsupported_version_is_contradictory(self) -> None:
        state = canonical_state()
        state["stateSchemaVersion"] = "9.0"
        with tempfile.TemporaryDirectory() as temporary:
            result = load_runtime_state(self._repo(Path(temporary), state))
        self.assertEqual(result.classification, "unsupported")
        self.assertTrue(any(item.result == "contradictory" for item in result.findings))

    def test_gate_b_cost_mismatch_is_contradictory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), canonical_state())
            (repo / ".aim/decisions/001-gate-b.md").write_text(
                "Mode: Strict\n\nCost profile: Deep\n", encoding="utf-8"
            )
            result = load_runtime_state(repo)
        self.assertEqual(result.classification, "contradictory")
        self.assertTrue(any("costProfile" in item.rule for item in result.findings))

    def test_cost_selection_contract_covers_required_cases(self) -> None:
        core = " ".join(
            (REPO_ROOT / "docs/workflow/agile-iteration-method.md")
            .read_text(encoding="utf-8")
            .split()
        )
        cost = " ".join(
            (REPO_ROOT / "docs/workflow/cost-control-mode.md")
            .read_text(encoding="utf-8")
            .split()
        )
        for marker in (
            "completed Epic's persisted profile is history",
            "persisted cost profile remains authoritative",
            "escalation or de-escalation",
        ):
            self.assertIn(marker, core)
        self.assertIn("does not by itself require", cost)
        self.assertIn("public release path", cost)

    def test_missing_schema_is_blocked_without_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self._repo(Path(temporary), canonical_state())
            (repo / RUNTIME_STATE_SCHEMA_PATH).unlink()
            result = load_runtime_state(repo)
        self.assertEqual(result.classification, "blocked")
        self.assertTrue(any(item.result == "blocked" for item in result.findings))


if __name__ == "__main__":
    unittest.main()

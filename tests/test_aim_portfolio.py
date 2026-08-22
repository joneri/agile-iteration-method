"""Portfolio focus and admission policy tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from aim_portfolio import (  # noqa: E402
    activation_decision,
    load_portfolio_control,
    project_portfolio_control,
    validate_control_document,
)
from aim_validator.schema_subset import unsupported_keywords, validate  # noqa: E402


class AimPortfolioTests(unittest.TestCase):
    def test_schema_supports_bounded_focus_and_capacity_only(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas/aim-portfolio-control.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(unsupported_keywords(schema), [])
        control = {
            "controlVersion": "1.0",
            "maxActiveEpics": 2,
            "focusedEpicId": "EPIC-UI",
            "updatedAt": "2026-08-21T18:20:00Z",
        }
        self.assertEqual(validate(control, schema), [])
        self.assertEqual(validate_control_document(control), [])
        control["gate"] = "Gate B"
        self.assertTrue(any("additional property" in issue.message for issue in validate(control, schema)))
        self.assertTrue(any("unsupported fields" in issue for issue in validate_control_document(control)))

    def test_missing_control_preserves_unbounded_legacy_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            aim_root = Path(temporary)
            control = load_portfolio_control(aim_root)
            projection, warnings = project_portfolio_control(
                aim_root,
                [{"id": "EPIC-ONE", "lifecycle": "running"}],
            )
        self.assertTrue(control["valid"])
        self.assertFalse(control["configured"])
        self.assertEqual(projection["admission"], "unbounded")
        self.assertEqual(warnings, [])
        self.assertTrue(
            activation_decision(control, ["EPIC-ONE"], "EPIC-TWO")["allowed"]
        )

    def test_capacity_blocks_new_epic_but_allows_existing_epic(self) -> None:
        control = {
            "configured": True,
            "valid": True,
            "maxActiveEpics": 1,
            "focusedEpicId": "EPIC-ONE",
        }
        blocked = activation_decision(control, ["EPIC-ONE"], "EPIC-TWO")
        resumed = activation_decision(control, ["EPIC-ONE"], "EPIC-ONE")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason"], "capacity_full")
        self.assertTrue(resumed["allowed"])
        self.assertEqual(resumed["reason"], "already_running")

    def test_lower_capacity_reports_over_capacity_without_mutating_epics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            aim_root = Path(temporary)
            (aim_root / "portfolio-control.json").write_text(
                json.dumps(
                    {
                        "controlVersion": "1.0",
                        "maxActiveEpics": 1,
                        "focusedEpicId": "EPIC-TWO",
                        "updatedAt": "2026-08-21T18:20:00Z",
                    }
                ),
                encoding="utf-8",
            )
            epics = [
                {"id": "EPIC-ONE", "lifecycle": "running"},
                {"id": "EPIC-TWO", "lifecycle": "running"},
            ]
            before = json.dumps(epics, sort_keys=True)
            projection, warnings = project_portfolio_control(aim_root, epics)
        self.assertEqual(json.dumps(epics, sort_keys=True), before)
        self.assertEqual(projection["admission"], "over_capacity")
        self.assertTrue(projection["overCapacity"])
        self.assertEqual(projection["availableSlots"], 0)
        self.assertEqual(projection["focusStatus"], "running")
        self.assertEqual(warnings, [])

    def test_invalid_configured_control_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            aim_root = Path(temporary)
            (aim_root / "portfolio-control.json").write_text(
                '{"controlVersion":"1.0","maxActiveEpics":0,"updatedAt":"now"}',
                encoding="utf-8",
            )
            control = load_portfolio_control(aim_root)
            projection, warnings = project_portfolio_control(aim_root, [])
        self.assertFalse(control["valid"])
        self.assertEqual(projection["admission"], "blocked")
        self.assertTrue(warnings)
        self.assertFalse(activation_decision(control, [], "EPIC-ONE")["allowed"])

    def test_control_symlink_is_rejected_without_reading_external_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            aim_root = root / ".aim"
            aim_root.mkdir()
            outside = root / "outside.json"
            outside.write_text(
                '{"controlVersion":"1.0","maxActiveEpics":2,"updatedAt":"now"}',
                encoding="utf-8",
            )
            (aim_root / "portfolio-control.json").symlink_to(outside)
            control = load_portfolio_control(aim_root)

        self.assertFalse(control["valid"])
        self.assertIn("must not be a symbolic link", control["issue"])


if __name__ == "__main__":
    unittest.main()

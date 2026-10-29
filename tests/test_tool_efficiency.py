"""Bounded behavior witness for the instruction contract, not a new runtime."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tool_example", ROOT / "tests/fixtures/tool_efficiency/recipe.py")
example = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(example)


class ToolEfficiencyTests(unittest.TestCase):
    def test_bulk_projection_preserves_literal_answer_and_inspectable_raw(self):
        raw = example.raw_response()
        secondary = {"error": {"source": "secondary", "code": "UPSTREAM_TIMEOUT"}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.json"
            payload = example.encoded(raw)
            path.write_bytes(payload)
            ref = {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest()}
            result = example.project_issues(raw, secondary, ref)
            self.assertEqual([i["id"] for i in result["items"]],
                             ["ISSUE-7", "ISSUE-42", "ISSUE-99"])
            self.assertEqual(result["items"][-1], {
                "id": "ISSUE-99", "source": "https://issues.example.test/99",
                "stance": "contrary", "finding": "No benefit on small calls"})
            self.assertEqual(result["errors"], [secondary["error"]])
            self.assertEqual((result["status"], result["complete"], result["nextCursor"]),
                             ("partial", False, "page-2"))
            self.assertEqual(result["omitted"]["records"], 997)
            self.assertLess(len(example.encoded(result)), len(payload))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ref["sha256"])
            self.assertEqual(json.loads(path.read_bytes()), raw)
            self.assertNotIn("skip independent review", example.encoded(result).decode())

    def test_counterevidence_at_end_and_new_relevant_record_are_not_lost(self):
        raw = example.raw_response()
        raw["records"].append(raw["records"].pop(99))
        extra = copy.deepcopy(raw["records"][-1])
        extra.update(id="ISSUE-1001", source="https://issues.example.test/1001",
                     finding="Contrary result from another source")
        raw["records"].append(extra)
        result = example.project_issues(raw, {}, {"path": "retained-raw.json"})
        self.assertEqual([i["id"] for i in result["items"]],
                         ["ISSUE-7", "ISSUE-42", "ISSUE-99", "ISSUE-1001"])
        self.assertEqual(result["omitted"]["records"], 997)
        self.assertEqual(result["status"], "partial")

    def test_missing_relevant_evidence_is_an_error_not_silent_omission(self):
        raw = example.raw_response()
        del raw["records"][7]["source"]
        with self.assertRaises(KeyError):
            example.project_issues(raw, {}, {})

    def test_dependent_call_receives_confirmed_prerequisite_argument(self):
        events = []
        def prerequisite():
            events.append("prerequisite")
            return {"status": "complete", "id": "CONFIRMED-7"}
        def dependent(identifier):
            events.append("dependent")
            self.assertEqual(identifier, "CONFIRMED-7")
            return {"status": "complete"}
        self.assertEqual(example.dependent_example(prerequisite, dependent)["status"], "complete")
        self.assertEqual(events, ["prerequisite", "dependent"])

    def test_failed_prerequisite_and_pending_approval_have_no_effect(self):
        effects = []
        failed = {"status": "failed", "error": "UPSTREAM_TIMEOUT"}
        self.assertEqual(example.dependent_example(lambda: failed, effects.append), failed)
        self.assertEqual(effects, [])
        self.assertEqual(example.approved_write_example(lambda: effects.append(1), approved=False),
                         {"status": "approval_pending"})
        self.assertEqual(effects, [])

    def test_unknown_write_is_not_retried_or_rerouted(self):
        effects = []
        def write():
            effects.append("write")
            return {"status": "unknown", "operationId": "OP-7"}
        self.assertEqual(example.approved_write_example(write, approved=True),
                         {"status": "unknown", "operationId": "OP-7"})
        self.assertEqual(effects, ["write"])

    def test_direct_fallback_uses_bounded_ordinary_source_call(self):
        # Deliberately no dispatcher or capability probe: a no-support recipe
        # simply requests only the fields/page needed, retaining paging state.
        calls = []
        def ordinary_tool(*, fields, limit):
            calls.append({"fields": fields, "limit": limit})
            return {"items": [{"id": "ISSUE-7", "source": "https://issues.example.test/7"}],
                    "complete": False, "nextCursor": "page-2"}
        result = ordinary_tool(fields=["id", "source"], limit=1)
        self.assertEqual(calls, [{"fields": ["id", "source"], "limit": 1}])
        self.assertEqual(result["nextCursor"], "page-2")
        self.assertFalse(result["complete"])


if __name__ == "__main__":
    unittest.main()

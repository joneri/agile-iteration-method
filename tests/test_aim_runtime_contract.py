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
    MAX_REFERENCED_EVIDENCE_BYTES,
    RuntimeTransitionError,
    apply_epic_closure,
    apply_post_gate_e_continue,
    plan_epic_closure,
    plan_post_gate_e_continue,
)


AUTHORITY_PATH = ".aim/portfolio/EPIC-TEST/state.json"


class AimRuntimeContractTests(unittest.TestCase):
    @staticmethod
    def _reference(path: Path, workspace: Path, kind: str) -> dict[str, str]:
        return {
            "path": path.relative_to(workspace).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": kind,
        }

    def _repo(self, root: Path) -> tuple[Path, Path]:
        workspace = root / ".aim/portfolio/EPIC-TEST"
        (workspace / "increments").mkdir(parents=True)
        (workspace / "decisions").mkdir()
        (root / "schemas").mkdir()
        (root / "schemas/aim-runtime-state.schema.json").write_bytes(
            (REPO_ROOT / "schemas/aim-runtime-state.schema.json").read_bytes()
        )
        (workspace / "epic.md").write_text(
            "# EPIC-TEST — Continue safely\n\nOutcome class: Product\n\n"
            "## Acceptance criteria\n\n1. The representative journey works.\n"
        )
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

    def _closure_evidence(
        self, repo: Path, *, outcome_class: str = "product"
    ) -> str:
        workspace = repo / ".aim/portfolio/EPIC-TEST"
        evidence_dir = workspace / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        black_box = evidence_dir / "black-box.json"
        black_box.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "kind": "black_box_result",
                    "status": "passed",
                    "representative": True,
                    "operatorAssistance": False,
                    "entryPoint": "public CLI",
                    "scenario": "Run the representative user journey",
                    "expectedOutcome": "The requested outcome is delivered",
                    "actualOutcome": "The requested outcome was delivered",
                    "performedBy": "reviewer",
                    "startedAt": "2026-08-29T08:00:00Z",
                    "completedAt": "2026-08-29T08:01:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        negative_test = evidence_dir / "negative-test.md"
        negative_test.write_text(
            "# Negative test\n\nA repeated unsupported closure was rejected.\n",
            encoding="utf-8",
        )
        authority = workspace / "decisions/epic-closure-authority.md"
        authority.write_text(
            "# Epic closure — EPIC-TEST\n\nDecision: Approved\n\n"
            "Authority: user\n\nThe user separately approved Epic closure.\n",
            encoding="utf-8",
        )
        black_box_ref = self._reference(black_box, workspace, "black_box_result")
        path = workspace / "decisions/epic-closure-truth.json"
        path.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "epicId": "EPIC-TEST",
                    "outcomeClass": outcome_class,
                    "recommendation": "close",
                    "acceptanceCriteria": [
                        {
                            "id": "AC-1",
                            "status": "proven",
                            "evidenceClass": "representative",
                            "evidence": [black_box_ref],
                        }
                    ],
                    "counterevidence": {
                        "searched": True,
                        "unresolvedFindings": [],
                        "evidence": [
                            self._reference(negative_test, workspace, "negative_test")
                        ],
                    },
                    "blackBoxValidation": {
                        "status": "passed",
                        "representative": True,
                        "operatorAssistance": False,
                        "entryPoint": "public CLI",
                        "scenario": "Run the representative user journey",
                        "expectedOutcome": "The requested outcome is delivered",
                        "actualOutcome": "The requested outcome was delivered",
                        "performedBy": "reviewer",
                        "startedAt": "2026-08-29T08:00:00Z",
                        "completedAt": "2026-08-29T08:01:00Z",
                        "evidence": [black_box_ref],
                    },
                    "remainingGaps": [],
                    "contradictions": [],
                    "decisionAuthority": "user",
                    "authorityEvidence": [
                        self._reference(authority, workspace, "authority_decision")
                    ],
                    "decidedAt": "2026-08-29T08:02:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path.relative_to(repo).as_posix()

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

    def test_continuation_drops_nonterminal_closure_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            source = json.loads(state_path.read_text(encoding="utf-8"))
            source.update(
                {
                    "epicClosureEvidence": ".aim/decisions/stale.json",
                    "epicClosureEvidenceSha256": "a" * 64,
                    "epicClosureEvidenceSetSha256": "b" * 64,
                }
            )
            state_path.write_text(
                json.dumps(source, indent=2) + "\n", encoding="utf-8"
            )
            preview = plan_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:02:00Z",
            )

        for field in (
            "epicClosureEvidence",
            "epicClosureEvidenceSha256",
            "epicClosureEvidenceSetSha256",
        ):
            self.assertNotIn(field, preview["candidate"])

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

    def test_truth_audited_closure_previews_and_applies_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence = self._closure_evidence(repo)
            preview = plan_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence,
                updated_at="2026-08-29T08:03:00Z",
            )
            self.assertEqual(preview["candidate"]["epicStatus"], "epic_complete")
            self.assertEqual(preview["candidate"]["epicClosureEvidence"], evidence)
            self.assertEqual(
                preview["epicClosureEvidenceSha256"],
                preview["candidate"]["epicClosureEvidenceSha256"],
            )
            result = apply_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence,
                updated_at="2026-08-29T08:03:00Z",
                expected_state_sha256=preview["sourceStateSha256"],
                expected_closure_evidence_sha256=preview["candidate"][
                    "epicClosureEvidenceSha256"
                ],
                expected_evidence_set_sha256=preview[
                    "epicClosureEvidenceSetSha256"
                ],
            )
            written = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(result["result"], "applied")
        self.assertEqual(written["epicStatus"], "epic_complete")
        self.assertEqual(written["epicClosureEvidence"], evidence)
        self.assertRegex(written["epicClosureEvidenceSha256"], r"^[0-9a-f]{64}$")

    def test_closure_apply_rejects_evidence_changed_after_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence = self._closure_evidence(repo)
            preview = plan_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence,
                updated_at="2026-08-29T08:03:00Z",
            )
            evidence_path = repo / evidence
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            payload["decidedAt"] = "2026-08-29T08:03:01Z"
            evidence_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "changed since preview"):
                apply_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence,
                    updated_at="2026-08-29T08:03:00Z",
                    expected_state_sha256=preview["sourceStateSha256"],
                    expected_closure_evidence_sha256=preview["candidate"][
                        "epicClosureEvidenceSha256"
                    ],
                    expected_evidence_set_sha256=preview[
                        "epicClosureEvidenceSetSha256"
                    ],
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_apply_rejects_referenced_bytes_changed_after_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence = self._closure_evidence(repo)
            preview = plan_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence,
                updated_at="2026-08-29T08:03:00Z",
            )
            black_box = repo / ".aim/portfolio/EPIC-TEST/evidence/black-box.json"
            black_box.write_text(
                black_box.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            before = state_path.read_bytes()

            with self.assertRaisesRegex(
                RuntimeTransitionError, "Referenced Epic evidence changed|sha256 does not match"
            ):
                apply_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence,
                    updated_at="2026-08-29T08:03:00Z",
                    expected_state_sha256=preview["sourceStateSha256"],
                    expected_closure_evidence_sha256=preview[
                        "epicClosureEvidenceSha256"
                    ],
                    expected_evidence_set_sha256=preview[
                        "epicClosureEvidenceSetSha256"
                    ],
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_rejects_empty_evidence_and_prose_black_box_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            black_box = repo / ".aim/portfolio/EPIC-TEST/evidence/black-box.json"
            black_box.write_text("Representative black-box result: PASS\n", encoding="utf-8")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            reference = evidence["blackBoxValidation"]["evidence"][0]
            reference["sha256"] = hashlib.sha256(black_box.read_bytes()).hexdigest()
            evidence["acceptanceCriteria"][0]["evidence"][0]["sha256"] = reference[
                "sha256"
            ]
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "not readable JSON"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

            self._closure_evidence(repo)
            negative = repo / ".aim/portfolio/EPIC-TEST/evidence/negative-test.md"
            negative.write_bytes(b"")
            with self.assertRaisesRegex(RuntimeTransitionError, "evidence file is empty"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )

    def test_implementation_side_cannot_self_attest_black_box_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            black_box = repo / ".aim/portfolio/EPIC-TEST/evidence/black-box.json"
            result = json.loads(black_box.read_text(encoding="utf-8"))
            result["performedBy"] = "Dev"
            black_box.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            digest = hashlib.sha256(black_box.read_bytes()).hexdigest()
            evidence["acceptanceCriteria"][0]["evidence"][0]["sha256"] = digest
            evidence["blackBoxValidation"]["evidence"][0]["sha256"] = digest
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "implementation side"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_normalizes_criterion_ids_and_parses_bold_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            epic_path = repo / ".aim/portfolio/EPIC-TEST/epic.md"
            epic_path.write_text(
                "# EPIC-TEST — Continue safely\n\nOutcome class: Product\n\n"
                "## Acceptance criteria\n\n- **AC-1 — The representative journey works.**\n",
                encoding="utf-8",
            )
            evidence_path = repo / self._closure_evidence(repo)
            preview = plan_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                updated_at="2026-08-29T08:03:00Z",
            )
            self.assertEqual(preview["candidate"]["epicStatus"], "epic_complete")
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            duplicate = dict(evidence["acceptanceCriteria"][0])
            duplicate["id"] = "ac-1"
            evidence["acceptanceCriteria"].append(duplicate)
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "duplicates id AC-1"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_requires_separate_matching_authority_and_can_continue(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence.pop("authorityEvidence")
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "authority"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

            continuation = plan_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:04:00Z",
            )
            applied = apply_post_gate_e_continue(
                repo,
                authority_state_path=AUTHORITY_PATH,
                increment_id="DI-002",
                updated_at="2026-08-29T08:04:00Z",
                expected_state_sha256=continuation["sourceStateSha256"],
            )
            self.assertEqual(applied["candidate"]["epicStatus"], "gate_b_pending")
            self.assertEqual(applied["candidate"]["previousIncrementId"], "DI-001")

    def test_product_closure_rejects_poc_or_assisted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["acceptanceCriteria"][0]["evidenceClass"] = "synthetic"
            evidence["blackBoxValidation"]["representative"] = False
            evidence["blackBoxValidation"]["operatorAssistance"] = True
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(
                RuntimeTransitionError, "representative evidence|synthetic"
            ):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_explicit_poc_epic_can_close_on_its_bounded_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            epic_path = repo / ".aim/portfolio/EPIC-TEST/epic.md"
            epic_path.write_text(
                epic_path.read_text(encoding="utf-8").replace(
                    "Outcome class: Product", "Outcome class: POC"
                ),
                encoding="utf-8",
            )
            evidence = self._closure_evidence(repo, outcome_class="poc")
            preview = plan_epic_closure(
                repo,
                authority_state_path=AUTHORITY_PATH,
                closure_evidence_path=evidence,
                updated_at="2026-08-29T08:03:00Z",
            )
            self.assertEqual(preview["candidate"]["epicStatus"], "epic_complete")
            self.assertEqual(state_path.read_text(encoding="utf-8").count("epic_complete"), 0)

    def test_closure_rejects_unproven_criteria_gaps_and_contradictions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["acceptanceCriteria"][0]["status"] = "partial"
            evidence["counterevidence"]["unresolvedFindings"] = ["repeat failed"]
            evidence["remainingGaps"] = ["GitHub trigger missing"]
            evidence["contradictions"] = ["Done claim conflicts with black-box run"]
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "not proven"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_requires_exact_complete_epic_criterion_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            epic_path = repo / ".aim/portfolio/EPIC-TEST/epic.md"
            epic_path.write_text(
                epic_path.read_text(encoding="utf-8")
                + "2. Repeat and resume are idempotent.\n",
                encoding="utf-8",
            )
            evidence = self._closure_evidence(repo)
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "omits.*AC-2"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence,
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_authority_record_cannot_substitute_for_criterion_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["acceptanceCriteria"][0]["evidence"] = evidence[
                "authorityEvidence"
            ]
            evidence_path.write_text(
                json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
            )
            before = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "no proof evidence"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_rejects_missing_or_escaped_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["acceptanceCriteria"][0]["evidence"] = [
                {"path": "../invented.md", "sha256": "0" * 64, "kind": "review"}
            ]
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "unsafe evidence path"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

    def test_closure_rejects_symlinked_and_oversized_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            negative = repo / ".aim/portfolio/EPIC-TEST/evidence/negative-test.md"
            outside = repo / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            negative.unlink()
            negative.symlink_to(outside)
            before = state_path.read_bytes()
            with self.assertRaisesRegex(RuntimeTransitionError, "missing or unsafe"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())

            negative.unlink()
            negative.write_bytes(b"x" * (MAX_REFERENCED_EVIDENCE_BYTES + 1))
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["counterevidence"]["evidence"][0]["sha256"] = hashlib.sha256(
                negative.read_bytes()
            ).hexdigest()
            evidence_path.write_text(
                json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeTransitionError, "size limit"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )

    def test_closure_rejects_same_evidence_path_replayed_as_another_kind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, state_path = self._repo(Path(temporary))
            evidence_path = repo / self._closure_evidence(repo)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            replay = dict(evidence["acceptanceCriteria"][0]["evidence"][0])
            replay["kind"] = "negative_test"
            evidence["counterevidence"]["evidence"] = [replay]
            evidence_path.write_text(
                json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
            )
            before = state_path.read_bytes()

            with self.assertRaisesRegex(RuntimeTransitionError, "contradictory bindings"):
                plan_epic_closure(
                    repo,
                    authority_state_path=AUTHORITY_PATH,
                    closure_evidence_path=evidence_path.relative_to(repo).as_posix(),
                    updated_at="2026-08-29T08:03:00Z",
                )
            self.assertEqual(before, state_path.read_bytes())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Inspect engineering evidence and share bounded, generalized local learning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aim_quality.evidence import check_claims
from aim_quality.files import fingerprint, read_evidence
from aim_quality.skills import suggest_skills
from aim_quality.timing import summarize_timing, summarize_trace, TRACE_LIMIT, TRACE_ACTIVITIES
from aim_quality.profiles import check_profiles
from aim_quality.localities import check_localities
from aim_quality.delegation import check_delegation
from aim_quality.review import check_review
from aim_quality.knowledge import check_knowledge_use
from aim_quality.patterns import lookup as lookup_pitfalls


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key in lesson")
        result[key] = value
    return result


def _learning(args):
    # Optional capability: unavailable SQLite must not break other commands.
    try:
        import sqlite3
        from aim_quality import learning
    except ImportError as exc:
        raise ValueError("Shared learning requires Python SQLite with FTS5; local delivery evidence is unchanged") from exc

    registry = args.registry or learning.default_registry()
    try:
        if args.learning_action == "triage":
            try:
                record = json.loads(read_evidence(args.repo, args.record, 2_000_000), object_pairs_hook=_unique_object)
                return learning.triage(record, args.limit)
            except RecursionError as exc:
                raise ValueError("Triage record exceeds its nesting limit") from exc
        if args.learning_action == "init":
            return learning.initialize(registry)
        if args.learning_action == "recall":
            return learning.recall(registry, args.text, args.phase, args.technology)
        if args.learning_action == "history":
            return learning.history(registry, args.lesson_id)
        evidence = {"path": args.evidence, "sha256": args.evidence_sha256}
        if args.learning_action == "withdraw":
            return learning.withdraw(registry, args.repo, args.lesson_id,
                                     args.expected_revision, args.reason, evidence)
        raw = sys.stdin.buffer.read(32769)
        if len(raw) > 32768:
            raise ValueError("Lesson input exceeds 32768 bytes")
        try:
            lesson = json.loads(raw, object_pairs_hook=_unique_object)
        except RecursionError as exc:
            raise ValueError("Lesson input exceeds its nesting limit") from exc
        return learning.share(registry, args.repo, lesson, evidence,
                              lesson_id=args.lesson_id, expected_revision=args.expected_revision)
    except sqlite3.Error as exc:
        # A sharing failure never changes the result of an earlier local check.
        raise ValueError("Shared learning registry unavailable; local delivery evidence is unchanged") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    learning = commands.add_parser("learning", help="Recall or explicitly share generalized lessons across local projects")
    actions = learning.add_subparsers(dest="learning_action", required=True)
    for name in ("init", "recall", "share", "withdraw", "history", "triage"):
        action = actions.add_parser(name)
        action.add_argument("--registry", type=Path, help="Override the shared local registry")
        if name == "triage":
            action.add_argument("--record", required=True, help="Existing local maintenance record; referenced evidence is never followed")
            action.add_argument("--limit", type=int, default=3, help="Bounded detail preview, 1–100; summary covers every record")
        if name == "recall":
            action.add_argument("--text", default="", help="Sanitized task, symptom or technical question")
            action.add_argument("--phase", choices=("planning", "implementation", "review", "diagnosis"), default="planning")
            action.add_argument("--technology", action="append", default=[])
        if name in ("share", "withdraw"):
            action.add_argument("--evidence", required=True, help="Existing proof, relative to --repo")
            action.add_argument("--evidence-sha256", required=True)
            action.add_argument("--expected-revision", type=int, required=name == "withdraw")
        if name in ("share", "withdraw", "history"):
            action.add_argument("--lesson-id", required=name != "share")
        if name == "withdraw":
            action.add_argument("--reason", required=True)
    pitfalls = commands.add_parser("pitfalls", help="Look up bounded engineering advice for explicit concern tags")
    pitfalls.add_argument("--concern", action="append", required=True)
    skills = commands.add_parser("skills", help="Propose skills without installing them")
    skills.add_argument("--requirements", action="append", default=None)
    profiles = commands.add_parser("profiles", help="Validate project profiles and reachable role skills")
    profiles.add_argument("--only", choices=("all", "repo", "roles"), default="all")
    localities = commands.add_parser("localities", help="Inspect locality path and dependency references without certifying meaning")
    localities.add_argument("--locality", action="append", default=None)
    delegation = commands.add_parser("delegation", help="Check a proposed dependency/ownership plan; never launch agents")
    delegation.add_argument("record")
    review = commands.add_parser("review", help="Check current review coverage and declared session separation")
    review.add_argument("record")
    review.add_argument("--changed", action="append", required=True)
    review.add_argument("--allow-exception", action="append", choices=("trivial", "unavailable"), default=[])
    knowledge = commands.add_parser("knowledge", help="Inventory scoped rules or check recorded knowledge use")
    knowledge.add_argument("--locality", action="append", required=True)
    knowledge.add_argument("--record")
    check = commands.add_parser("check", help="Check an attributed knowledge evidence JSON file")
    check.add_argument("evidence")
    timing = commands.add_parser("timing", help="Separate recorded work and repository-improvement time")
    timing.add_argument("record")
    trace = commands.add_parser("trace", help="Summarize an explicit Codex JSONL window from stdin; never writes or executes trace content")
    trace.add_argument("--first-call", required=True)
    trace.add_argument("--last-call", required=True)
    trace.add_argument("--activity", choices=TRACE_ACTIVITIES, default="mixed")
    trace.add_argument("--max-calls", type=int)
    trace.add_argument("--max-input-bytes", type=int)
    snapshot = commands.add_parser("fingerprint", help="Print file fingerprints; does not certify facts")
    snapshot.add_argument("files", nargs="+")
    args = parser.parse_args()
    try:
        if args.command == "learning":
            result = _learning(args)
        elif args.command == "pitfalls":
            result = lookup_pitfalls(args.concern)
        elif args.command == "skills":
            result = suggest_skills(args.repo, args.requirements)
        elif args.command == "profiles":
            result = check_profiles(args.repo, args.only)
        elif args.command == "localities":
            result = check_localities(args.repo, args.locality)
        elif args.command == "delegation":
            result = check_delegation(json.loads(read_evidence(args.repo, args.record)))
        elif args.command == "review":
            result = check_review(args.repo, json.loads(read_evidence(args.repo, args.record)), args.changed,
                                  allowed_exceptions=args.allow_exception)
        elif args.command == "knowledge":
            record = json.loads(read_evidence(args.repo, args.record)) if args.record else None
            result = check_knowledge_use(args.repo, record, args.locality)
        elif args.command == "check":
            result = check_claims(args.repo, json.loads(read_evidence(args.repo, args.evidence)))
        elif args.command == "timing":
            result = summarize_timing(json.loads(read_evidence(args.repo, args.record)))
        elif args.command == "trace":
            result = summarize_trace(sys.stdin.buffer.read(TRACE_LIMIT + 1), args.first_call,
                                     args.last_call, activity=args.activity,
                                     max_calls=args.max_calls, max_input_bytes=args.max_input_bytes)
        else:
            result = {"files": [fingerprint(args.repo, path) for path in args.files],
                      "semanticTruthVerified": False}
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("fresh") is False or result.get("eligible") is False or result.get("needsReview") or result.get("diagnostics") else 0


if __name__ == "__main__":
    raise SystemExit(main())

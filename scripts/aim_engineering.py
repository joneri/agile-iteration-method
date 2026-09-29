#!/usr/bin/env python3
"""Inspect role-skill candidates and knowledge freshness without running AIM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aim_quality.evidence import check_claims
from aim_quality.files import fingerprint, read_evidence
from aim_quality.skills import suggest_skills
from aim_quality.timing import summarize_timing
from aim_quality.profiles import check_profiles
from aim_quality.localities import check_localities
from aim_quality.delegation import check_delegation
from aim_quality.review import check_review
from aim_quality.knowledge import check_knowledge_use


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
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
    snapshot = commands.add_parser("fingerprint", help="Print file fingerprints; does not certify facts")
    snapshot.add_argument("files", nargs="+")
    args = parser.parse_args()
    try:
        if args.command == "skills":
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

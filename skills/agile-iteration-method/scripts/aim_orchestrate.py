#!/usr/bin/env python3
# GENERATED FILE. DO NOT EDIT DIRECTLY. Generated from canonical Agile Iteration Method sources. Regenerate with: python3 scripts/build_public_skill.py
# Source: scripts/aim_orchestrate.py
"""Native graph planning and ledger-backed orchestration. Never launches agents."""
import argparse
import json
import sys
from pathlib import Path

from aim_quality.orchestration import construct_default_graph, validate_graph, assess_campaign
from aim_quality.orchestration_runtime import prepare_plan, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("default", "validate", "assess", "plan", "status", "checkpoint", "activate", "observe", "decide"))
    parser.add_argument("--input", type=Path, help="JSON file; stdin when omitted")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--outcome")
    args = parser.parse_args()
    try:
        if args.operation in {"status", "checkpoint"}:
            from aim_stories import load
            if args.repo is None:
                raise ValueError("--repo is required for ledger operations.")
            document, store_hash = load(args.repo)
            if args.operation == 'checkpoint':
                from aim_quality.orchestration_runtime import campaign_for
                campaign = campaign_for(document, args.outcome)
                if campaign is None:
                    raise ValueError('Choose an existing original --outcome.')
                record = next((r for r in reversed(campaign['observations']) if 'sourceCheckpoint' in r), None)
                if record is None:
                    raise ValueError('No usable source checkpoint was recorded.')
                checkpoint = record['sourceCheckpoint']
                if checkpoint['kind'] == 'git':
                    from aim_stories import _orchestration_checkpoint
                    _orchestration_checkpoint(args.repo, record['sourceBindings'], checkpoint['commit'])
                result = dict(outcomeId=args.outcome, sourceCheckpoint=checkpoint)
            else:
                result = dict(storeSha256=store_hash, **summary(document))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        data = json.loads(args.input.read_text() if args.input else sys.stdin.read())
        if args.operation == "default":
            result = construct_default_graph(data["pattern"], data["outcomes"], data["coordinator"], data["policy"])
        elif args.operation == "validate":
            result = validate_graph(data)
        elif args.operation == "assess":
            result = assess_campaign(data)
        elif args.operation == "plan":
            result = prepare_plan(data["graph"], data["storyOutcomes"])
        else:
            from aim_stories import execute, compact_result
            if args.repo is None:
                raise ValueError("--repo is required for ledger operations.")
            data["action"] = args.operation
            result = compact_result(execute(args.repo, "orchestrate", data, args.expected_sha256), receipt=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"error": str(exc), "authorityGranted": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

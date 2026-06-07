#!/usr/bin/env python3
"""Build or validate AIM's release-facing public artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aim_publication import PublicationError, build_artifact, validate_artifact


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parents[1]),
        help="AIM source repository root.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory to build or validate.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate an already assembled artifact without rebuilding it.",
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    try:
        if args.check_only:
            validate_artifact(Path(args.output))
        else:
            build_artifact(Path(args.repo), Path(args.output))
    except (PublicationError, OSError) as exc:
        print(f"Publication validation: FAIL\n- {exc}", file=sys.stderr)
        return 1
    print("Publication validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit AIM's current documentation and website release surfaces."""

from __future__ import annotations

import sys
from pathlib import Path

from aim_docs import audit


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    errors = audit(root)
    if errors:
        print("Documentation audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Documentation audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

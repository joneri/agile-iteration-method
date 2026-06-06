"""Run the AIM runtime validator and surface its result class for the plan."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


VALIDATOR_RELATIVE_PATH = "scripts/validate_aim_runtime.py"

RESULT_CLASSES = ("healthy", "recoverable", "blocked", "contradictory")


def run_validator(source_root: Path) -> dict[str, object]:
    """Run ``validate_aim_runtime.py`` against ``source_root``.

    Returns a small dict describing the validator outcome. The dry-run planner
    only reports this; it never blocks plan computation on validator state.
    """

    validator_path = source_root / VALIDATOR_RELATIVE_PATH
    if not validator_path.is_file():
        return {
            "available": False,
            "resultClass": "unknown",
            "exitCode": None,
            "detail": f"validator not found at {VALIDATOR_RELATIVE_PATH}",
        }

    try:
        completed = subprocess.run(
            [sys.executable, str(validator_path), str(source_root)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "available": True,
            "resultClass": "unknown",
            "exitCode": None,
            "detail": f"validator could not run: {exc}",
        }

    result_class = "unknown"
    for line in completed.stdout.splitlines():
        if line.startswith("Result:"):
            token = line.split(":", 1)[1].strip().lower()
            if token in RESULT_CLASSES:
                result_class = token
            break

    return {
        "available": True,
        "resultClass": result_class,
        "exitCode": completed.returncode,
        "detail": None,
    }

"""Interactive terminal helpers for the guided-first installer."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, TextIO


def is_interactive(
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> bool:
    """Return whether prompts are safe for the current terminal."""

    return bool(input_stream.isatty() and output_stream.isatty())


def use_color(mode: str, *, output_stream: TextIO = sys.stdout) -> bool:
    """Resolve auto/always/never color behavior."""

    if mode == "always":
        return True
    if mode == "never" or os.environ.get("NO_COLOR") is not None:
        return False
    return bool(output_stream.isatty())


def prompt_target(
    *,
    source_root: Path,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> Path:
    """Ask for the missing target repository and validate the response."""

    cwd = Path.cwd().resolve()
    default = cwd if cwd != source_root else None
    while True:
        suffix = f" [{default}]" if default else ""
        output_stream.write(f"Target repository{suffix}: ")
        output_stream.flush()
        raw = input_stream.readline()
        if raw == "":
            raise EOFError("target repository was not provided")
        value = raw.strip()
        candidate = Path(value).expanduser().resolve() if value else default
        if candidate is None:
            output_stream.write("  Enter a repository path.\n")
            continue
        if candidate == source_root:
            output_stream.write("  Choose a target other than the AIM source repository.\n")
            continue
        if not candidate.exists() or not candidate.is_dir():
            output_stream.write("  That directory does not exist.\n")
            continue
        return candidate


def resolve_collisions(
    collisions: list[dict[str, Any]],
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> dict[str, str]:
    """Collect keep/overwrite/abort decisions for every collision."""

    decisions: dict[str, str] = {}
    output_stream.write("\nResolve collisions\n")
    for index, action in enumerate(collisions, start=1):
        destination = str(action["destination"])
        while True:
            output_stream.write(
                f"  {index}/{len(collisions)} {destination}\n"
                "    [k]eep existing  [o]verwrite with backup  [a]bort: "
            )
            output_stream.flush()
            raw = input_stream.readline()
            if raw == "":
                raise EOFError(f"no decision provided for {destination}")
            choice = raw.strip().lower()
            if choice in ("", "k", "keep"):
                decisions[destination] = "keep"
                break
            if choice in ("o", "overwrite"):
                decisions[destination] = "overwrite"
                break
            if choice in ("a", "abort"):
                raise KeyboardInterrupt("installation aborted by user")
            output_stream.write("    Choose keep, overwrite, or abort.\n")
    return decisions

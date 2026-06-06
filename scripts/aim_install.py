#!/usr/bin/env python3
"""AIM 2.0 installer — canonical entrypoint.

DI-044 implements the read-only dry-run engine: it computes a manifest-driven
install plan and renders it as human-readable text and/or machine-readable JSON.
It never writes to a target repository. ``--apply`` is intentionally rejected
until DI-045.

Examples:
    python3 scripts/aim_install.py --target /path/to/repo --mode team --adapter copilot
    python3 scripts/aim_install.py --target /path/to/repo --format json
    python3 scripts/aim_install.py --target /path/to/repo --plan-out plan.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow importing the installer package when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aim_installer import apply, planner, render  # noqa: E402
from aim_installer.manifest import ManifestError, load_manifest  # noqa: E402
from aim_installer.validator import run_validator  # noqa: E402


EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2
EXIT_FAILED = 3


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aim_install.py",
        description="AIM 2.0 installer (dry-run engine).",
    )
    parser.add_argument(
        "--target",
        help="Path to the target repository to plan an install for.",
    )
    parser.add_argument(
        "--source",
        help="Path to the AIM source repository (defaults to this repo).",
    )
    parser.add_argument(
        "--home",
        help="Override the home directory used for home-scope packages (e.g. Codex).",
    )
    parser.add_argument(
        "--mode",
        default="team",
        help="Install mode (team is supported in DI-044).",
    )
    parser.add_argument(
        "--adapter",
        action="append",
        help="Adapter to include (repeatable). Defaults to copilot.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the plan on stdout.",
    )
    parser.add_argument(
        "--plan-out",
        help="Write the machine-readable JSON plan to this path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Compute a plan without writing (default and only mode in DI-044).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the plan to the target repo (reviewed apply with rollback).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --apply, overwrite collisions after backing them up.",
    )
    return parser.parse_args(argv)


def _normalize_adapters(raw: list[str] | None) -> list[str]:
    if not raw:
        return ["copilot"]
    adapters: list[str] = []
    for item in raw:
        for part in item.split(","):
            part = part.strip().lower()
            if part and part not in adapters:
                adapters.append(part)
    return adapters or ["copilot"]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if not args.target:
        print("error: --target is required.", file=sys.stderr)
        return EXIT_USAGE

    source_root = (
        Path(args.source).resolve()
        if args.source
        else Path(__file__).resolve().parent.parent
    )
    target_root = Path(args.target).resolve()

    try:
        manifest = load_manifest(source_root)
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    mode = args.mode.strip().lower()
    if mode not in manifest.modes:
        print(
            f"error: unknown mode '{mode}'. Known modes: {', '.join(manifest.modes)}.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    adapters = _normalize_adapters(args.adapter)
    unknown_adapters = [a for a in adapters if a not in manifest.adapters]
    if unknown_adapters:
        print(
            f"error: unknown adapter(s): {', '.join(unknown_adapters)}. "
            f"Known adapters: {', '.join(manifest.adapters)}.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    blockers: list[str] = []
    if target_root == source_root:
        blockers.append(
            "refusing to install into the AIM source repository itself"
        )
    if not target_root.exists():
        blockers.append(f"target path does not exist: {target_root}")
    elif not target_root.is_dir():
        blockers.append(f"target path is not a directory: {target_root}")

    validator_result = run_validator(source_root)

    try:
        plan = planner.compute_plan(
            source_root=source_root,
            target_root=target_root,
            mode=mode,
            adapters=adapters,
            manifest=manifest,
            validator_result=validator_result,
            home_root=Path(args.home).resolve() if args.home else None,
            blockers=blockers,
        )
    except planner.PlanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.apply:
        plan["operation"] = "apply"
        plan["applyAllowed"] = not plan["blockers"]

    if args.plan_out:
        Path(args.plan_out).write_text(render.render_json(plan), encoding="utf-8")

    if args.format == "json":
        print(render.render_json(plan))
    else:
        print(render.render_text(plan))

    if args.apply:
        try:
            result = apply.apply_plan(
                plan=plan,
                source_root=source_root,
                target_root=target_root,
                manifest=manifest,
                force=args.force,
            )
        except apply.ApplyRefused as exc:
            print(f"apply refused: {exc}", file=sys.stderr)
            return EXIT_BLOCKED
        except apply.ApplyFailed as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_FAILED
        print(
            f"apply complete: wrote {result['writtenCount']} file(s), "
            f"{result['untouchedCount']} already up to date.",
            file=sys.stderr,
        )
        return EXIT_OK

    return EXIT_BLOCKED if plan["blockers"] else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

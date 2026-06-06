#!/usr/bin/env python3
"""AIM 2.0 guided-first installer entrypoint.

Collects missing required input in an interactive terminal, computes a
manifest-driven plan, and renders a compact summary by default. ``--verbose`` and
JSON preserve advanced plan inspection. ``--dry-run`` previews without writing;
``--apply`` uses explicit collision decisions, rollback, and idempotent re-runs.

Examples:
    python3 scripts/aim_install.py --target /path/to/repo --mode team --adapter copilot
    python3 scripts/aim_install.py --target /path/to/repo --format json
    python3 scripts/aim_install.py --target /path/to/repo --apply
    python3 scripts/aim_install.py --target /path/to/repo --apply --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow importing the installer package when run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aim_installer import apply, guided, planner, render  # noqa: E402
from aim_installer.manifest import ManifestError, load_manifest  # noqa: E402
from aim_installer.validator import run_validator  # noqa: E402


EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2
EXIT_FAILED = 3


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aim_install.py",
        description="AIM 2.0 installer.",
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
        help="Install mode: team, personal, or enterprise. Guided default: personal.",
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
        "--verbose",
        "--raw",
        action="store_true",
        dest="verbose",
        help="Show every planned file action and detailed guidance.",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Colorize guided text output (default: auto).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Never prompt; missing input or unresolved collisions fail clearly.",
    )
    parser.add_argument(
        "--plan-out",
        help="Write the machine-readable JSON plan to this path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only; do not offer same-session apply.",
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
    if args.apply and args.dry_run:
        print("error: --apply and --dry-run cannot be used together.", file=sys.stderr)
        return EXIT_USAGE

    source_root = (
        Path(args.source).resolve()
        if args.source
        else Path(__file__).resolve().parent.parent
    )
    interactive = (
        not args.non_interactive
        and args.format == "text"
        and guided.is_interactive()
    )

    try:
        manifest = load_manifest(source_root)
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.target:
        target_root = Path(args.target).expanduser().resolve()
    elif interactive:
        try:
            target_root = guided.prompt_target(source_root=source_root)
        except (EOFError, KeyboardInterrupt):
            print("\ninstallation cancelled.", file=sys.stderr)
            return EXIT_USAGE
    else:
        print(
            "error: --target is required in non-interactive or JSON mode.",
            file=sys.stderr,
        )
        return EXIT_USAGE

    try:
        if args.mode:
            mode = args.mode.strip().lower()
        elif interactive:
            mode = guided.prompt_mode(manifest.modes)
        else:
            mode = "team"

        if args.adapter:
            adapters = _normalize_adapters(args.adapter)
        elif interactive:
            adapters = guided.prompt_adapters(manifest.adapters)
        else:
            adapters = ["copilot"]
    except (EOFError, KeyboardInterrupt):
        print("\ninstallation cancelled.", file=sys.stderr)
        return EXIT_USAGE

    if mode not in manifest.modes:
        print(
            f"error: unknown mode '{mode}'. Known modes: {', '.join(manifest.modes)}.",
            file=sys.stderr,
        )
        return EXIT_USAGE

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
        print(
            render.render_text(
                plan,
                verbose=args.verbose,
                color=guided.use_color(args.color),
                guided_session=interactive,
            )
        )

    apply_in_session = args.apply or (
        interactive and not args.dry_run and not plan["blockers"]
    )
    if apply_in_session:
        collision_decisions: dict[str, str] | None = None
        collisions = [
            action
            for action in plan["actions"]
            if action["classification"] == "collision"
        ]
        if collisions and not args.force and interactive:
            try:
                collision_decisions = guided.resolve_collisions(collisions)
            except (EOFError, KeyboardInterrupt):
                print("\ninstallation cancelled; no files were written.", file=sys.stderr)
                return EXIT_BLOCKED
        if interactive and not plan["blockers"]:
            try:
                confirmed = guided.confirm_apply()
            except (EOFError, KeyboardInterrupt):
                confirmed = False
            if not confirmed:
                if args.apply:
                    print(
                        "\ninstallation cancelled at final confirmation; "
                        "no files were written.",
                        file=sys.stderr,
                    )
                    return EXIT_BLOCKED
                print("\npreview complete; no files were written.", file=sys.stderr)
                return EXIT_OK
        plan["operation"] = "apply"
        plan["applyAllowed"] = True
        try:
            result = apply.apply_plan(
                plan=plan,
                source_root=source_root,
                target_root=target_root,
                manifest=manifest,
                force=args.force,
                collision_decisions=collision_decisions,
            )
        except apply.ApplyRefused as exc:
            print(f"apply refused: {exc}", file=sys.stderr)
            return EXIT_BLOCKED
        except apply.ApplyFailed as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_FAILED
        print(
            f"apply complete: wrote {result['writtenCount']} file(s), "
            f"{result['untouchedCount']} kept or already up to date.",
            file=sys.stderr,
        )
        return EXIT_OK

    return EXIT_BLOCKED if plan["blockers"] else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

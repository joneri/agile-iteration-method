#!/usr/bin/env python3
"""Validate AIM public-skill discovery, installation, and prompt generation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_public_skill import OFFICIAL_SKILLS_CLI_VERSION


SKILL_NAME = "agile-iteration-method"
AGENT_TARGETS = {
    "codex": Path(".agents/skills") / SKILL_NAME,
    "github-copilot": Path(".agents/skills") / SKILL_NAME,
    "claude-code": Path(".claude/skills") / SKILL_NAME,
}
PROMPT_MARKERS = (
    "PO -> TDO -> Dev -> Reviewer -> TDO -> PO",
    "/aim help",
    "Gate A",
    "Gate B",
    "Gate E",
    "main AIM thread",
)


class CliValidationError(RuntimeError):
    """Raised when the official skills CLI violates the expected AIM contract."""


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        raise CliValidationError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n{output}"
        )
    return output


def _npx(cli_version: str) -> list[str]:
    return ["npx", "--yes", f"skills@{cli_version}"]


def _validate_installed_package(path: Path) -> None:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise CliValidationError(f"installed manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != SKILL_NAME:
        raise CliValidationError(f"installed package has wrong name: {manifest.get('name')!r}")
    expected_files = set(manifest.get("files", []))
    actual_files = {
        file.relative_to(path).as_posix()
        for file in path.rglob("*")
        if file.is_file()
    }
    if actual_files != expected_files:
        raise CliValidationError(
            f"installed package is incomplete; missing={sorted(expected_files - actual_files)} "
            f"extra={sorted(actual_files - expected_files)}"
        )
    package_text = "\n".join(
        file.read_text(encoding="utf-8", errors="replace")
        for file in path.rglob("*")
        if file.is_file()
    )
    for marker in PROMPT_MARKERS:
        if marker not in package_text:
            raise CliValidationError(f"installed package lacks AIM semantic marker: {marker}")


def validate(source: str, cli_version: str) -> None:
    source_path = Path(source)
    resolved_source = str(source_path.resolve()) if source_path.exists() else source
    with tempfile.TemporaryDirectory(prefix="aim-public-skill-cli-") as temporary:
        root = Path(temporary)
        environment = os.environ.copy()
        environment.update(
            {
                "DISABLE_TELEMETRY": "1",
                "DO_NOT_TRACK": "1",
                "NO_COLOR": "1",
                "npm_config_cache": str(root / "npm-cache"),
            }
        )

        discovery = root / "discovery"
        discovery.mkdir()
        environment["HOME"] = str(root / "discovery-home")
        list_output = _run(
            _npx(cli_version) + ["add", resolved_source, "--list"],
            cwd=discovery,
            env=environment,
        )
        if SKILL_NAME not in list_output:
            raise CliValidationError("official skills CLI did not discover agile-iteration-method")

        for agent, relative_target in AGENT_TARGETS.items():
            project = root / agent / "project"
            home = root / agent / "home"
            project.mkdir(parents=True)
            home.mkdir(parents=True)
            _run(["git", "init", "-q"], cwd=project, env=environment)
            agent_env = dict(environment, HOME=str(home))
            _run(
                _npx(cli_version)
                + [
                    "add",
                    resolved_source,
                    "--skill",
                    SKILL_NAME,
                    "--agent",
                    agent,
                    "--yes",
                    "--copy",
                ],
                cwd=project,
                env=agent_env,
            )
            _validate_installed_package(project / relative_target)

        use_root = root / "use"
        use_root.mkdir()
        use_output = _run(
            _npx(cli_version)
            + ["use", resolved_source, "--skill", SKILL_NAME],
            cwd=use_root,
            env=dict(environment, HOME=str(root / "use-home")),
        )
        for marker in PROMPT_MARKERS:
            if marker not in use_output:
                raise CliValidationError(f"skills use prompt lacks AIM marker: {marker}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parents[1]),
        help="local path or GitHub owner/repository source",
    )
    parser.add_argument(
        "--cli-version",
        default=OFFICIAL_SKILLS_CLI_VERSION,
        help="official skills CLI version validated by this release",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if shutil.which("npx") is None:
        print("public skill CLI validation failed: npx is unavailable", file=sys.stderr)
        return 1
    try:
        validate(args.source, args.cli_version)
    except (CliValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"public skill CLI validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Official skills CLI validation passed for discovery, Codex, GitHub "
        "Copilot, Claude Code, and skills use."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

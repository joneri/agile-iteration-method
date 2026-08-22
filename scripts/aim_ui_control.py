#!/usr/bin/env python3
"""Start, open, inspect, or stop one repository-bound AIM UI instance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
import webbrowser
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback keeps lifecycle functional.
    fcntl = None


STATE_ENV = "AIM_UI_STATE_DIR"
DEFAULT_STATE_ROOT = Path.home() / ".aim" / "ui" / "instances"
MAX_METADATA_BYTES = 16_384
MAX_LOG_BYTES = 1_048_576
START_TIMEOUT_SECONDS = 6.0
_STARTED_PROCESSES: dict[int, subprocess.Popen[bytes]] = {}


class AimUiControlError(RuntimeError):
    """A safe, actionable AIM UI lifecycle failure."""


def resolve_repo(raw: str | Path | None) -> Path:
    repo = Path(raw).expanduser() if raw is not None else Path.cwd()
    try:
        resolved = repo.resolve(strict=True)
    except OSError as exc:
        raise AimUiControlError(f"Repository was not found: {repo}") from exc
    if not resolved.is_dir():
        raise AimUiControlError(f"Repository must be a directory: {resolved}")
    return resolved


def state_root() -> Path:
    configured = os.environ.get(STATE_ENV)
    return Path(configured).expanduser().resolve() if configured else DEFAULT_STATE_ROOT


def instance_key(repo: Path) -> str:
    return hashlib.sha256(str(repo).encode("utf-8")).hexdigest()[:24]


def metadata_path(repo: Path) -> Path:
    return state_root() / f"{instance_key(repo)}.json"


def log_path(repo: Path) -> Path:
    return state_root() / f"{instance_key(repo)}.log"


@contextmanager
def _instance_lock(repo: Path):
    root = state_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{instance_key(repo)}.lock"
    with path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read_metadata(repo: Path) -> dict[str, Any] | None:
    path = metadata_path(repo)
    if path.is_symlink() or not path.is_file():
        return None
    try:
        if path.stat().st_size > MAX_METADATA_BYTES:
            path.unlink(missing_ok=True)
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        path.unlink(missing_ok=True)
        return None
    required = {
        "instanceVersion",
        "instanceId",
        "repo",
        "pid",
        "url",
        "port",
        "startedAt",
    }
    if (
        not isinstance(value, dict)
        or value.get("instanceVersion") != "1.0"
        or not required.issubset(value)
        or value.get("repo") != str(repo)
        or not isinstance(value.get("pid"), int)
        or isinstance(value.get("pid"), bool)
        or value["pid"] < 1
        or not isinstance(value.get("port"), int)
        or not 1 <= value["port"] <= 65535
        or value.get("url") != f"http://127.0.0.1:{value.get('port')}/"
        or not isinstance(value.get("instanceId"), str)
        or not 16 <= len(value["instanceId"]) <= 128
    ):
        path.unlink(missing_ok=True)
        return None
    return value


def _write_metadata(repo: Path, value: dict[str, Any]) -> None:
    root = state_root()
    root.mkdir(parents=True, exist_ok=True)
    path = metadata_path(repo)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _health(metadata: dict[str, Any], timeout: float = 0.4) -> bool:
    if not _pid_exists(metadata["pid"]):
        return False
    try:
        with urlopen(f"{metadata['url']}api/health", timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return False
    return (
        value.get("instanceId") == metadata["instanceId"]
        and value.get("repo") == metadata["repo"]
        and value.get("pid") == metadata["pid"]
        and value.get("readOnly") is True
    )


def _healthy_metadata(repo: Path) -> dict[str, Any] | None:
    metadata = _read_metadata(repo)
    if metadata is None:
        return None
    if _health(metadata):
        return metadata
    metadata_path(repo).unlink(missing_ok=True)
    return None


def _free_port(requested: int | None) -> int:
    if requested is not None and not 1 <= requested <= 65535:
        raise AimUiControlError("Port must be between 1 and 65535.")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", requested or 0))
            return int(probe.getsockname()[1])
    except OSError as exc:
        target = str(requested) if requested is not None else "an automatic port"
        raise AimUiControlError(f"Loopback port {target} is unavailable.") from exc


def _start(repo: Path, *, port: int | None, open_browser: bool) -> dict[str, Any]:
    existing = _healthy_metadata(repo)
    if existing is not None:
        if open_browser:
            webbrowser.open(existing["url"])
        return {**existing, "status": "running", "reused": True}

    selected_port = _free_port(port)
    token = uuid.uuid4().hex
    ui_server = Path(__file__).resolve().with_name("aim_ui.py")
    if not ui_server.is_file():
        raise AimUiControlError(
            f"AIM UI server payload is missing beside the launcher: {ui_server}"
        )
    state_root().mkdir(parents=True, exist_ok=True)
    instance_log = log_path(repo)
    log_mode = (
        "wb"
        if instance_log.is_file() and instance_log.stat().st_size > MAX_LOG_BYTES
        else "ab"
    )
    log_handle = instance_log.open(log_mode)
    command = [
        sys.executable,
        str(ui_server),
        "--repo",
        str(repo),
        "--host",
        "127.0.0.1",
        "--port",
        str(selected_port),
        "--no-browser",
        "--quiet",
        "--instance-id",
        token,
    ]
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    metadata = {
        "instanceVersion": "1.0",
        "instanceId": token,
        "repo": str(repo),
        "pid": process.pid,
        "port": selected_port,
        "url": f"http://127.0.0.1:{selected_port}/",
        "startedAt": now,
    }
    deadline = time.monotonic() + START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if _health(metadata, timeout=0.2):
            _write_metadata(repo, metadata)
            _STARTED_PROCESSES[process.pid] = process
            if open_browser:
                webbrowser.open(metadata["url"])
            return {**metadata, "status": "running", "reused": False}
        time.sleep(0.08)

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)
    raise AimUiControlError(
        f"AIM UI did not become ready. Inspect {log_path(repo)} for details."
    )


def start(
    repo: Path, *, port: int | None = None, open_browser: bool = True
) -> dict[str, Any]:
    with _instance_lock(repo):
        return _start(repo, port=port, open_browser=open_browser)


def status(repo: Path) -> dict[str, Any]:
    metadata = _healthy_metadata(repo)
    if metadata is None:
        return {"status": "stopped", "repo": str(repo), "url": None}
    return {**metadata, "status": "running", "reused": True}


def open_instance(repo: Path) -> dict[str, Any]:
    metadata = _healthy_metadata(repo)
    if metadata is None:
        raise AimUiControlError("No healthy AIM UI instance is running for this repository.")
    webbrowser.open(metadata["url"])
    return {**metadata, "status": "running", "reused": True}


def _stop(repo: Path) -> dict[str, Any]:
    metadata = _read_metadata(repo)
    if metadata is None:
        return {"status": "stopped", "repo": str(repo), "stopped": False}
    if not _health(metadata):
        metadata_path(repo).unlink(missing_ok=True)
        return {
            "status": "stopped",
            "repo": str(repo),
            "stopped": False,
            "staleMetadataRemoved": True,
        }
    try:
        os.kill(metadata["pid"], signal.SIGTERM)
    except ProcessLookupError:
        metadata_path(repo).unlink(missing_ok=True)
        return {"status": "stopped", "repo": str(repo), "stopped": False}
    child = _STARTED_PROCESSES.get(metadata["pid"])
    if child is not None:
        try:
            child.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            pass
        _STARTED_PROCESSES.pop(metadata["pid"], None)
    else:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and _pid_exists(metadata["pid"]):
            time.sleep(0.05)
    if _pid_exists(metadata["pid"]) and _health(metadata):
        raise AimUiControlError(
            "AIM UI received the stop request but the verified instance is still running."
        )
    metadata_path(repo).unlink(missing_ok=True)
    return {"status": "stopped", "repo": str(repo), "stopped": True}


def stop(repo: Path) -> dict[str, Any]:
    with _instance_lock(repo):
        return _stop(repo)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command")
    for name in ("start", "open", "status", "stop"):
        sub = subparsers.add_parser(name)
        sub.add_argument(
            "repo", nargs="?", help="Repository path (default: current directory)"
        )
        if name == "start":
            sub.add_argument("--port", type=int, help="Preferred loopback port")
            sub.add_argument(
                "--no-browser", action="store_true", help="Do not open a browser tab"
            )
    return parser


def _print_result(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    if result["status"] == "running":
        label = (
            "AIM UI is already running" if result.get("reused") else "AIM UI started"
        )
        print(f"{label} for {result['repo']}")
        print(f"Open {result['url']}")
    elif result.get("stopped"):
        print(f"AIM UI stopped for {result['repo']}")
    else:
        print(f"AIM UI is not running for {result['repo']}")


def main() -> int:
    args = _parser().parse_args()
    command = args.command or "start"
    try:
        repo = resolve_repo(getattr(args, "repo", None))
        if command == "start":
            result = start(
                repo,
                port=getattr(args, "port", None),
                open_browser=not getattr(args, "no_browser", False),
            )
        elif command == "open":
            result = open_instance(repo)
        elif command == "status":
            result = status(repo)
        else:
            result = stop(repo)
    except (AimUiControlError, OSError) as exc:
        print(f"AIM UI: {exc}", file=sys.stderr)
        return 1
    _print_result(result, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

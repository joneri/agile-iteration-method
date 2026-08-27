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
MAX_HEALTH_BYTES = 16_384
START_TIMEOUT_SECONDS = 6.0
_STARTED_PROCESSES: dict[int, subprocess.Popen[bytes]] = {}
INSTANCE_VERSION = "1.1"
LEGACY_INSTANCE_VERSION = "1.0"
UI_PROTOCOL_VERSION = "1.1"
PAYLOAD_FILES = (
    "scripts/aim_ui_control.py",
    "scripts/aim_ui.py",
    "scripts/aim_runtime_contract.py",
    "aim-ui/index.html",
    "aim-ui/app.js",
    "aim-ui/styles.css",
)


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


def payload_fingerprint() -> str:
    """Fingerprint the launcher, server, and static assets as one UI payload."""

    package_root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for relative in PAYLOAD_FILES:
        path = package_root / relative
        if path.is_symlink() or not path.is_file():
            raise AimUiControlError(f"AIM UI payload file is missing or symlinked: {path}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _valid_fingerprint(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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
        or value.get("instanceVersion") not in {LEGACY_INSTANCE_VERSION, INSTANCE_VERSION}
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
        or (
            value.get("instanceVersion") == INSTANCE_VERSION
            and not _valid_fingerprint(value.get("payloadFingerprint"))
        )
        or (
            value.get("payloadFingerprint") is not None
            and not _valid_fingerprint(value["payloadFingerprint"])
        )
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


def _health_probe(metadata: dict[str, Any], timeout: float = 0.4) -> dict[str, Any]:
    expected = payload_fingerprint()
    if not _pid_exists(metadata["pid"]):
        return {
            "identityVerified": False,
            "compatible": False,
            "reason": "process_missing",
            "expectedPayloadFingerprint": expected,
            "observedPayloadFingerprint": None,
        }
    try:
        with urlopen(f"{metadata['url']}api/health", timeout=timeout) as response:
            payload = response.read(MAX_HEALTH_BYTES + 1)
            if len(payload) > MAX_HEALTH_BYTES:
                raise ValueError("health response is too large")
            value = json.loads(payload.decode("utf-8"))
    except (OSError, URLError, UnicodeDecodeError, ValueError):
        return {
            "identityVerified": False,
            "compatible": False,
            "reason": "health_invalid",
            "expectedPayloadFingerprint": expected,
            "observedPayloadFingerprint": None,
        }
    if not isinstance(value, dict):
        return {
            "identityVerified": False,
            "compatible": False,
            "reason": "health_invalid",
            "expectedPayloadFingerprint": expected,
            "observedPayloadFingerprint": None,
        }
    identity_verified = (
        value.get("instanceId") == metadata["instanceId"]
        and value.get("repo") == metadata["repo"]
        and value.get("pid") == metadata["pid"]
        and value.get("readOnly") is True
    )
    observed = value.get("payloadFingerprint")
    metadata_fingerprint = metadata.get("payloadFingerprint")
    compatible = (
        identity_verified
        and value.get("protocolVersion") == UI_PROTOCOL_VERSION
        and observed == expected
        and metadata_fingerprint == expected
    )
    return {
        "identityVerified": identity_verified,
        "compatible": compatible,
        "reason": (
            "compatible"
            if compatible
            else "payload_mismatch"
            if identity_verified
            else "identity_mismatch"
        ),
        "expectedPayloadFingerprint": expected,
        "observedPayloadFingerprint": observed,
        "protocolVersion": value.get("protocolVersion"),
    }


def _health(metadata: dict[str, Any], timeout: float = 0.4) -> bool:
    return bool(_health_probe(metadata, timeout=timeout)["compatible"])


def _stop_verified_instance(repo: Path, metadata: dict[str, Any]) -> None:
    probe = _health_probe(metadata)
    if not probe["identityVerified"]:
        raise AimUiControlError(
            "Refused to signal an AIM UI process whose repository and instance identity could not be verified."
        )
    try:
        os.kill(metadata["pid"], signal.SIGTERM)
    except ProcessLookupError:
        return
    child = _STARTED_PROCESSES.get(metadata["pid"])
    if child is not None:
        try:
            child.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            pass
        _STARTED_PROCESSES.pop(metadata["pid"], None)
    else:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if not _pid_exists(metadata["pid"]):
                break
            current = _health_probe(metadata, timeout=0.15)
            if not current["identityVerified"]:
                break
            time.sleep(0.05)
    if _pid_exists(metadata["pid"]):
        current = _health_probe(metadata, timeout=0.15)
        if current["identityVerified"]:
            raise AimUiControlError(
                "AIM UI received the stop request but the verified instance is still running."
            )


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
    existing = _read_metadata(repo)
    replaced = False
    if existing is not None:
        probe = _health_probe(existing)
        if probe["compatible"]:
            if open_browser:
                webbrowser.open(existing["url"])
            return {
                **existing,
                "status": "running",
                "reused": True,
                "compatible": True,
                "protocolVersion": UI_PROTOCOL_VERSION,
            }
        if probe["identityVerified"]:
            _stop_verified_instance(repo, existing)
            replaced = True
        metadata_path(repo).unlink(missing_ok=True)

    selected_port = _free_port(port)
    token = uuid.uuid4().hex
    fingerprint = payload_fingerprint()
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
        "--expected-payload-fingerprint",
        fingerprint,
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
        "instanceVersion": INSTANCE_VERSION,
        "instanceId": token,
        "repo": str(repo),
        "pid": process.pid,
        "port": selected_port,
        "url": f"http://127.0.0.1:{selected_port}/",
        "startedAt": now,
        "payloadFingerprint": fingerprint,
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
            return {
                **metadata,
                "status": "running",
                "reused": False,
                "replacedIncompatible": replaced,
                "compatible": True,
                "protocolVersion": UI_PROTOCOL_VERSION,
            }
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
    metadata = _read_metadata(repo)
    if metadata is None:
        return {"status": "stopped", "repo": str(repo), "url": None}
    probe = _health_probe(metadata)
    if probe["compatible"]:
        return {
            **metadata,
            "status": "running",
            "reused": True,
            "compatible": True,
            "protocolVersion": UI_PROTOCOL_VERSION,
        }
    if probe["identityVerified"]:
        return {
            **metadata,
            "status": "stale",
            "reused": False,
            "compatible": False,
            "payloadStatus": probe["reason"],
            "expectedPayloadFingerprint": probe["expectedPayloadFingerprint"],
            "observedPayloadFingerprint": probe["observedPayloadFingerprint"],
            "protocolVersion": probe.get("protocolVersion"),
        }
    metadata_path(repo).unlink(missing_ok=True)
    return {
        "status": "stopped",
        "repo": str(repo),
        "url": None,
        "staleMetadataRemoved": True,
    }


def open_instance(repo: Path) -> dict[str, Any]:
    current = status(repo)
    if current["status"] == "stale":
        raise AimUiControlError(
            "The AIM UI server payload is stale. Run `/aim ui` to replace the verified instance."
        )
    if current["status"] != "running":
        raise AimUiControlError("No healthy AIM UI instance is running for this repository.")
    webbrowser.open(current["url"])
    return current


def _stop(repo: Path) -> dict[str, Any]:
    metadata = _read_metadata(repo)
    if metadata is None:
        return {"status": "stopped", "repo": str(repo), "stopped": False}
    probe = _health_probe(metadata)
    if not probe["identityVerified"]:
        metadata_path(repo).unlink(missing_ok=True)
        return {
            "status": "stopped",
            "repo": str(repo),
            "stopped": False,
            "staleMetadataRemoved": True,
        }
    _stop_verified_instance(repo, metadata)
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
    elif result["status"] == "stale":
        print(f"AIM UI payload is stale for {result['repo']}")
        print("Run `/aim ui` to replace the verified instance.")
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
